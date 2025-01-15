from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aiohttp-pgsessions",
    version="0.1.1",
    author="Christian Houle",
    author_email="christian@meunier8.com",
    description="PostgreSQL session storage for aiohttp",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seoul04/aiohttp-pgsessions",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: aiohttp",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.0.0",
        "aiohttp-session>=2.0.0",
    ],
) 