from setuptools import setup, find_packages

setup(
    name="sqlmask",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlparse>=0.4.4",
    ],
    python_requires=">=3.7",
    author="Nathaniel Larson",
    description="A tool for obfuscating SQL statements while preserving structure",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
