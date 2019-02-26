
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

setup(name="typed_contextmanager",
      version="0.1.0",
      author="Vitalii Abetkin",
      author_email="abvit89s@gmail.com",
      url="http://github.com/abetkin/typed_contextmanager",
      py_modules=["typed_contextmanager"],
      description="using types for API",
      long_description=README,
      license="MIT",
      classifiers=classifiers
      )
