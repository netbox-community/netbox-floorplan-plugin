import codecs
import os.path

from setuptools import find_packages, setup


with open("README.md", "r") as fh:
    long_description = fh.read()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name="netbox-floorplan-plugin",
    version=get_version('netbox_floorplan/version.py'),
    author="Tony Nealon",
    author_email="tony@worksystems.co.nz",
    description="Netbox Plugin to support graphical floorplans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/netbox-community/netbox-floorplan-plugin.git",
    license="LGPLv3+",
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    min_version="4.3.0",
    max_version="4.3.99"
)
