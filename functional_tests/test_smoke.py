"""
Functional test suite - smoke tests.
"""
import requests
import time
import pprint
import piexif
import datetime
import sys

BASE_URL = "http://127.0.0.1:8000"

# post an image
files = {'input': open("media/shadows.jpg", "rb")}

r = requests.post(BASE_URL+"/clean", files=files)

id_ = r.json()

# use the id returned to check the status of the processing job
output = {"is_finished": False}

# when "is_finished" is true, the job is done.
while output.get("is_finished", False) is False:
    r = requests.get(BASE_URL+"/status/{}".format(id_))
    print(r.text)
    output = r.json()
    if output.get("is_failed", False):
        print("ERROR: Job failed!")
        sys.exit(0)
    
    time.sleep(0.5)

# check for the json exif data
r = requests.get(BASE_URL+"/data/{}.json".format(id_))

print("EXIF DATA in {}".format(id_))
print("=====================================")
pprint.pprint(r.json())

# check for the thumbnail
r = requests.get(BASE_URL+"/data/{}.thumb.jpg".format(id_))

print("Return code for {}.thumb.jpg: {}".format(id_, r.status_code))

### check for the cleaned image, download it, and print exif data

# save the image
r = requests.get(BASE_URL+"/data/{}.jpg".format(id_), stream=True)

if r.status_code != 200:
    print("ERROR: request for {} returned status code {}".format(id_, r.status_code))
else:
    # download the image
    outfile = "./test-file.jpg"
    
    with open(outfile, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
            
    # get the new EXIF data:
    data = piexif.load(outfile)
    
    print("NEW EXIF DATA AFTER CLEANING")
    print("=========================================")
    pprint.pprint(data)

wait = input("Wait 12 minute for the files to be deleted? (y/[n]) ")

if wait.lower() in ['y']:
    print("Waiting 12 minutes for the image and related files to be removed...", end='', flush=True)
    elapsed = datetime.timedelta(0)
    start = datetime.datetime.now()
    while elapsed.seconds < 60*12:
        time.sleep(5)
        # print(".", end="", flush=True)
        print(elapsed.seconds)
        now = datetime.datetime.now()
        elapsed = now - start
        
    print("", flush=True)
    
    print("Checking if the files were removed:", flush=True)
    for url in ["{}/data/{}.jpg", "{}/data/{}.json", "{}/data/{}.thumb.jpg"]:
        print("\t", "Does ", url.format(BASE_URL, id_), " exist?", end="", flush=True)
        r = requests.get(url.format(BASE_URL, id_))
        if r.status_code == 404:
            print("... Nope!", flush=True)
        else:
            print("... Yes. (code {})".format(r.status_code), flush=True)
            

print("Trying to upload a non-jpeg file")
files = {'input': open("media/shadows.png", "rb")}

r = requests.post(BASE_URL+"/clean", files=files)

if r.status_code != 400:
    print("ERROR: bad file accepted")
else:
    print("400 recieved. Bad file rejected.")