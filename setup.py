import os
import setuptools

setuptools.setup(
    name = "recursive radon tool",
    version = "0.1",
    author = "Brumo Maximilian Voss",
    author_email = "bruno.m.voss@gmail.com",
    description = ("get radon info"),
    packages=setuptools.find_packages(),
    #package_dir={'': 'foldername'},
    license = "MIT",
    package_data={'radon_tool': ['templates/*.html']},
    entry_points={
    "console_scripts": [
        "recursive_radon_tool = radon_tool.main:main",
    ]
    }
)
