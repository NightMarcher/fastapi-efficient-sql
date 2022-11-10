from os import path as os_path
import setuptools

import fastapi_esql

current_dir = os_path.abspath(os_path.dirname(__file__))


def read_file(filename):
    with open(os_path.join(current_dir, filename), encoding="utf-8") as f:
        long_description = f.read()
    return long_description


with open("README.md", "r") as f:
    long_description = f.read()


def read_requirements(filename):
    return [
        line.strip() for line in read_file(filename).splitlines()
        if not line.startswith("#")
    ]


setuptools.setup(
    name="fastapi-efficient-sql",
    version=fastapi_esql.__version__,
    author="BryanLee",
    author_email="bryanlee@126.com",
    description="Generate bulk DML SQL and execute them based on tortoise-orm and mysql8.0+, and integrated with fastapi.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NightMarcher/fastapi-efficient-sql",
    packages=setuptools.find_packages(),
    license="MIT",
    keywords=["sql", "fastapi", "tortoise-orm", "mysql8", "bulk-operation"],
    install_requires=read_requirements("requirements.txt"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
)
