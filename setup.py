# Uses setuptools to package this project. Almost all variables are parsed from pyproject.toml.
# Also can download codepacks (such as framework) into the project.

from pathlib import Path
from setuptools import setup
from setuptools import find_packages
import toml
import re
from os import path, mkdir
import shutil
from urllib import request
from zipfile import ZipFile


def normalize(name: str) -> str:
    """Simple function to normalize and pythonize names"""
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_pyproject(pyproject_path: str) -> str:
    """Opens a pyproject.toml at 'pyproject_path' and returns the contents as a dictionary."""
    pp = Path(pyproject_path)
    return toml.load(pp.open())


def create_dirs(dirs: list[str]) -> None:
    """Creates the directories in dirs"""
    for dir in dirs:
        if not path.exists(dir):
            mkdir(dir)


def install_codepacks(bem_shelf: dict[str, str]) -> None:
    """Consumes a dictionary of codepack names and the url to gather them from.
    Downloads from the url and extracts the codepack to the top level of the project.
    Note that this is in development and currently only works with bem-shelf-master."""
    for codepack, url in bem_shelf.items():
        request.urlretrieve(url, shelf_name)
        with ZipFile(shelf_name, "r") as zip_ref:
            zip_ref.extractall(".tmp")
        if src:
            cpack_path = Path(src + "/" + project_name + "/" + codepack)
        else:
            cpack_path = Path(project_name + "/" + codepack)
        shutil.rmtree(cpack_path, ignore_errors=True)
        shutil.copytree(".tmp/bash-environment-shelf-master/codepacks/" + codepack, cpack_path)


def parse_extras_require(pyproject: dict[str, dict[str, list[str]]]) -> dict[str, list[str]]:
    """parses optional dependencies from the dictionary parse of a pyproject.toml file.
    Returns a dictionary in the same format but with recursive references interpretted.
    i.e., project[test] => pytest, pytest-cov"""
    extra_requirements = pyproject["project"]["optional-dependencies"]
    recursive_re = re.compile(project_name + r"\[.*\]")
    extra_re = re.compile(r"(?<=\[).*(?=\])")

    def parse_extra(reqs: list[str]) -> list[str]:
        """parses list of requirements and interprets recursive (e.g., project[test]) requirements"""
        parsed_reqs = []
        for req in reqs:
            if recursive_re.fullmatch(req):
                extra_name = extra_re.search(req).group(0)
                parsed_reqs += [expanded_rq for expanded_rq in parse_extra(extra_requirements[extra_name])]
            else:
                parsed_reqs.append(req)
        return parsed_reqs

    for extra, reqs in extra_requirements.items():
        extra_requirements[extra] = parse_extra(reqs)
    return extra_requirements


# VARS
pyproject_path: str = "pyproject.toml"
pyproject: dict = _parse_pyproject(pyproject_path)
project_name: str = normalize(pyproject["project"]["name"])
src: str = pyproject["tool"]["bem"]["source-directory"]
dirs: list[str] = [".tmp", ".tmp/download", ".tmp/logs"]
shelf_name: str = ".tmp/download/bash-environment-shelf.zip"


# BEM setup and framework import
create_dirs(dirs)
install_codepacks(pyproject.get("tool", {}).get("bem", {}).get("codepack", {}))

# setuptools setup
setup_kwargs: dict = {}
if not src:
    setup_kwargs["packages"] = [project_name]
else:
    setup_kwargs["packages"] = find_packages(where=src)
    setup_kwargs["package_dir"] = {"": src}

setup(
    name=project_name,
    version=pyproject["project"]["version"],
    description=pyproject["project"]["description"],
    url=pyproject["project"]["urls"]["repository"],
    author=[auth for auth in pyproject["project"]["authors"]],
    author_email=[auth for auth in pyproject["project"]["authors"]],
    license_files=pyproject["project"]["license"],
    zip_safe=False,
    include_package_data=True,
    python_requires=pyproject["project"]["requires-python"],
    install_requires=pyproject["tool"]["bem"].get("pins") + pyproject["project"]["dependencies"],
    extras_require=parse_extras_require(pyproject),
    entry_points="""
        [console_scripts]
    """
    + f"{project_name}={project_name}.__main__:main",
    **setup_kwargs,
)
