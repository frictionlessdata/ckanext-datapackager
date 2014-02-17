This is a CKAN extension that contains the CKAN theme and plugins for the B2
Metadata Generator.

To install the latest development version, first
[install CKAN 2.2 from source](http://docs.ckan.org/en/latest/maintaining/installing/install-from-source.html)
and then (assuming you installed CKAN in the default location):

    cd /usr/lib/ckan/default/src/ckan
    git checkout b2  # ckanext-b2 currently requires this custom CKAN branch.
    pip install -e 'git+https://github.com/ckan/ckanext-b2.git#egg=ckanext-b2'
    pip install -r ../ckanext-b2/requirements.txt

(The `pip install -r` command installs [pandas](http://pandas.pydata.org/)
which requires a lot of compiling, there may be some packages that need to be
`apt-get install`ed for this to work.)

Then add `b2` to the `ckan.plugins` setting in your CKAN config file, and
restart your web server.
