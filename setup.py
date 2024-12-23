#!/usr/bin/env python3
from setuptools import setup, find_packages

this_dir = Path(__file__).parent
module_dir = this_dir / "piper"

requirements = []
requirements_path = this_dir / "requirements.txt"
if requirements_path.is_file():
    with open(requirements_path, "r", encoding="utf-8") as requirements_file:
        requirements = requirements_file.read().splitlines()

data_files = [module_dir / "voices.json"]

# -----------------------------------------------------------------------------

setup(
    name="piper-tts",
    version="v3.1.2",
    url="https://github.com/Amberg/IMS-Toucan",
    author="Flux9665",
    license="MIT",
    packages=setuptools.find_packages(),
    packages=find_packages(),  # Findet alle Python-Module (Ordner mit `__init__.py`)
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="IMS-Toucan - fork",
)