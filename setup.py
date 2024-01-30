# coding=utf-8
import setuptools

setuptools.setup(
    name="uesgraphs",
    version="0.6.2",
    description="Graphs to describe Urban Energy Systems",
    url="https://github.com/RWTH-EBC/uesgraphs",
    author="Marcus Fuchs",
    author_email="mfuchs@eonerc.rwth-aachen.de",
    license="MIT License",
    packages=setuptools.find_packages(),
    install_requires=[
        "pytest",
        "networkx>=2.1",
        "numpy",
        "pandas",
        "shapely",
        "pyproj",
        "matplotlib",
        "nose",
        "pytest-mpl",
        "scikit-learn",
        "mako",
    ],
    classifiers=("Programming Language :: Python :: 3",),
)
