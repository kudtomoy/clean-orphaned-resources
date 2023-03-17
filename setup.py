from setuptools import setup, find_packages


def _requires_from_file(filename):
    return open(filename).read().splitlines()


setup(
    name="clean_orphaned_resources",
    version="0.3.0",
    packages=find_packages(),
    install_requires=_requires_from_file("requirements.txt"),
    entry_points={
        "console_scripts": [
            "clean-orphaned-resources=clean_orphaned_resources.app:main",
        ],
    },
)
