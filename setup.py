from setuptools import setup, find_packages

setup(
    name="modeling_tool",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pyyaml>=6.0,<7.0",
    ],
    python_requires=">=3.7",
)
