from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="print_fortran_routines",
    version="0.0.1",
    author="E. Farrell",
    author_email="efarrel4@tcd.ie",
    description="Prints names of subroutines in Fortran when they are called",
    long_description_content_type="text/markdown",
    url="https://github.com/onfarrell/sampleproject",
    packages=['print_fortran_routines'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
