#!/usr/bin/env python3
"""
Setup script for EasyRoutes SMS Tool
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    requirements = []
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove version constraints for setup.py
                package = line.split(">=")[0].split("==")[0].split("~=")[0]
                requirements.append(package)
    return requirements

setup(
    name="easyroutes-sms-tool",
    version="1.0.0",
    author="Manus AI",
    author_email="admin@easyroutes-sms-tool.local",
    description="A tool to send SMS notifications to incomplete EasyRoutes delivery stops",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/easyroutes-sms-tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-asyncio>=0.18.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "isort>=5.10.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "easyroutes-sms=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
    },
    zip_safe=False,
    keywords="easyroutes sms twilio delivery notifications api automation",
    project_urls={
        "Bug Reports": "https://github.com/your-org/easyroutes-sms-tool/issues",
        "Source": "https://github.com/your-org/easyroutes-sms-tool",
        "Documentation": "https://github.com/your-org/easyroutes-sms-tool/blob/main/README.md",
    },
)

