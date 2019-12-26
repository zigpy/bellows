"""Setup module for bellows"""

from setuptools import find_packages, setup

import bellows

setup(
    name="bellows-homeassistant",
    version=bellows.__version__,
    description="Library implementing EZSP",
    url="http://github.com/zigpy/bellows",
    author="Russell Cloran",
    author_email="rcloran@gmail.com",
    license="GPL-3.0",
    packages=find_packages(exclude=["*.tests"]),
    entry_points={"console_scripts": ["bellows=bellows.cli.main:main"]},
    install_requires=[
        "Click",
        "click-log==0.2.0",
        "pure_pcapy3==1.0.1",
        "pyserial-asyncio",
        "voluptuous",
        "zigpy-homeassistant>=0.12.0",
    ],
    dependency_links=["https://codeload.github.com/rcloran/pure-pcapy-3/zip/master"],
    tests_require=["asynctest", "pytest", "pytest-asyncio"],
)
