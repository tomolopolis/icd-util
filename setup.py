from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="icd9cms",
    description='A utility for searching across the full icd9cms (2015) diagnosis hierarchy',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomolopolis/icd-util",
    version='0.2.0',
    author_email='thomas.searle@kcl.ac.uk',
    author='Tom Searle',
    packages=['icd9cms'],
    install_requires=[
        'pandas',
        'bs4',
        'requests',
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
