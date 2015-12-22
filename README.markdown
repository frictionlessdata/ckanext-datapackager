[![Build Status](https://travis-ci.org/ckan/ckanext-datapackager.png)](https://travis-ci.org/ckan/ckanext-datapackager) [![Coverage Status](https://coveralls.io/repos/ckan/ckanext-datapackager/badge.png?branch=master)](https://coveralls.io/r/ckan/ckanext-datapackager?branch=master)

# CKAN Data Packager

This extension adds importing and exporting of [Data Packages][data-packages] to [CKAN][ckan] datasets.

## Requirements

* CKAN 2.4

## Installing

To install `ckanext-datapackager` into a CKAN instance, do:

1. If you're using a virtual environment for CKAN, activate it doing, for example:

    ```
    source /usr/lib/ckan/default/bin/activate
    ```
    
2. Install the `ckanext-datapackager` extension using pip:

    ```
    pip install ckanext-datapackager
    ```
    
3. Add `datapackager` to the `ckan.plugins` setting in your CKAN config file;
4. Restart CKAN.

## Using

### Web Interface

#### Importing

![Importing Data Package](doc/images/ckanext-datapackager-import-demo.gif)

## Developing ckanext-datapackager

### Running tests

You'll need to install the dev requirements to run the tests:

    pip install -r dev-requirements.txt

To run the tests:

    nosetests --nologcapture --ckan --with-pylons=test.ini

Note that ckanext-datapackager's `test.ini` file assumes that the relative path from it
to CKAN's `test-core.ini` file is `../ckan/test-core.ini`, i.e. that you have
CKAN and ckanext-datapackager installed next to each other in the same directory. This
would normally be the case if you've done development installs of CKAN and
ckanext-datapackager.

## Where is the old Open Knowledge's Data Packager?

The [Open Knowledge Data Packager](http://datapackager.okfn.org) is a web app for quickly creating and
publishing [Tabular Data Packages](http://dataprotocols.org/tabular-data-package/).
For more information, see the [blog post on CKAN.org](http://ckan.org/2014/06/09/the-open-knowledge-data-packager/)
and the [about page on datapackager.okfn.org](http://datapackager.okfn.org/about).

[ckan]: http://ckan.org
[data-packages]: http://dataprotocols.org/data-packages/
