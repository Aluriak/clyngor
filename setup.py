import os
from setuptools   import setup, find_packages
from pip.req      import parse_requirements
from pip.download import PipSession


# access to the file at the package top level (like README)
def path_to(filename):
    return os.path.join(os.path.dirname(__file__), filename)
# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements(path_to('requirements.txt'), session=PipSession())
reqs = [str(ir.req) for ir in install_reqs]


setup(
    name = 'clyngor',
    version = '0.0.16',
    packages = find_packages(),
    include_package_data = True,  # read the MANIFEST.in file
    install_requires = reqs,

    author = "lucas bourneuf",
    author_email = "lucas.bourneuf@laposte.net",
    description = "Python wrapper around Clingo/Answer Set Programming",
    long_description = open(path_to('README.mkd')).read(),
    keywords = "ASP clingo wrapper",
    url = "https://github.com/aluriak/clyngor",

    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: ASP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
