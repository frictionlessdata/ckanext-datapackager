Data Packager API Documentation
===============================

The Data Packager allows you edit data packages via a JSON api, creating packages and
files works the same as the CKAN API. For further details of the CKAN API see 
http://docs.ckan.org/en/latest/api/index.html#action-api-reference . The Data Packager
API is an extension on top of the CKAN API, the additional functions are detailed here. 

Example
-------
These examples all use the ckanapi command, for more details see https://github.com/ckan/ckanapi

After creating a package and uploading a csv file from the web interface you
can you can fetch it via the api using::

    $ ckanapi action resource_schema_show resource_id=<resource id>
    {
      "fields": [
      ]
    }

We can add fields to the schema of our csv file using `resource_schema_field_create`::

    $ ckanapi action resource_schema_field_create resource_id=<resource id> name=my-field type=string
    {
      "index": 0,
      "name": "my-field",
      "type": "string"
    }

And set our new field as the primary key::

    $ ckanapi action resource_schema_pkey_create resource_id=<resource id> pkey=my-field  -c tsb.ini
    "my-field"

We can create another field in the schema and set it as a foreign key to another
field in a different csv file as long as it belongs to the same datapackage::

    $ ckanapi action resource_schema_field_create resource_id=<resource id> name=another-field type=string
    {
      "index": 1,
      "name": "another-field",
    }

    $ ckanapi action resource_schema_fkey_create resource_id=<resource id> field=another-field referenced_field='another-field-id' referenced_resource_id=<other resource id> -c tsb.ini
    {
      "fields": [
        {
          "index": 0,
          "name": "my-field",
          "type": "string"
        },
        {
          "index": 1,
          "name": "another-field"
        }
      ],
      "foreignKeys": [
        {
          "fields": "another-field",
          "fkey_uid": "abcdf1234",
          "reference": {
            "_resource_id": "<other resource id>",
            "fields": "another-field-id",
            "resource": "another.csv"
          }
        }
      ],
      "primaryKey": "my-field"
    }

API Reference
=============

Schemas and fields
------------------

.. autofunction:: ckanext.datapackager.logic.action.create.resource_schema_field_create
.. autofunction:: ckanext.datapackager.logic.action.get.resource_schema_field_show
.. autofunction:: ckanext.datapackager.logic.action.get.resource_schema_show
.. autofunction:: ckanext.datapackager.logic.action.update.resource_schema_field_update
.. autofunction:: ckanext.datapackager.logic.action.delete.resource_schema_field_delete

Primary Keys
------------

.. autofunction:: ckanext.datapackager.logic.action.create.resource_schema_pkey_create
.. autofunction:: ckanext.datapackager.logic.action.get.resource_schema_pkey_show
.. autofunction:: ckanext.datapackager.logic.action.update.resource_schema_pkey_update
.. autofunction:: ckanext.datapackager.logic.action.delete.resource_schema_pkey_delete

Foreign Keys
------------

.. autofunction:: ckanext.datapackager.logic.action.create.resource_schema_fkey_create
.. autofunction:: ckanext.datapackager.logic.action.get.resource_schema_fkey_show
.. autofunction:: ckanext.datapackager.logic.action.update.resource_schema_fkey_update
.. autofunction:: ckanext.datapackager.logic.action.delete.resource_schema_fkey_delete

Other
-----

.. autofunction:: ckanext.datapackager.logic.action.get.package_to_tabular_data_format
