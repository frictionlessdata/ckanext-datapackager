#!/bin/sh -e

# Drop Travis' postgres cluster if we're building using a different pg version.
TRAVIS_PGVERSION='9.1'
if [ $PGVERSION != $TRAVIS_PGVERSION ]
then
  sudo -u postgres pg_dropcluster --stop $TRAVIS_PGVERSION main
  # Make psql use $PGVERSION
  export PGCLUSTER=$PGVERSION/main
fi

# Force Postgres 8.4 to use port 5432.
if [ $PGVERSION == '8.4' ]
then
  sudo sed -i -e 's/port = 5433/port = 5432/g' /etc/postgresql/8.4/main/postgresql.conf
fi

sudo service postgresql restart

# Install the packages that CKAN requires.
sudo apt-get update -qq
sudo apt-get install postgresql-$PGVERSION solr-jetty libcommons-fileupload-java:amd64=1.2.2-1

# Install CKAN and its Python dependencies.
git clone https://github.com/ckan/ckan
cd ckan
git checkout b2
python setup.py develop
pip install -r requirements.txt --use-mirrors

# Create the PostgreSQL database and users.
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

# Configure Solr.
echo "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nJAVA_HOME=$JAVA_HOME" | sudo tee /etc/default/jetty
sudo cp ckan/config/solr/schema.xml /etc/solr/conf/schema.xml
sudo service jetty restart

# Initialise the database.
paster db init -c test-core.ini

# Install ckanext-b2 and its requirements.
python setup.py develop
pip install -r dev-requirements.txt
