from setuptools import setup, find_packages

setup(
    name='vdi',
    packages=find_packages(),
    entry_points="""
    [console_scripts]
    vdi=vdi.main:main
    """,
)
