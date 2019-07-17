import re
import ast

from setuptools import setup, find_packages

install_requirements = [
    "click >= 4.1",
    "prompt_toolkit >= 2.0.6",
    "Pygments >= 2.0",
    "cli_helpers[styles] >= 1.2.0",
    "elasticsearch == 7.0.1",
    "pyfiglet == 0.8.post1",
    "boto3 >= 1.9.181",
    "requests-aws4auth == 0.9"
]

_version_re = re.compile(r"__version__\s+=\s+(.*)")

with open("escli/__init__.py", "rb") as f:
    version = str(
        ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1))
    )

description = "CLI for Elasticsearch Open Distro SQL. " \
              "With auto-completion and syntax highlighting."

setup(
    name="escli",
    author="Zhongnan",
    author_email="zhongnan.su@outlook.com",
    version=version,
    license="Apache 2.0",
    url="https://opendistro.github.io/for-elasticsearch-docs/",
    packages=find_packages(),
    package_data={"escli": ["esclirc", "esliterals/esliterals.json"]},
    description=description,
    install_requires=install_requirements,
    entry_points="""
        [console_scripts]
        escli=escli.main:cli
    """,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: SQL",
        "Topic :: Database",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
