from setuptools import setup
import re
import ast

# TODO: Update dependency list
# for test purpose
install_requirements = [
    "click >= 4.1",
    "prompt_toolkit >= 2.0.6",
    "Pygments >= 2.0",
    "cli_helpers[styles] >= 1.2.0",
    "elasticsearch==7.0.1",
    "pyfiglet==0.8.post1",
    "boto3==1.9.181",
    "requests-aws4auth==0.9"
]

_version_re = re.compile(r"__version__\s+=\s+(.*)")

with open("escli/__init__.py", "rb") as f:
    version = str(
        ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1))
    )

description = "CLI for Elasticsearch Open Distro SQL. With auto-completion and syntax highlighting."

setup(
    name="escli",
    author="AES",
    author_email="zhongnan.su@outlook.com",
    version=version,
    license="BSD",
    # url="http://pgcli.com",
    # packages=find_packages(),
    # package_data={"pgcli": ["pgclirc", "packages/pgliterals/pgliterals.json"]},
    description=description,
    # long_description=open("README.rst").read(),
    install_requires=install_requirements,
    # extras_require={"keyring": ["keyring >= 12.2.0"]},
    entry_points="""
        [console_scripts]
        escli=escli.main:cli
    """
)