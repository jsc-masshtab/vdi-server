from setuptools import setup

setup(
    name='mi',
    packages=['mi'],
    install_requires=[
        'docopt', 'cached-property'
    ],
    entry_points="""
    [console_scripts]
    mi=mi.main:entry_point
    """,
)
