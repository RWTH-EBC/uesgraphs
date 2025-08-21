# -*- coding:utf8 -*-
"""
This module contains unit tests for uesgraphs module
"""
import os
import shapely.geometry as sg
import uesgraphs.uesgraph as uesgr
import uesgraphs.systemmodels.systemmodelheating as uesmo
import pytest


@pytest.fixture
def example_model():
    example_model = uesmo.SystemModelHeating()
    return example_model


class Test_uesmodels(object):
    def test_pipe_nodes(self, example_model):
        """Tests the methods to add and remove pipe nodes
        """
        example_model.add_pipe_node(name="test_pipe", position=sg.Point(0, 0))

        assert len(example_model.nodelist_pipe) == 1

        curr_pipe = example_model.nodes_by_name["test_pipe"]
        example_model.remove_pipe_node(curr_pipe)

        assert len(example_model.nodelist_pipe) == 0

    def test_time(self, example_model):
        """Tests the time handling in uesmodels
        """
        example_model.stop_time = 3600
        example_model.timestep = 900

        msg = "Time vector is not created correctly: {}"
        assert example_model.time == [0, 900, 1800, 2700, 3600], msg.format(
            example_model.time
        )
