from setuptools import setup, find_packages

setup(
    name="giantt-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "giantt=giantt.cli:cli",
        ],
    },
    python_requires=">=3.7",
)