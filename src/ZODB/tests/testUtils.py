##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test the routines to convert between long and 64-bit strings"""

import unittest

NUM = 100


class TestUtils(unittest.TestCase):

    _small = _large = None

    @property
    def small(self):
        import random
        if self._small is None:
            self._small = [random.randrange(1, 1L<<32, int=long)
                            for i in range(NUM)]
        return self._small

    @property
    def large(self):
        import random
        if self._large is None:
            self._large = [random.randrange(1L<<32, 1L<<64, int=long)
                            for i in range(NUM)]
        return self._large

    @property
    def all(self):
        return self.small + self.large

    def testLongToStringToLong(self):
        from ZODB.utils import U64
        from ZODB.utils import p64
        from ZODB.utils import u64
        for num in self.all:
            s = p64(num)
            n = U64(s)
            self.assertEquals(num, n, "U64() failed")
            n2 = u64(s)
            self.assertEquals(num, n2, "u64() failed")

    def testKnownConstants(self):
        from ZODB.utils import U64
        from ZODB.utils import p64
        from ZODB.utils import u64
        self.assertEquals("\000\000\000\000\000\000\000\001", p64(1))
        self.assertEquals("\000\000\000\001\000\000\000\000", p64(1L<<32))
        self.assertEquals(u64("\000\000\000\000\000\000\000\001"), 1)
        self.assertEquals(U64("\000\000\000\000\000\000\000\001"), 1)
        self.assertEquals(u64("\000\000\000\001\000\000\000\000"), 1L<<32)
        self.assertEquals(U64("\000\000\000\001\000\000\000\000"), 1L<<32)

    def testPersistentIdHandlesDescriptor(self):
        from persistent import Persistent
        from ZODB.serialize import ObjectWriter
        class P(Persistent):
            pass

        writer = ObjectWriter(None)
        self.assertEqual(writer.persistent_id(P), None)

    # It's hard to know where to put this test.  We're checking that the
    # ConflictError constructor uses utils.py's get_pickle_metadata() to
    # deduce the class path from a pickle, instead of actually loading
    # the pickle (and so also trying to import application module and
    # class objects, which isn't a good idea on a ZEO server when avoidable).
    def testConflictErrorDoesntImport(self):
        from ZODB.serialize import ObjectWriter
        from ZODB.POSException import ConflictError
        from ZODB.tests.MinPO import MinPO
        import cPickle as pickle

        obj = MinPO()
        data = ObjectWriter().serialize(obj)

        # The pickle contains a GLOBAL ('c') opcode resolving to MinPO's
        # module and class.
        self.assert_('cZODB.tests.MinPO\nMinPO\n' in data)

        # Fiddle the pickle so it points to something "impossible" instead.
        data = data.replace('cZODB.tests.MinPO\nMinPO\n',
                            'cpath.that.does.not.exist\nlikewise.the.class\n')
        # Pickle can't resolve that GLOBAL opcode -- gets ImportError.
        self.assertRaises(ImportError, pickle.loads, data)

        # Verify that building ConflictError doesn't get ImportError.
        try:
            raise ConflictError(object=obj, data=data)
        except ConflictError, detail:
            # And verify that the msg names the impossible path.
            self.assert_('path.that.does.not.exist.likewise.the.class' in
                         str(detail))
        else:
            self.fail("expected ConflictError, but no exception raised")


def test_suite():
    import doctest
    return unittest.TestSuite((
        unittest.makeSuite(TestUtils),
        doctest.DocFileSuite('../utils.txt'),
    ))
