"""
User manager tests
"""

import unittest
from unittest.mock import patch
# from exifcleaner.user import errors
from simpleschema import errors
from exifcleaner.user.manager import User
import udatetime
import random

def static_date(*args, **kwargs):
    """
    Return a known datetime object.
    """
    return udatetime.from_string('1993-10-26T08:00:00-04:00')

def static_id(*args, **kwargs):
    return "1234"

class TestUserClass(unittest.TestCase):
    """
    Test the User class.
    """
    def setUp(self):
        import exifcleaner.user.manager
        
        self._old = {}
        
        self._old['id'] = exifcleaner.user.manager.schema['id'].default
        self._old['joined'] = exifcleaner.user.manager.schema['joined'].default
        
        exifcleaner.user.manager.schema['id'].default = static_id
        exifcleaner.user.manager.schema['joined'].default = static_date
    
    def tearDown(self):
        import exifcleaner.user.manager
        
        exifcleaner.user.manager.schema['id'].default = self._old['id']
        exifcleaner.user.manager.schema['joined'].default = self._old['joined']
    
    @patch("exifcleaner.user.manager.pbkdf2_sha256.hash", lambda x: "did it")
    def test_happy_path(self):
        """
        Populate a User object - typical use case, no errors
        """
        
        u = User(
            username="user1", 
            email="none@donthave.com",
            password="xxxx")
        
        self.assertEqual(u.username, "user1")
        self.assertEqual(u.password, "did it")
        self.assertEqual(u.email, "none@donthave.com")
        self.assertEqual(u.id, "1234")
        self.assertEqual(u.admin, False)
        self.assertEqual(u.activated, False)
        self.assertEqual(u.enabled, True)
        self.assertEqual(u.joined, static_date())
    
    @patch("exifcleaner.user.manager.pbkdf2_sha256.hash", lambda x: "did it")
    def test_to_redis(self):
        """
        Test typical use case of to_redis() method - no errors.
        """
        
        u = User(
            username="user1", 
            email="none@donthave.com",
            password="xxxx")
        
        expected = {
            'email': 'none@donthave.com',
            'username': "user1",
            'password': 'did it',
            'id': '1234',
            'admin': 0,
            'activated': 0,
            'enabled': 1,
            'joined': '1993-10-26T08:00:00.000000-04:00'
        }
        
        self.assertEqual(u.to_redis(), expected)
    
    @patch("exifcleaner.user.manager.pbkdf2_sha256.hash", lambda x: "did it")
    def test_from_redis(self):
        """
        Test typical use case of from_redis() method - no errors.
        """
        
        u = User.from_redis({
            'email': 'none@donthave.com',
            'username': "user1",
            'password': 'did it',
            'id': '1234',
            'admin': '0',
            'activated': '0',
            'enabled': '0',
            'joined': '1993-10-26T08:00:00.000000-04:00'
        })
        
        self.assertEqual(u.username, "user1")
        self.assertEqual(u.password, "did it")
        self.assertEqual(u.email, "none@donthave.com")
        self.assertEqual(u.id, "1234")
        self.assertEqual(u.admin, False)
        self.assertEqual(u.activated, False)
        self.assertEqual(u.enabled, False)
        self.assertEqual(u.joined, static_date())
        
    def test_changed(self):
        """
        Test the changed() method - typical case
        """
        u = User(
            username="user1", 
            email="none@donthave.com",
            password="xxxx")
        
        # initially nothing has changed
        self.assertEqual(u.changed(), [])
        
        u.update(admin=True, activated=True, username="user2")
        
        self.assertEqual(sorted(u.changed()), ['activated', 'admin', 'username'])
        
    def test_authenticate_pass(self):
        """
        Test the authenticate() method. Valid creds provided.
        """
        u = User(
            username="user1", 
            email="none@donthave.com",
            password="xxxx",
            activated=True)
        
        self.assertTrue(u.authenticate("xxxx"))
        
    def test_authenticate_fail(self):
        """
        Test the authenticate() method. Invalid creds provided.
        """
        u = User(
            username="user1", 
            email="none@donthave.com",
            password="xxxx",
            activated=True)
        
        self.assertFalse(u.authenticate("bad!"))        
        