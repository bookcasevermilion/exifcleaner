from setuptools import setup, find_packages
setup(
    name="exifcleaner",
    version="0.1",
    packages=["exifcleaner"],
    install_requires=['webob', 'rq', 'englids', 'rq-scheduler', 'passlib', 'udatetime']
)