
from setuptools import setup

g_tasks_classifiers = [
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
]

with open("README.md", "r") as fp:
    README = fp.read()

setup(name="g_tasks",
      version="0.1.0",
      author="Vitalii Abetkin",
      author_email="abvit89s@gmail.com",
      url="http://github.com/abetkin/g_tasks",
      py_modules=["g_tasks"],
      description="utils for async tasks",
      long_description=README,
      license="MIT",
      classifiers=g_tasks_classifiers
      )
