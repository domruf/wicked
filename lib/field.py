##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit@kalistra.com>
#   - Rob Miller <rob@kalistra.com> (RaFromBRC)
#   - and contributors
#
##########################################################

from AccessControl import ClassSecurityInfo
from ZPublisher.HTTPRequest import FileUpload

from relation import Backlink
from filter import WickedFilter
from Products.wicked import config, utils
from Products.filter import api as fapi

from Products.Archetypes import public as atapi
from Products.Archetypes.Registry import registerField

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext
from interfaces import IMacroCacheManager

try:
    # When Reference are in CMFCore
    from Products.CMFCore.reference_config import *
    from Products.CMFCore.ReferenceCatalog import Reference
    from Products.CMFCore.Referenceable import Referenceable
except ImportError:
    # And while they still live in Archetypes
    from Products.Archetypes.ReferenceEngine import Reference
    from Products.Archetypes.Referenceable import Referenceable
    from Products.Archetypes.config import REFERENCE_CATALOG as REFERENCE_MANAGER
    from Products.Archetypes.config import UID_CATALOG as UID_MANAGER

from filter import pattern as linkregex 
from normalize import titleToNormalizedId

def removeParens(wikilink):
    wikilink.replace('((', '')
    wikilink.replace('))', '')
    return wikilink

class WikiField(fapi.FilterField):
    """ drop-in wiki """
    
    __implements__ = fapi.FilterField.__implements__
    _properties = fapi.FilterField._properties.copy()
    _properties.update({
        'filter':WickedFilter.name,

        # scope, template, and wicked_macro would work nicely as TALS
        
        'scope': '',
        'template': 'wicked_link',
        'wicked_macro':'wicked_link'
        })
    

    security  = ClassSecurityInfo()
    def get(self, instance, mimetype=None, raw=False, **kwargs):
        """
        Pass in a scope, template and macro, then let filter field do it's magic
        """
        # configuration
        kwargs['scope'] = self.scope
        kwargs['template'] = self.template
        kwargs['wicked_macro'] = self.wicked_macro
        kwargs['fieldname'] = self.getName()
        return super(WikiField, self).get(instance, mimetype=mimetype,
                                        raw=raw, **kwargs)
        
    def set(self, instance, value, **kwargs):
        """
        do a normal text field set, set backlink references, remove stale
        backlinks, cache resolved forward links
        """
        super(WikiField, self).set(instance, value, **kwargs)        

        # parse wiki text, set backlinks
        
        value_str = value
        if value.__class__ == atapi.BaseUnit:
            value_str = value.getRaw()
        elif value.__class__ == FileUpload:
            # a file was uploaded, get the (possibly transformed) value
            value_str = self.get(instance, skip_filters=True)

        new_links = dict()
        found = linkregex.findall(value_str)

        # use straight catalog
        old_links = instance.getBRefs(relationship=config.BACKLINK_RELATIONSHIP)

        if len(found):
            new_links = found
            new_links = map(removeParens, new_links)
            new_links = dict([(titleToNormalizedId(link), False) for link in new_links])

        wicked = utils.getFilter(instance)
        wicked.fieldname = fieldname = self.getName() 
        cache = IMacroCacheManager(wicked)

        # unravel this
        unlink = [obj.deleteReference for obj in old_links \
                  if not new_links.has_key(obj.getId())]

        [delRef(instance,
                     relationship=config.BACKLINK_RELATIONSHIP) \
         for delRef in unlink]
        
        if not len(new_links):
            return

        # add appropriate backlinks, remove stale ones
        kwargs['scope'] = self.scope 

        renderLink, getBrain = (wicked.renderLinkForBrain,
                                wicked.getLinkTargetBrain)
        
        refcat = getToolByName(instance, REFERENCE_MANAGER)

        for link in new_links.keys():
            brain = getBrain(link, **kwargs)
            if brain is None:
                new_links.pop(link)
            else:
                refcat.addReference(brain.getObject(),
                                    instance,
                                    relationship=config.BACKLINK_RELATIONSHIP,
                                    referenceClass=Backlink,
                                    link_text=link,
                                    fieldname=fieldname)
                
                rendered = renderLink(self.template, self.wicked_macro,
                                      link, brain)
                cache.set(intern(link), rendered)  

    def removeLinkFromCache(self, link, instance):
        """
        clears a link from the wicked cache on the 'instance' object
        """
        link_store = getattr(instance.aq_base, '_wicked_cache', {})
        cached_links = link_store.get(self.getName(), {})
        if cached_links.has_key(link):
            cached_links.pop(link)
            instance._p_changed = True

registerField(WikiField,
              title='Wiki',
              description='Text field capable of wiki style behavior')
