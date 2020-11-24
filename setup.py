#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['numpy', 'python-dateutil', 'pandas']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', 'ddt']

setup(
    author="Jeandet Alexis",
    author_email='alexis.jeandet@member.fsf.org',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="An HAPI client POC written in python.",
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='hapi_client_poc',
    name='hapi_client_poc',
    packages=find_packages(include=['hapi_client_poc', 'hapi_client_poc.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/jeandet/hapi_client_poc',
    version='0.1.0',
    zip_safe=False,
)
