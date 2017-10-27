"""
Tests For The User Manager - Functional Tests For The UserManager class.
"""
import pytest
import random
import udatetime, datetime
from exifcleaner import util
import redis
import os
from . import util as testutil
import simpleschema

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
def usermanager():
    """
    Import the module and create a UserManager object, reset the database, 
    add test users.
    """
    from exifcleaner.user.manager import UserManager
    
    manager = UserManager()
    
    manager.redis.flushdb()
    
    # user who is used for password checking.
    manager.add(username="mylovelyuser", 
                activated=True, 
                enabled=True, 
                password="xxxxx", 
                email="my@email.com")
    
    # user used for authenticating an unactivate user
    manager.add(username="unactivated", password="qqqqq", email="blah@blah.com")
    
    # user used to 
    manager.add(username="to_change", 
                activated=True, 
                enabled=True, 
                password="qqqqq", 
                email="blah@blah.com")
    
    common = {
        "username": "paging",
        "email": "some-email@blah.com",
        "password": "always-the-same"
    }
    
    for x in range(4, 24):
        spec = common.copy()
        
        spec['username'] = "{}-{:0>3}".format(spec['username'], x)
        manager.add(**spec)
    
    yield manager
    
    manager.redis.flushdb()
    
def test_add_get_typical(usermanager):
    """
    Test adding a user, typical use case.
    """
    usermanager.add(
        username="test-user",
        password="12345", 
        email="none@donthave.com")
    
    user = usermanager.get("test-user")
    
def test_add_with_existing_username(usermanager):
    """
    Try adding a user when a user with that username already exists.
    """
    from exifcleaner.user.errors import UsernameInUse
    
    usermanager.add(username="test-user-2", password="12345", email="none@donthave.com")
    
    with pytest.raises(UsernameInUse):
        usermanager.add(username="test-user-2", password="12345", email="none@donthave.com")

def test_add_with_bad_data(usermanager):
    """
    Try adding a user with some bad data, ensure it raises an error.
    """
    
    with pytest.raises(simpleschema.errors.SchemaError) as err:
        usermanager.add(username="x"*400, password="12345", email="none@donthave.com", admin="duh")
        
    assert isinstance(err.value.errors['username'], simpleschema.errors.TooLong)
    assert isinstance(err.value.errors['admin'], simpleschema.errors.BadBoolean)
    
    with pytest.raises(KeyError):
        err.value.errors['password']
    
def test_add_nothing_passed(usermanager):
    """
    Try adding a user without providing required fields.
    """
    with pytest.raises(simpleschema.errors.SchemaError) as err:
        usermanager.add()
        
    assert isinstance(err.value.errors['username'], simpleschema.errors.MissingValue)
    assert isinstance(err.value.errors['password'], simpleschema.errors.MissingValue)
    assert isinstance(err.value.errors['email'], simpleschema.errors.MissingValue)
    
    assert len(err.value.errors) is 3
    
def test_get_not_found(usermanager):
    """
    Check that UserManager.get() rasies an error on an non-existing user.
    """
    from exifcleaner.user.errors import UserNotFound
    
    with pytest.raises(UserNotFound):
        usermanager.get("use23212423423423423423423423423")
        
def test_exists_doesnt_exist(usermanager):
    """
    Test UserManager.exists(), when the user isn't in the db.
    """
    assert usermanager.exists("dsdfasdgfasdgasd fasdf") is False
    
def test_exists_user_exist(usermanager):
    """
    Test UserManager.exists(), when the user is in the db.
    """
    assert usermanager.exists("mylovelyuser") is True    
    
def test_authenticate_pass_typical(usermanager):
    """
    Authenticate a user, the user exists, and we give a valid password.
    """
    assert usermanager.authenticate("mylovelyuser", "xxxxx") is True
    
def test_authenticate_fail_user_doesnt_exist(usermanager):
    """
    Authenticate a user, the user doesn't exist.
    """
    assert usermanager.authenticate("test-user-nonexistant-forever", "xxxxx") is False
    
def test_authenticate_fail_bad_password(usermanager):
    """
    Authenticate a user, the user exists, and we give an invalid password.
    """
    assert usermanager.authenticate("mylovelyuser", "xxxxx1") is False
    
def test_authenticate_fail_not_activated(usermanager):
    """
    Authenticate a user with the right password, but the user is not activated.
    """
    usermanager.modify("mylovelyuser", activated=False)
    assert usermanager.authenticate("mylovelyuser", "xxxxx") is False
    
def test_authenticate_fail_deactivated(usermanager):
    """
    Authenticate a user with the right password, but the user is not enabled.
    """
    usermanager.modify("mylovelyuser", enabled=False)
    assert usermanager.authenticate("mylovelyuse", "xxxxx") is False
    
def test_activation(usermanager):
    """
    Activate a user.
    """
    
    user = usermanager.get("unactivated")
    assert user.activated is False
    assert user.enabled is True
    
    usermanager.activate("unactivated")
    
    user = usermanager.get("unactivated")
    assert user.activated is True
    
    
def test_activation_user_not_found(usermanager):
    """
    Try to activate a user that doesn't exist.
    """
    from exifcleaner.user.errors import UserNotFound
    with pytest.raises(UserNotFound):
        usermanager.activate("sddasdadsfsadfas dfsdfasdf asdf asdf asd")
        
def test_delete_typical(usermanager):
    """
    Delete a user.
    """
    usermanager.add(username="to_delete", password="qqqqq", email="deleteme@sdfasdsdas.blah")
    
    assert usermanager.exists("to_delete") is True
    
    usermanager.delete("to_delete")
    
    assert usermanager.exists("to_delete") is False
    
def test_delete_not_found(usermanager):
    """
    Try to delete a user that doesn't exist
    """
    from exifcleaner.user.errors import UserNotFound
    with pytest.raises(UserNotFound):
        usermanager.delete("sddasdadsfsadfas dfsdfasdf asdf asdf asd")
    
def test_modify_typical(usermanager):
    """
    Modify a user, typical "happy path" - change everything
    """
    old = usermanager.modify(
        "to_change", 
        username="othername", 
        password="newpass",
        email="newemail@new.com",
        activated=False,
        enabled=False,
        joined=udatetime.from_string('2010-10-23T08:00:00-06:00'))
    
    assert usermanager.exists("to_change") is False
    assert usermanager.exists("othername") is True
    
    user = usermanager.get("othername")
    assert user.id == old.id
    assert user.key == old.key
    assert user.username == "othername"
    assert user.activated is False
    assert user.enabled is False
    assert user.joined == udatetime.from_string('2010-10-23T08:00:00-06:00')
    
    # skip enabled/activated check
    assert user.authenticate("newpass", True)
    
def test_modify_user_bad_data(usermanager):
    """
    Modify a user, but provide some bad data.
    """
    with pytest.raises(simpleschema.errors.SchemaError) as err:
        usermanager.modify("mylovelyuser", activated="boo", password="x"*600, email="bad_email")
        
    assert isinstance(err.value.errors['activated'], simpleschema.errors.BadBoolean)
    assert isinstance(err.value.errors['password'], simpleschema.errors.TooLong)
    assert isinstance(err.value.errors['email'], simpleschema.errors.NotAnEmail)
    
    assert len(err.value.errors) is 3
    
def test_modify_user_username_exists(usermanager):
    """
    Try to modify a user's username, providing a username already in use.
    """
    from exifcleaner.user.errors import UsernameInUse
    with pytest.raises(UsernameInUse):
        usermanager.modify("mylovelyuser", username="unactivated")
        
def test_modify_user_not_exists(usermanager):
    """
    Try to modify a user that doesn't exist.
    """
    from exifcleaner.user.errors import UserNotFound
    with pytest.raises(UserNotFound):
        usermanager.modify("sadf as;dfjk sdlkf lsd.f lsdhj lskdh ", activated="False")
        
def test_users_get_all(usermanager):
    """
    Get all of the users, typical use case.
    """
    users = usermanager.users()
    
    assert len(users) == 25
    
def test_users_page(usermanager):
    """
    Grab a single range of users.
    """
    users = usermanager.users(20, 25)
    
    assert len(users) == 5
    
    assert users[0].username == "test-user-2"
    assert users[1].username == "test-user"
    assert users[2].username == "mylovelyuser"
    assert users[3].username == "othername"
    assert users[4].username == "unactivated"