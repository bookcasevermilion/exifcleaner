# exifcleaner

## Dev Setup

$ git clone ...
$ cd exifcleaner
$ virtualenv .
$ sorce bin/activate
$ pip install -e src/*
$ pip install -r requirements.txt

## Dev Server

$ source bin/activate
$ gunicorn --reload wsgi:app
