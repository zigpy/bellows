"""Setup module for bellows"""

from setuptools import find_packages, setup

setup(
    name="bellows",
    version="0.2.0",
    description="",
    url="http://github.com/rcloran/bellows",
    author="Russell Cloran",
    author_email="rcloran@gmail.com",
    license="GPL-3.0",
    packages=find_packages(exclude=['*.tests']),
    entry_points={
        'console_scripts': ['bellows=bellows.cli.main:main'],
    },
    install_requires=[
        'Click',
        'click-log',
        'pure_pcapy==1.0.2',
        'pyserial-asyncio',
    ],
    dependency_links=[
        # Unreleased Python 3 branch of pure-pcapy
        'https://bitbucket.org/viraptor/pure-pcapy/get/b19e25020aa90720.zip#egg=pure_pcapy-1.0.2',
    ],
    tests_require=[
        'pytest',
    ],
)
