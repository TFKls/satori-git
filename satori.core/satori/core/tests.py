from six import print_
#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:expandtab
"""Test suite for satori.core.
"""

import unittest

import satori.core.setup
from satori.core.sec.token import Token
from datetime import timedelta

import crypt
from satori.core.models import User, Privilege
from satori.core.models import Login
from satori.ars import django_
from satori.ars.naming import Name, ClassName, MethodName
import satori.core.sec
from satori.core.api import Security

class TestToken(unittest.TestCase):
    """Test token manipulation.
    """

    def setUp(self):
        """Prepare test environment.
        """
        pass

    def testToken(self):
        """Test scenario: create token by parameters, and by string.
        """
        tok1 = Token(user_id='test_user', data={'test' : 'data'}, auth='test_auth', validity=timedelta(days=1))

        print_('Token:    ', tok1)
        print_('User:     ', tok1.user_id)
        print_('Auth:     ', tok1.auth)
        print_('Data:     ', tok1.data)
        print_('Valid:    ', tok1.valid)
        print_('Deadline: ', tok1.deadline)
        print_('Validity: ', tok1.validity)
        print_('Salt:     ', tok1.salt)


        tok2 = Token(str(tok1))
        self.assertEqual(tok2.user_id, 'test_user')
        self.assertEqual(tok2.auth, 'test_auth')
        self.assertEqual(tok2.salt, tok1.salt)

        print_('Token:    ', tok2)
        print_('User:     ', tok2.user_id)
        print_('Auth:     ', tok2.auth)
        print_('Data:     ', tok2.data)
        print_('Valid:    ', tok2.valid)
        print_('Deadline: ', tok2.deadline)
        print_('Validity: ', tok2.validity)
        print_('Salt:     ', tok2.salt)

    def tearDown(self):
        """Clean up.
        """
        pass

class TestLogin(unittest.TestCase):
    """Test login mechanism.
    """

    def setUp(self):
        u = User.objects.filter(login='mammoth')
        if len(u) == 0:
            u = User(login='mammoth', name='Grzegorz Gutowski')
            u.save()
        u = User.objects.get(login='mammoth')
        l = Login.objects.filter(login='mammoth')
        if len(l) == 0:
            l = Login(login='mammoth', password=crypt.crypt('mammoth','aaa'), user=u)
            l.save()
        l = Login.objects.get(login='mammoth')
        p = Privilege.objects.filter(object=u, role=u, right='ADMIN')
        if len(p) == 0:
            p = Privilege(object=u, role=u, right='ADMIN')
            p.save()

    def testLogin(self):
        tok = Security.Security__login(login='mammoth', password='mammoth', namespace='')
        print_('Token:    ', tok)
        print_('User:     ', tok.user)
        print_('Auth:     ', tok.auth)
        print_('Data:     ', tok.data)
        print_('Valid:    ', tok.valid)
        print_('Deadline: ', tok.deadline)
        print_('Validity: ', tok.validity)
        print_('Salt:     ', tok.salt)
        user = Security.Security__whoami(token=tok)
        print_('User.login', user.login)
        print_('VIEW?', Security.Security__right_have(token=tok, object=user, right='VIEW'))




if __name__ == '__main__':
    unittest.main()
