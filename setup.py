from setuptools import setup, find_packages


with open('README') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pyremote',
    version='0.1.0',
    description='Client-server library for remote python interaction',
    long_description=readme,
    author='Ted Meyer',
    author_email='tmathmeyer@gmail.com',
    url='https://github.com/tmathmeyer/pyremote',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)