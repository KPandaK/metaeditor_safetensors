#!/usr/bin/env python3
"""
Setup for metaeditor_safetensors
Simple pip-based package setup for multiple distribution methods
"""

from setuptools import setup, find_packages

setup(
    name="metaeditor_safetensors",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description="Metadata editor for safetensors files",
    author="KPandaK",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "Pillow>=10.3.0",
        "tkcalendar>=1.6.1",
    ],
    python_requires=">=3.10",
    entry_points={
        'console_scripts': [
            'metaeditor-safetensors=metaeditor_safetensors.main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
