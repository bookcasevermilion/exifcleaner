"""
User manager tests
"""

import unittest
from unittest.mock import patch
from exifcleaner.user import User, errors
import udatetime

class TestUserClass(unittest.TestCase):
    
    def test_validation_no_attributes(self):
        """
        New user object, no attributes provided, check that all errors are returned.
        """
        
        user = User()
        
        expected = [
            errors.ExifCleanerUsernameMissing,
            errors.ExifCleanerPasswordMissing,
            errors.ExifCleanerEmailMissing
        ]
        
        e = user.update()
        
        self.assertEqual(len(e), 3)
        self.assertTrue(e[0].__class__ in expected)
        self.assertTrue(e[1].__class__ in expected)
        self.assertTrue(e[2].__class__ in expected)
    
    def test_user_validation_everything_is_wrong(self):
        """
        Pass nothing but malformed data to the update method.
        """
        user = User()
        
        expected = [
            errors.ExifCleanerJoinedMalformed,
            errors.ExifCleanerActivatedMalformed,
            errors.ExifCleanerAdminMalformed,
            errors.ExifCleanerEmailMissing,
            errors.ExifCleanerUsernameTooLong,
            errors.ExifCleanerPasswordMissing
        ]
        
        e = user.update(
            password=None,
            username='e'*500,
            email="      ",
            activated=0.1,
            admin=object(),
            joined="aasSasdasd"
        )
        
        self.assertEqual(6, len(e))
        self.assertTrue(e[0].__class__ in expected)
        self.assertTrue(e[1].__class__ in expected)
        self.assertTrue(e[2].__class__ in expected)
        self.assertTrue(e[3].__class__ in expected)
        self.assertTrue(e[4].__class__ in expected)
        self.assertTrue(e[5].__class__ in expected)
        
    
    def test_new_user_no_attributes(self):
        """
        New user object, no attributes provided.
        """
        
        current_datetime = udatetime.now()
        current_datetime_text = udatetime.to_string(current_datetime)
        
        with patch('exifcleaner.user.user.udatetime.now') as mocked:
            mocked.return_value = current_datetime
            
            user = User()
        
            user.update()
        
            expected = {
                'password': None,
                'username': None,
                'email': None,
                'key': None,
                'enabled': 0,
                'joined': current_datetime_text,
                'admin': 0,
                'activated': 0
            }
        
        self.assertEqual(expected, user.dict())
        
    def test_dict_proper_values(self):
        """
        Happy-path test - give the User object different from default values, 
        and make sure they come out correctly when calling dict()
        """
        now = udatetime.to_string(udatetime.now())
        
        with patch("exifcleaner.user.user.pbkdf2_sha256.hash") as mocked:
            mocked.return_value = "hashedpass"
            
            user = User()
            
            user.update(password="sensiblepass", 
                        username="bobdobbs",
                        email="bob@dobbs.com",
                        activated=True,
                        admin=True,
                        joined=now,
                        enabled=True)
            
            expected = {
                    'password': "hashedpass",
                    'username': "bobdobbs",
                    'email': "bob@dobbs.com",
                    'key': "user:bobdobbs",
                    'enabled': 1,
                    'joined': now,
                    'admin': 1,
                    'activated': 1
                }
        
        self.assertEqual(expected, user.dict())
        