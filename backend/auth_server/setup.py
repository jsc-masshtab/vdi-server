from setuptools import setup

setup(
    name='sanic_server',
    py_modules=['main'],
    entry_points="""
    [console_scripts]
    sanic_server=main:entry_point
    """,
)