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