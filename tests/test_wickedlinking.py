import os, sys, time
import unittest
from sets import Set
import traceback

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from wickedtestcase import WickedTestCase, makeContent
from Products.wicked.lib.normalize import titleToNormalizedId
from Products.wicked.config import BACKLINK_RELATIONSHIP

class TestWikiLinking(WickedTestCase):
    wicked_type = 'IronicWiki'
    wicked_field = 'body'
    
    def afterSetUp(self):
        WickedTestCase.afterSetUp(self)
        self.page1.setBody('((DMV Computer has died))')

    def replaceCreatedIndex(self):
        """ replace the 'created' index w/ a field index b/c we need
        better than 1 minute resolution for our testing """
        cat = self.portal.portal_catalog
        cat.delIndex('created')
        cat.manage_addIndex('created', 'FieldIndex',
                            extra={'indexed_attrs':'created'})
        cat.manage_reindexIndex(ids=['created'])

    def test_backlink(self):
        assert self.page1 in self.page2.getRefs(relationship=BACKLINK_RELATIONSHIP)

    def testforlink(self):
        self.failUnless(self.hasWickedLink(self.page1, self.page2))

    def testformultiplelinks(self):
        self.page1.setBody('((DMV Computer has died))  ((Make another link))')
        self.failUnless(self.hasAddLink(self.page1))
        self.failUnless(self.hasWickedLink(self.page1, self.page2))

    def testLocalIdBeatsLocalTitle(self):
        w1 = makeContent(self.folder, 'IdTitleClash',
                         self.test_type, title='Some Title')
        w2 = makeContent(self.folder, 'some_other_id',
                         self.test_type, title='IdTitleClash')
        self.page1.setBody("((%s))" % w1.id) # matches w2 title
        self.failUnless(self.hasWickedLink(self.page1, w1))
        self.failIf(self.hasWickedLink(self.page1, w2))

    def testLocalIdBeatsRemoteId(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(f2, self.page1.id, self.test_type,
                         title='W1 Title')
        w2 = makeContent(f2, 'w2_id', self.test_type,
                         title='W2 Title')
        w2.setBody("((%s))" % self.page1.id)
        self.failUnless(self.hasWickedLink(w2, w1))
        self.failIf(self.hasWickedLink(w2, self.page1))

    def testLocalTitleBeatsRemoteId(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(f2, 'w1_id', self.test_type,
                         title=self.page1.id)
        w2 = makeContent(f2, 'w2_id', self.test_type,
                         title='W2 Title')
        w2.setBody("((%s))" % self.page1.id)
        self.failUnless(self.hasWickedLink(w2, w1))
        self.failIf(self.hasWickedLink(w2, self.page1))
        
    def testInexactTitleNotMatch(self):
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title='W1 Title With Extra')
        self.page1.setBody("((W1 Title))")
        self.failIf(self.hasWickedLink(self.page1, w1))
        self.failUnless(self.hasAddLink(self.page1))

    def testInexactTitleNotBlockLocalId(self):
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.test_type,
                         title='%s With Extra' % w1.id)
        self.page1.setBody("((%s))" % w1.id)
        self.failUnless(self.hasWickedLink(self.page1, w1))
        self.failIf(self.hasWickedLink(self.page1, w2))

    def testInexactLocalTitleNotBlockLocalTitle(self):
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.test_type,
                         title='%s With Extra' % w1.Title())
        self.page1.setBody("((%s))" % w1.Title())
        self.failUnless(self.hasWickedLink(self.page1, w1))
        self.failIf(self.hasWickedLink(self.page1, w2))

    def testInexactLocalTitleNotBlockRemoteId(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title='W1 Title')
        w2 = makeContent(f2, 'w2', self.test_type,
                         title='%s With Extra' % w1.id)
        w3 = makeContent(f2, 'w3', self.test_type,
                         title='W3 Title')
        w3.setBody("((%s))" % w1.id)
        self.failUnless(self.hasWickedLink(w3, w1))
        self.failIf(self.hasWickedLink(w3, w2))

    def testInexactRemoteTitleNotBlockRemoteId(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.test_type,
                         title='%s With Extra' % w1.id)
        w3 = makeContent(f2, 'w3', self.test_type,
                         title='W3 Title')
        w3.setBody("((%s))" % w1.id)
        self.failUnless(self.hasWickedLink(w3, w1))
        self.failIf(self.hasWickedLink(w3, w2))

    def testInexactLocalTitleNotBlockRemoteTitle(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title='W1 Title')
        w2 = makeContent(f2, 'w2', self.test_type,
                         title='%s With Extra' % w1.Title())
        w3 = makeContent(f2, 'w3', self.test_type,
                         title='W3 Title')
        w3.setBody("((%s))" % w1.Title())
        self.failUnless(self.hasWickedLink(w3, w1))
        self.failIf(self.hasWickedLink(w3, w2))

    def testInexactRemoteTitleNotBlockRemoteTitle(self):
        f2 = makeContent(self.folder, 'f2', 'Folder')
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title='W1 Title')
        w2 = makeContent(self.folder, 'w2', self.test_type,
                         title='%s With Extra' % w1.Title())
        w3 = makeContent(f2, 'w3', self.test_type,
                         title='W3 Title')
        w3.setBody("((%s))" % w1.Title())
        self.failUnless(self.hasWickedLink(w3, w1))
        self.failIf(self.hasWickedLink(w3, w2))

    def testDupLocalTitleMatchesOldest(self):
        self.replaceCreatedIndex()
        title = 'Duplicate Title'
        w1 = makeContent(self.folder, 'w1', self.test_type,
                         title=title)
        w2 = makeContent(self.folder, 'w2', self.test_type,
                         title=title)
        w3 = makeContent(self.folder, 'w3', self.test_type,
                         title=title)
        self.page1.setBody("((%s))" % title)
        self.failUnless(self.hasWickedLink(self.page1, w1))
        self.failIf(self.hasWickedLink(self.page1, w2))
        self.failIf(self.hasWickedLink(self.page1, w3))

        self.folder.manage_delObjects(ids=[w1.id])
        self.failUnless(self.hasWickedLink(self.page1, w2))
        self.failIf(self.hasWickedLink(self.page1, w3))

    def testDupRemoteIdMatchesOldest(self):
        self.replaceCreatedIndex()
        id = 'duplicate_id'
        f2 = makeContent(self.folder, 'f2', 'Folder')
        f3 = makeContent(self.folder, 'f3', 'Folder')
        f4 = makeContent(self.folder, 'f4', 'Folder')
        w1 = makeContent(f2, id, self.test_type,
                         title='W1 Title')
        # mix up the order, just to make sure
        w3 = makeContent(f4, id, self.test_type,
                         title='W3 Title')
        w2 = makeContent(f3, id, self.test_type,
                         title='W2 Title')
        self.page1.setBody("((%s))" % id)
        self.failUnless(self.hasWickedLink(self.page1, w1))
        self.failIf(self.hasWickedLink(self.page1, w2))
        self.failIf(self.hasWickedLink(self.page1, w3))

        f2.manage_delObjects(ids=[w1.id])
        self.failUnless(self.hasWickedLink(self.page1, w3))
        self.failIf(self.hasWickedLink(self.page1, w2))

    def testDupRemoteTitleMatchesOldest(self):
        self.replaceCreatedIndex()
        title = 'Duplicate Title'
        f2 = makeContent(self.folder, 'f2', 'Folder')
        f3 = makeContent(self.folder, 'f3', 'Folder')
        f4 = makeContent(self.folder, 'f4', 'Folder')
        w1 = makeContent(f2, 'w1', self.test_type,
                         title=title)
        # mix up the order, just to make sure
        w3 = makeContent(f4, 'w3', self.test_type,
                         title=title)
        w2 = makeContent(f3, 'w2', self.test_type,
                         title=title)
        self.page1.setBody("((%s))" % title)
        self.failUnless(self.hasWickedLink(self.page1, w1))
        self.failIf(self.hasWickedLink(self.page1, w2))
        self.failIf(self.hasWickedLink(self.page1, w3))

        f2.manage_delObjects(ids=[w1.id])
        self.failUnless(self.hasWickedLink(self.page1, w3))
        self.failIf(self.hasWickedLink(self.page1, w2))
    

class TestDocCreation(WickedTestCase):
    test_type = 'IronicWiki'
    wicked_field = 'body'
    
    def afterSetUp(self):
        WickedTestCase.afterSetUp(self)
        self.title = 'Create a New Document'
        self.page1.setBody('((%s))' %self.title)
        self._refreshSkinData()

    def demoCreate(self):
        self.login('test_user_1_')
        self.page1.addByWickedLink(Title=self.title)
        
    def testDocAdded(self):
        self.demoCreate()
        self.failUnless(getattr(self.folder,
                                titleToNormalizedId(self.title), None))

    def testBacklinks(self):
        self.demoCreate()
        newdoc = getattr(self.folder, titleToNormalizedId(self.title))
        backlinks = newdoc.getRefs(relationship=BACKLINK_RELATIONSHIP)
        self.failUnless(self.page1 in backlinks)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDocCreation))
    suite.addTest(unittest.makeSuite(TestWikiLinking))
    return suite

if __name__ == '__main__':
    framework()