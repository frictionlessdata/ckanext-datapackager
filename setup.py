# encoding: utf-8

from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
from os import path

version = '1.1.0'

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ckanext-datapackager',
    version=version,
    description="This extension adds importing and exporting of Data Packages to CKAN datasets.",
    long_description=long_description,

    # see http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        "Programming Language :: Python :: 3",
    ],
    keywords='CKAN datapackages FrictionlessData',
    author='Open Knowledge Foundation',
    author_email='info@okfn.org',
    url='https://github.com/ckan/ckanext-datapackager',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.datapackager'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
    ],
    entry_points={
        'ckan.plugins': [
            'datapackager=ckanext.datapackager.plugin:DataPackagerPlugin'
        ],
    }
    ,
)
