import unittest

from satori.ars.naming import NameKind, NameComponent


class Parsing(unittest.TestCase):

	def setUp(self):
		self.kind = NameKind(name='(none)')

	def testLower(self):
		name = NameComponent(string='lowercase', kind=self.kind)
		self.assertEqual(name.words, ['lowercase'])

	def testUpper(self):
		name = NameComponent(string='UPPERCASE', kind=self.kind)
		self.assertEqual(name.words, ['UPPERCASE'])

	def testCamel(self):
		name = NameComponent(string='CamelCase', kind=self.kind)
		self.assertEqual(name.words, ['Camel', 'Case'])

	def testPascal(self):
		name = NameComponent(string='pascalCase', kind=self.kind)
		self.assertEqual(name.words, ['pascal', 'Case'])

	def testUnderscores(self):
		name = NameComponent(string='a_FewWords_withUnderscores_', kind=self.kind)
		self.assertEqual(name.words, ['a', 'Few', 'Words', 'with', 'Underscores'])

	def testWhiteSpace(self):
		name = NameComponent(string=' a\tText_withSome  embedded\nWHITESPACE\t ', kind=self.kind)
		self.assertEqual(name.words, ['a', 'Text', 'with', 'Some', 'embedded', 'WHITESPACE'])
