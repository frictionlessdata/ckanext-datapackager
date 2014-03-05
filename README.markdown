[![Build Status](https://travis-ci.org/ckan/ckanext-b2.png?branch=travis)](https://travis-ci.org/ckan/ckanext-b2) [![Coverage Status](https://coveralls.io/repos/ckan/ckanext-b2/badge.png?branch=master)](https://coveralls.io/r/ckan/ckanext-b2?branch=master)

This is a CKAN extension that contains the CKAN theme and plugins for the B2
Metadata Generator.

To install the latest development version on Ubuntu 12.04, first
[install CKAN 2.2 from source](http://docs.ckan.org/en/ckan-2.2/install-from-source.html)
and then (assuming you installed CKAN in the default location):

    sudo apt-get install build-essential  # Install packages needed to build ckanext-b2
    . /usr/lib/ckan/default/bin/activate  # Activate your CKAN virtualenv
    cd /usr/lib/ckan/default/src/ckan
    git checkout b2  # ckanext-b2 currently requires this custom CKAN branch
    pip install -e 'git+https://github.com/ckan/ckanext-b2.git#egg=ckanext-b2'
    pip install -r ../ckanext-b2/requirements.txt

The final `pip install -r` command may take a while to run, because it installs
[pandas](http://pandas.pydata.org/) which requires a lot of compiling.

Then add `b2` to the `ckan.plugins` setting in your CKAN config file, and
restart your web server.


Tests
-----

You'll need to install the dev requirements to run the tests:

    pip install -r dev-requirements.txt

To run the tests:

    nosetests --nologcapture --ckan --with-pylons=test.ini

Note that ckanext-b2's `test.ini` file assumes that the relative path from it
to CKAN's `test-core.ini` file is `../ckan/test-core.ini`, i.e. that you have
CKAN and ckanext-b2 installed next to each other in the same directory. This
would normally be the case if you've done development installs of CKAN and
ckanext-b2.


### Coverage

To run the tests with test coverage reporting, first install `coverage` in your
virtualenv:

    pip install coverage

Then run nosetests like this from the top-level `ckanext-b2` directory:

    nosetests --nologcapture --ckan --with-pylons=test.ini --with-coverage --cover-package=ckanext.b2 --cover-inclusive --cover-erase .

To get a nice, HTML-formatted coverage report in `cover/index.html` add the
`--cover-html` option.
