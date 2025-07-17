"""
StudySprint DB Package Setup
"""

from setuptools import setup, find_packages
import os

# Read version from _version.py
version = {}
with open("studysprint_db/_version.py") as fp:
    exec(fp.read(), version)

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="studysprint-db",
    version=version["__version__"],
    author="StudySprint Team",
    author_email="dev@studysprint.com",
    description="StudySprint 2.0 Database Models and Migrations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/studysprint/studysprint-db",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "studysprint-db=studysprint_db.cli:main",
            "studysprint-migrate=studysprint_db.cli:migrate_command",
            "studysprint-init-db=studysprint_db.cli:init_command",
        ],
    },
    include_package_data=True,
    package_data={
        "studysprint_db": [
            "alembic.ini",
            "alembic/**/*",
        ],
    },
)
