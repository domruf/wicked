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

import sre
from Products.CMFCore.utils import getToolByName
from Products.filter.utils import createContext, macro_render
from Products.AdvancedQuery import Eq, Generic

from Products.wicked import utils, config
from Products.filter import filter as filters
from normalize import titleToNormalizedId

pattern = sre.compile('\(\(([\w\W]+?)\)\)') # matches ((Some Text To link 123))

class WickedFilter(filters.MacroSubstitutionFilter):
    """
    Filter for creating core wiki behavior 
    """

    name = config.FILTER_NAME
    pattern = pattern

    def _getMatchFromQueryResults(self, chunk, brains):
        """
        Given a set of query results and the wicked link text, return
        the brain that represents the correct object to link to, or
        None

        Assumes that brains are already ordered oldest to newest, so
        the first absolute match is the one returned.  Matches on id
        take priority over matches on title

        Currently title match comparisons are just testing for equal
        length; since the index lookup was for an exact phrase, equal
        length implies equal value

        XXX do we want to be more forgiving w/ extra whitespace in the
        title?
        """
        link_brain = None
        if len(brains) == 1:
            if brains[0].id == chunk or len(brains[0].Title) == len(chunk):
                link_brain = brains[0]
        else:
            for brain in brains:
                if brain.id == chunk:
                    link_brain = brain
                    break
            if not link_brain:
                # there was no id match, get the earliest created Title match
                for brain in brains:
                    if len(brain.Title) == len(chunk):
                        link_brain = brain
                        break
        return link_brain

    def _filterCore(self, chunk, return_brain=False, **kwargs):
        """
        First check the link cache.  If the link is not in the cache,
        use the portal catalog to find a list of possible links.

        Filter by path, present by macro.
        """
        normalled = titleToNormalizedId(chunk)
        cached_links = kwargs.get('cached_links', {})
        if cached_links.has_key(chunk) and not return_brain:
            return cached_links[chunk]

        catalog = getToolByName(self.context, 'portal_catalog')
        path = '/'.join(self.context.aq_inner.aq_parent.getPhysicalPath())
        getId = chunk
        title = '"%s"' % chunk

        query = Generic('path', {'query': path, 'depth': 1}) \
                & (Eq('getId', getId) | Eq('Title', title) | Eq('getId', normalled)) 
        brains = catalog.evalAdvancedQuery(query, ('created',))

        link_brain = None
        if brains:
            link_brain = self._getMatchFromQueryResults(chunk, brains)

        if not link_brain:
            if kwargs['scope']:
                scope = getattr(self.context, kwargs['scope'])
                if callable(scope):
                    scope = scope()
                query = Generic('path', scope) \
                        & (Eq('getId', getId) | Eq('Title', title))
            else:
                query = Eq('getId', getId) | Eq('Title', title)
            brains = catalog.evalAdvancedQuery(query, ('created',))
            if brains:
                link_brain = self._getMatchFromQueryResults(chunk, brains)

        if return_brain:
            return link_brain
        
        if link_brain:
            # XXX do we need to support 'links' as a sequence or should
            #     we change to a single 'link'
            kwargs['links'] = [{'path': link_brain.getPath(),
                                'icon': link_brain.getIcon,
                                'rel_path': utils.getPathRelToPortal(link_brain.getPath(),
                                                                     self.context)}]
        else:
            kwargs['links'] = []
        kwargs['chunk'] = chunk
        macro = kwargs['wicked_macro']; del kwargs['wicked_macro']
        return self._macro_renderer(macro, **kwargs)

    def getLinkTargetBrain(self, link_text, **kwargs):
        """
        returns a brain of the object that would be the link target
        for the 'link_text' parameter in the context of the 'self.context'
        object
        """
        return self._filterCore(link_text, return_brain=True,
                                **kwargs)

    def renderLinkForBrain(self, template, macro, text, brain, **kw):
        """
        returns rendered wicked link that would resolve to the object related
        to the specified brain

        - template: template containing the wicked link macro

        - macro: name of the wicked link macro

        - text: text that is the content of the wicked link

        - self.context: object on which the link is being rendered

        - brain: object to which the link should resolve
        """
        kw['links'] = [{'path': brain.getPath(),
                        'icon': brain.getIcon,
                        'rel_path': utils.getPathRelToPortal(brain.getPath(),
                                                       self.context)}]
        kw['chunk'] = text
        econtext = createContext(self.context, **kw)
        template = self.context.restrictedTraverse(path=template)
        macro = template.macros[macro]
        return macro_render(macro, self.context, econtext, **kw)
