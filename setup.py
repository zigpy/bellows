"""Setup module for bellows"""

from setuptools import find_packages, setup

setup(
    name="bellows",
    version="0.1",
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
        'pyserial-asyncio',
    ],
    tests_require=[
        'pytest',
    ],
)
