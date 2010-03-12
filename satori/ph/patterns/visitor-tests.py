"""Test suite for ph.patterns.visitor"""

import unittest

from satori.ph.patterns import visitor


class A(object):					# pylint: disable-msg=C0103,C0111
	pass

class B(A):						# pylint: disable-msg=C0103,C0111
	pass

class C(A):						# pylint: disable-msg=C0103,C0111
	pass

class D(B):						# pylint: disable-msg=C0103,C0111
	pass

class E(C, B):						# pylint: disable-msg=C0103,C0111
	pass

class Visitor(unittest.TestCase):			# pylint: disable-msg=C0103,C0111
	
	@visitor.Dispatch(argument=1)
	def visit(self, _):				# pylint: disable-msg=C0103,C0111,R0201
		return '*'
	
	@visitor.Implement(type=A)
	def visit(self, _): 				# pylint: disable-msg=E0102,C0111,R0201
		return 'A'
	
	@visitor.Implement(type=C)
	def visit(self, _): 				# pylint: disable-msg=E0102,C0111,R0201
		return 'C'
	
	@visitor.Implement(type=D)
	def visit(self, _): 				# pylint: disable-msg=E0102,C0111,R0201
		return 'D'
	
	def test(self):
		self.assertEqual(self.visit(None), '*')
		self.assertEqual(self.visit(A()), 'A')
		self.assertEqual(self.visit(B()), 'A')
		self.assertEqual(self.visit(C()), 'C')
		self.assertEqual(self.visit(D()), 'D')
		self.assertEqual(self.visit(E()), 'C')
