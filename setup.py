# Copyright 2021 Red Hat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from setuptools import find_packages, setup

BASE_PATH = os.path.dirname(__file__)


def get_readme_content():
    with open(
        os.path.join(BASE_PATH, "README.md"), "r", encoding="utf8"
    ) as readme:
        return readme.read()


def get_version():
    with open(
        os.path.join(BASE_PATH, "VERSION"), "r", encoding="utf8"
    ) as version:
        return version.read().strip()


setup(
    name="managedtenants_cli",
    packages=find_packages(),
    version=get_version(),
    author="Red Hat Managed Tenants SRE Team",
    author_email="sd-mt-sre@redhat.com",
    url="https://github.com/mt-sre/managed-tenants-cli",
    description="A CLI tool commonly used by MT-SRE projects at Red Hat",
    long_description=get_readme_content(),
    python_requires=">=3.9",
    license="Apache-2.0",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries",
    ],
    install_requires=[
        "Jinja2>=2.10,<4.0",
        "markupsafe~=2.0.1",
        "PyYAML~=5.4.1",
        "jsonschema~=4.7",
        "requests~=2.23",
        "sretoolbox~=1.3.0",
        "semver~=2.13.0",
        "python-gitlab~=2.6",
        "checksumdir~=1.2",
        "docker ~=5.0.3",
    ],
    entry_points={
        "console_scripts": [
            "managedtenants = managedtenants.cli:main",
            "validate-imageset = managedtenants.cli.validate_imageset:main",
        ]
    },
    include_package_data=True,
)
