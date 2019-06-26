from setuptools import setup
import re
import ast
import platform

install_requirements = [
    "click >= 4.1",
    "prompt_toolkit >= 2.0.6",
    "Pygments >= 2.0",
    "cli_helpers[styles] >= 1.2.0",
    "elasticsearch==7.0.1",
    "pyfiglet==0.8.post1",
]

_version_re = re.compile(r"__version__\s+=\s+(.*)")

with open("escli/__init__.py", "rb") as f:
    version = str(
        ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1))
    )

# setproctitle is used to mask the password when running `ps` in command line.
# But this is not necessary in Windows since the password is never shown in the
# task manager. Also setproctitle is a hard dependency to install in Windows,
# so we'll only install it if we're not in Windows.
if platform.system() != "Windows" and not platform.system().startswith("CYGWIN"):
    install_requirements.append("setproctitle >= 1.1.9")

description = "CLI for Elasticsearch Open Distro SQL. With auto-completion and syntax highlighting."

setup(
    name="escli",
    author="AES",
    # author_email="",
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