# vim:ts=4:sts=4:sw=4:expandtab
import unittest

from satori.ars.naming import NameKind, NameComponent


class Parsing(unittest.TestCase):

    def setUp(self):
        self.kind = NameKind('(none)')

    def testLower(self):
        name = NameComponent('lowercase', self.kind)
        self.assertEqual(name.words, ['lowercase'])

    def testUpper(self):
        name = NameComponent('UPPERCASE', self.kind)
        self.assertEqual(name.words, ['UPPERCASE'])

    def testCamel(self):
        name = NameComponent('CamelCase', self.kind)
        self.assertEqual(name.words, ['Camel', 'Case'])

    def testPascal(self):
        name = NameComponent('pascalCase', self.kind)
        self.assertEqual(name.words, ['pascal', 'Case'])

    def testUnderscores(self):
        name = NameComponent('a_FewWords_withUnderscores_', self.kind)
        self.assertEqual(name.words, ['a', 'Few', 'Words', 'with', 'Underscores'])

    def testWhiteSpace(self):
        name = NameComponent(' a\tText_withSome  embedded\nWHITESPACE\t ', self.kind)
        self.assertEqual(name.words, ['a', 'Text', 'with', 'Some', 'embedded', 'WHITESPACE'])
