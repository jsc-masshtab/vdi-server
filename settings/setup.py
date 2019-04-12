
from setuptools import setup


with open("README.md", "r") as fp:
    README = fp.read()

setup(name="settings",
      version="0.1.0",
      author="Vitalii Abetkin",
      author_email="v.abetkin@mashtab.org",
      py_modules=["settings"],
      description="Vdi settings",
      )
