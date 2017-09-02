# exifcleaner

## Dev Setup

### Pre-requisites

  
  - redis
  - python 3.5+
  
### Setup

```
$ git clone ...
$ cd exifcleaner
$ virtualenv .
$ sorce bin/activate
$ pip install -e src/english-ids
$ pip install -e src/exifcleaner
$ pip install -r requirements.txt
```

## Dev Server

```
$ mkdir tmp
$ source bin/activate
$ redis-server &
$ gunicorn --reload wsgi:app
```

Default port is 8000. Static files are served at /. API is 


### Workers

Run in a separate shell (TODO: supervisord/etc to control the stack instead):

```
$ source bin/activate
$ rq worker exifcleaner
```

### Scheduler Service

Run in a separate shell (TODO: supervisord/etc to control the stack instead):

```
$ source bin/activate
$ rqscheduler
```