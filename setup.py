from setuptools import setup

setup(
    name="icd9cms",
    description='A utility for searching across the full icd9cms (2015) diagnosis hierarchy',
    version='0.1',
    author_email='thomas.searle@kcl.ac.uk',
    author='Tom Searle',
    packages=['icd9cms'],
    install_requires=[
        'pandas',
        'bs4',
        'requests',
    ],
    include_package_data=True
)
