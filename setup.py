from setuptools import setup

NAME = 'schemagic'
PACKAGES = ['schemagic']
VERSION = '0.3.21'
LICENSE = "LGPL"
DESCRIPTION = 'Define the shape of your data with simple python data structures. Use those data descriptions to validate your application.'
AUTHOR = 'Tyler Tolton'
AUTHOR_EMAIL = 'tjtolton@gmail.com'
URL = 'https://github.com/TJTolton/schemagic'
KEYWORDS = ['schema', 'schemas', 'schemata',
          'validate', 'validation', 'validator'
          'json', 'REST', 'webservice', 'flask', 'POST'
          'agile']

if __name__ == "__main__":
    setup(
        name=NAME,
        description=DESCRIPTION,
        license=LICENSE,
        url=URL,
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        keywords=KEYWORDS,
        packages=PACKAGES,
    )