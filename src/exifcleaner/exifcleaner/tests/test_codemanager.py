"""
Tests For The Code Manager - The Code Manager
"""
import pytest
import udatetime, datetime
from exifcleaner import util
import simpleschema
from unittest import mock
import redis
import os
from . import util as testutil

pytestmark = pytest.mark.skipif(not testutil.check_redis(), reason="Redis must be available. Set EXIFCLEANER_REDIS_URL to change from default local server")

@pytest.fixture(autouse=True)
def fixate_randomness(monkeypatch):
    """
    Set well-known values for time and ramdomness-sensative
    functions.
    """
    monkeypatch.setattr("udatetime.now", lambda: udatetime.from_string('1989-10-23T08:00:00-06:00'))
    monkeypatch.setattr(util, "random_id", lambda: "test-xxx-2")
    
@pytest.fixture(scope="module")
def fixture_initial_data():
    """
    Add in the necessary data from other systems that this one is dependant on.
    """
    from exifcleaner.user.manager import UserManager
    from exifcleaner.user.errors import UsernameInUse
    
    users = {}
    
    manager = UserManager()
    
    try:
        users['active'] = manager.add(username="activeuser", activated=True, password="12345", email="none@donthave.com")
        users['inactive'] = manager.add(username="inactiveuser", activated=False, password="12345", email="none@donthave.com")
    except UsernameInUse:
        users['active'] = manager.get("activeuser")
        users['inactive'] = manager.get("inactiveuser")
    
    yield users
    
    manager.delete("activeuser")
    manager.delete("inactiveuser")
    
def test_add_happy_path(fixture_initial_data):
    """
    Add a new code using the manager. Typical use case. 
    """
    from exifcleaner.codes.manager import CodeManager
    
    manager = CodeManager()
    
    c = manager.new("activeuser")
    
    assert c.user == fixture_initial_data['active'].id
    assert c.code == "test-xxx-2"
    assert c.created == udatetime.from_string('1989-10-23T08:00:00-06:00')
    assert c.expires == 3600
    assert c.used is False
    assert c.key == "code:test-xxx-2"
    assert c.expires_at() == udatetime.from_string('1989-10-23T09:00:00-06:00')