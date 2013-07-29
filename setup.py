from setuptools import setup, find_packages
import tattletale

setup(
    name='tattletale',
    version=tattletale.__version__,
    packages=['tattletale', 'tattletale.api', 'tattletale.api.v1'],
    url='',
    license='Confidential and proprietary; not licensed for distribution',
    author='Joshua "jag" Ginsberg',
    author_email='jag@socialcode.com',
    description='Tattletale is a Python web service for a realtime news feed'
)
