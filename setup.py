from distutils.core import setup
from setuptools import find_packages

setup(
    name='Netrunner Console',
    version='0.1',
    description="Terminal based Android: Netrunner deck builder",
    long_description=open('README.md', encoding="utf-8").read(),
    author="Colin Jacobs",
    author_email="colin@coljac.net",
    url="https://github.com/coljac/netrunner-console",
    data_files=[('help', ['help/help.txt'])],
    entry_points={
        'console_scripts': ['netrunner-console=console:main']
    },
    packages=['console', 'console.utils'],
    install_requires=['requests'],
    license='MIT License'
)


