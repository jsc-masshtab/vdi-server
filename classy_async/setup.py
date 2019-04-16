
from setuptools import setup

classifiers = [
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
]

with open("README.md", "r") as fp:
    README = fp.read()

setup(name="classy_async",
      version="0.1.0",
      author="Vitalii Abetkin",
      author_email="v.abetkin@mashtab.ru",
      packages=['classy_async'],
      description="utils for async tasks",
      long_description=README,
      license="MIT",
      classifiers=classifiers)
