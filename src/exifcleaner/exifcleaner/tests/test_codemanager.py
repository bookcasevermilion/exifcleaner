"""
Tests For The Code Manager - The Code Manager
"""
import pytest
import random
import udatetime, datetime
from exifcleaner import util
import simpleschema
from unittest import mock
import redis
import os
from . import util as testutil

pytestmark = pytest.mark.skipif(not testutil.check_redis(), reason="Redis must be available. Set EXIFCLEANER_REDIS_URL to change from default local server")

@pytest.fixture()
def fixate_now(monkeypatch):
    monkeypatch.setattr("udatetime.now", lambda: udatetime.from_string('1993-10-26T08:00:00-04:00'))

@pytest.fixture()
def fixate_randomness():
    """
    Set well-known values for time and ramdomness-sensative
    functions.
    """
    random.seed(200)

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
    
    manager.redis.flushdb()
    
def test_add_happy_path(fixture_initial_data, fixate_randomness, fixate_now):
    """
    Add a new code using the manager. Typical use case. 
    """
    from exifcleaner.codes.manager import CodeManager
    
    manager = CodeManager()
    
    manager.new("activeuser")
    
    code = manager.get("activeuser")
    
    assert code.user == fixture_initial_data['active'].id
    assert code.code == "hODPLE"
    assert code.created == udatetime.from_string('1993-10-26T08:00:00-04:00')
    assert code.expires == 3600
    assert code.used is False
    assert code.key == "code:hODPLE"
    assert code.expires_at() == udatetime.from_string('1993-10-26T09:00:00-04:00')
    
