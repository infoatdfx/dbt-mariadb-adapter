#!/usr/bin/env python
import os
import sys

# require python 3.13 or newer
if sys.version_info < (3, 13):
    print("Error: dbt-mariadb does not support this version of Python.")
    print("Please upgrade to Python 3.13 or higher.")
    sys.exit(1)


# require version of setuptools that supports find_namespace_packages
from setuptools import setup

try:
    from setuptools import find_namespace_packages
except ImportError:
    # the user has a downlevel version of setuptools.
    print("Error: dbt requires setuptools v40.1.0 or higher.")
    print('Please upgrade setuptools with "pip install --upgrade setuptools" and try again')
    sys.exit(1)


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


def _get_package_version():
    version_path = os.path.join(this_directory, "dbt", "adapters", "mariadb", "__version__.py")
    namespace: dict = {}
    with open(version_path) as f:
        exec(f.read(), namespace)
    return namespace["version"]


package_name = "dbt-mariadb"
package_version = _get_package_version()
description = "A dbt adapter for MariaDB 11.4+"

setup(
    name=package_name,
    version=package_version,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/infoatdfx/dbt-mariadb-adapter",
    packages=find_namespace_packages(include=["dbt", "dbt.*"]),
    include_package_data=True,
    install_requires=[
        "dbt-core>=1.11.0,<2.0.0",
        "dbt-adapters>=1.22.0,<2.0.0",
        "dbt-common>=1.37.0,<2.0.0",
        "mysql-connector-python>=9.0.0",
    ],
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.13",
)
