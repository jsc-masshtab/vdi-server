
from setuptools import setup


with open("README.md", "r") as fp:
    README = fp.read()

setup(name="agnostic",
      version="0.1.0",
      author="Vitalii Abetkin",
      author_email="v.abetkin@mashtab.org",
      py_modules=["settings", "db"],
      description="Vdi agnostic",
      )
