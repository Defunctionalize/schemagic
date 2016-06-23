from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


NAME = 'schemagic'
PACKAGES = ['schemagic']
VERSION = '0.3.24'
LICENSE = "LGPL"
DESCRIPTION = 'Define the shape of your data with simple python data structures. Use those data descriptions to validate your application.'
AUTHOR = 'Tyler Tolton'
AUTHOR_EMAIL = 'tjtolton@gmail.com'
URL = 'https://github.com/TJTolton/schemagic'
KEYWORDS = ['schema', 'schemas', 'schemata',
          'validate', 'validation', 'validator'
          'json', 'REST', 'webservice', 'flask', 'POST'
          'agile']


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)

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
        tests_require=['tox'],
        cmdclass={'test': Tox},
    )