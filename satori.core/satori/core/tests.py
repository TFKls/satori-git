# vim:ts=4:sts=4:sw=4:expandtab
"""Test suite for satori.core.
"""

import unittest

import satori.core.setup
from satori.core.sec import Token
from datetime import timedelta

import crypt
from satori.core.models import User, Privilege
from satori.core.models import Login
from satori.ars import django_
from satori.ars.naming import Name, ClassName, MethodName
import satori.core.sec

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
        tok1 = Token(user_id='test_user', data='\n'.join(['test', 'data']), auth='test_auth', validity=timedelta(days=1))

        print 'Token:    ', tok1
        print 'User:     ', tok1.user_id
        print 'Auth:     ', tok1.auth
        print 'Data:     ', tok1.data
        print 'Valid:    ', tok1.valid
        print 'Deadline: ', tok1.deadline
        print 'Validity: ', tok1.validity
        print 'Salt:     ', tok1.salt

        
        tok2 = Token(str(tok1))
        self.assertEqual(tok2.user_id, 'test_user')
        self.assertEqual(tok2.auth, 'test_auth')
        self.assertEqual(tok2.salt, tok1.salt)
        
        print 'Token:    ', tok2
        print 'User:     ', tok2.user_id
        print 'Auth:     ', tok2.auth
        print 'Data:     ', tok2.data
        print 'Valid:    ', tok2.valid
        print 'Deadline: ', tok2.deadline
        print 'Validity: ', tok2.validity
        print 'Salt:     ', tok2.salt

    def tearDown(self):
        """Clean up.
        """
        pass

class TestLogin(unittest.TestCase):
    """Test login mechanism.
    """

    def setUp(self):
        #u = User(login='mammoth', fullname='Grzegorz Gutowski')
        #u.save()
        u = User.objects.get(login='mammoth')
        #l = Login(login='mammoth', password=crypt.crypt('mammoth','aaa'), user=u)
        #l.save()
        l = Login.objects.get(login='mammoth')
        p = Privilege(object=u, role=u, right='ADMIN')
        p.save()
        django_.generate_contracts()
        satori.core.sec.generate_contracts(django_.contract_list)

    def testLogin(self):
        login = satori.core.sec.contract_list[0].procedures.names[Name(ClassName('Security'))+Name(MethodName('login'))]
        whoami = satori.core.sec.contract_list[0].procedures.names[Name(ClassName('Security'))+Name(MethodName('whoami'))]
        cani = satori.core.sec.contract_list[0].procedures.names[Name(ClassName('Security'))+Name(MethodName('cani'))]

        tok = Token(login.implementation('mammoth', 'mammoth'))
        print 'Token:    ', tok
        print 'User:     ', tok.user
        print 'Auth:     ', tok.auth
        print 'Data:     ', tok.data
        print 'Valid:    ', tok.valid
        print 'Deadline: ', tok.deadline
        print 'Validity: ', tok.validity
        print 'Salt:     ', tok.salt
        id = whoami.implementation(str(tok))
        print 'User.login', User.objects.get(id=id).login
        print 'VIEW?', cani.implementation(str(tok), id, 'VIEW')




if __name__ == '__main__':
	unittest.main()
