from setuptools import setup

setup(
    setup_requires=['d2to1'],
    d2to1=True,
    test_suite="nose.collector",
)
