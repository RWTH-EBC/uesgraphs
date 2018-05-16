# coding=utf-8
import setuptools

setuptools.setup(name='uesgraphs',
                 version='0.5.2',
                 description='Graphs to describe Urban Energy Systems',
                 url='https://github.com/RWTH-EBC/uesgraphs',
                 author='Marcus Fuchs',
                 author_email='mfuchs@eonerc.rwth-aachen.de',
                 license='Will be added soon',
                 packages=['uesgraphs'],
                 install_requires=['pytest', 'networkx', 'numpy', 'pandas',
                                   'shapely', 'pyproj', 'matplotlib',
                                   'nose', 'pytest-mpl',])
