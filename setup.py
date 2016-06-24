from setuptools import setup
from setuptools.command.test import test as TestCommand
import schemagic
import sys


NAME = schemagic.__name__
PACKAGES = ['schemagic']
VERSION = schemagic.__version__
LICENSE = schemagic.__license__
DESCRIPTION = schemagic.__description__
AUTHOR = schemagic.__author__
AUTHOR_EMAIL = schemagic.__authoremail__
URL = schemagic.__url__
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