"""
wicked
~~~~~~~~~~

A field drop-in wiki
"""

__authors__ = 'Whit Morriss <whit@kalistra.com>, Rob Miller <ra@burningman.com>'
__docformat__ = 'restructuredtext'

PROJECTNAME            = "wicked"
SKINS_DIR              = 'skins'
GLOBALS                = globals()
BACKLINK_RELATIONSHIP  = 'Backlink->Source Doc'

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
