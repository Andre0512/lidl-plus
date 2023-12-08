#!/usr/bin/env python3

"""
Setup Lidl Plus api
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="lidl-plus",
    version="0.3.4",
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
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    platforms="any",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.1",
    ],
    extras_require={
        "auth": [
            "getuseragent>=0.0.7",
            "oic>=1.4.0",
            "selenium-wire>=5.1.0",
            "webdriver-manager>=3.8.5",
        ]
    },
    entry_points={
        "console_scripts": [
            "lidl-plus = lidlplus.__main__:start",
        ]
    },
)
