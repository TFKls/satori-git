# vim:ts=4:sts=4:sw=4:expandtab
"""Test suite for satori.sec.
"""

import unittest

from satori.sec import Token
from datetime import timedelta

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
        tok1 = Token(user='test_user', data='\n'.join(['test', 'data']), auth='test_auth', validity=timedelta(days=1))

        print 'Token:    ', tok1
        print 'User:     ', tok1.user
        print 'Auth:     ', tok1.auth
        print 'Data:     ', tok1.data
        print 'Valid:    ', tok1.valid
        print 'Deadline: ', tok1.deadline
        print 'Validity: ', tok1.validity
        print 'Salt:     ', tok1.salt

        
        tok2 = Token(str(tok1))
        self.assertEqual(tok2.user, 'test_user')
        self.assertEqual(tok2.auth, 'test_auth')
        self.assertEqual(tok2.salt, tok1.salt)
        
        print 'Token:    ', tok2
        print 'User:     ', tok2.user
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

if __name__ == '__main__':
	unittest.main()
