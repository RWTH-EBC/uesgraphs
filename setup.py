# coding=utf-8
import setuptools

setuptools.setup(name='uesgraphs',
                 version='0.6.1',
                 description='Graphs to describe Urban Energy Systems',
                 url='https://github.com/RWTH-EBC/uesgraphs',
                 author='Marcus Fuchs',
                 author_email='mfuchs@eonerc.rwth-aachen.de',
                 license='MIT License',
                 packages=setuptools.find_packages(),
                 install_requires=['pytest', 'networkx', 'numpy', 'pandas',
                                   'shapely', 'pyproj', 'matplotlib',
                                   'nose', 'pytest-mpl', ],
                 classifiers=("Programming Language :: Python :: 3", ),
                 )

