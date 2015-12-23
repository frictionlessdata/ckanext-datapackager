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

1. Visit the Dataset list page (e.g. `http://your-ckan-address.com/dataset`)
2. Click on `Import Data Package` button;
3. Upload or link to a Data Package JSON or ZIP file;
  * Depending on your CKAN configuration, you might also need to define
    the dataset's organization and visibility here.
4. Review the created dataset.

#### Exporting

![Exporting CKAN Dataset as Data Package](doc/images/ckanext-datapackager-export-link.jpg)

1. Go to the dataset's page;
2. Click on `Download Data Package` button.

### API

Read the docstrings inside the files at [ckanext/datapackager/logic/action](ckanext/datapackager/logic/action)

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

The [Open Knowledge Data Packager](http://datapackager.okfn.org) was written for
an old CKAN version (2.2), and is now deprecated. This extension implements
parts of its functionality and improves them, supporting the current CKAN
version (2.4).

If you still need the old Data Packager, checkout this repository's commit
[57cff1f](https://github.com/ckan/ckanext-datapackager/commit/57cff1f5112504091891195a097433579275f968).

[ckan]: http://ckan.org
[data-packages]: http://dataprotocols.org/data-packages/
