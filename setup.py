#!/usr/bin/env python3

"""
Setup Lidl Plus api
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="lidl-plus",
    version="0.2.3",
    author="Andre Basche",
    description="Fetch receipts and more from Lidl Plus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        "GitHub": "https://github.com/Andre0512/lidl-plus",
        "PyPI": "https://pypi.org/project/lidl-plus/",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    platforms="any",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=["requests"],
    extras_require={"auth": ["selenium-wire", "webdriver-manager", "getuseragent", "oic"]},
    entry_points={
        "console_scripts": [
            "lidl-plus = lidlplus.__main__:start",
        ]
    },
)
