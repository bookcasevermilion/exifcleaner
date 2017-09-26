"""
Activation Service - smoke tests.
"""
import requests
from requests.auth import HTTPBasicAuth

from exifcleaner.user.manager import UserManager

# TODO: set these from environment variables
BASE_URL = "http://127.0.0.1:8000"
REDIS_URL = "redis://127.0.0.1:6379"

um = UserManager(redis_url=REDIS_URL)

ok = input("Clear the database? [[y]/n]: ")

if ok.strip().lower() in ["", "y"]:
    print("Clearing the database at {}".format(REDIS_URL))
    um.connection.flushdb()
    
    print("Adding test users:")
    
    for username in ['user1', 'user2', 'admin']:
        password = "xxxx"
        email = "none@donthave.com"
        print("\tAdding {} with password {}".format(username, password))
        
        user = um.add(username=username, password=password, email=email)
        print("\t\t", user)
        
    print("")
    print("\tMaking 'admin' user an admin, activating")
    
    um.modify('admin', admin=True, activated=True)
    
    print("\t\t", um.get("admin"))
    
    print("")
    print("====================================")
    print("")


print("Adding an activation using the REST API:")
r = requests.post(
    BASE_URL+"/activations", 
    auth=HTTPBasicAuth("admin", "xxxx"),
    data={"username": "user1"})

activation = r.json()

print(activation)

print("Get an activation using the REST API:")
r = requests.get(BASE_URL+"/activation/"+activation['code'], auth=HTTPBasicAuth("admin", "xxxx"))
print(r.json())

print("Activate an activation using the REST API:")
r = requests.get(BASE_URL+"/activate/"+activation['code'], auth=HTTPBasicAuth("user1", "xxxx"))
print(r.text)

print("Trying to get a used code:")
r = requests.get(BASE_URL+"/activation/"+activation['code'], auth=HTTPBasicAuth("admin", "xxxx"))
print(r.status_code)

print("Checking the user to see if they are now activated:")
user = um.get("user1")
print(user)

print("Create a new code:")
print("Adding an activation using the REST API:")
r = requests.post(
    BASE_URL+"/activations", 
    auth=HTTPBasicAuth("admin", "xxxx"),
    data={"username": "user1"})

activation = r.json()

print(activation)

print("Delete an activation using the REST API:")
r = requests.delete(BASE_URL+"/activation/"+activation['code'], auth=HTTPBasicAuth("admin", "xxxx"))
print(r.text)

print("Trying to get a deleted code:")
r = requests.get(BASE_URL+"/activation/"+activation['code'], auth=HTTPBasicAuth("admin", "xxxx"))
print(r.status_code)

print("Creating 34 activation codes:")
for i in range(34):
    r = requests.post(
        BASE_URL+"/activations", 
        auth=HTTPBasicAuth("admin", "xxxx"),
        data={"username": "user1"})
    print("\t{}:{}".format(i, r.text))
    

