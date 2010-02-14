from setuptools import setup, find_packages

setup(
    name = "routez",
    version = "1.0",
    url = 'http://github.com/wlach/routez',
    description = "Routez",
    author = 'William Lachance',
    packages = find_packages('.'),
    package_dir = {'': '.'},
    install_requires = ['setuptools'],
)
