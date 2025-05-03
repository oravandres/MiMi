"""Setup script for the MiMi package."""

from setuptools import setup, find_packages

setup(
    name="mimi",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "fastapi>=0.100.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.13",
        "langchain-core>=0.1.15",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mimi=mimi.__main__:main",
        ],
    },
    python_requires=">=3.10",
    author="MiMi Developers",
    author_email="",
    description="AI Tool for running Multi Agent Multi Model Projects",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 