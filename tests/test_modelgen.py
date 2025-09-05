"""This module tests the model generation of UESModel"""

from __future__ import unicode_literals
import dateutil.parser as dparser
import datetime
from shutil import copytree
import json
import pytest
import os

from uesgraphs.systemmodels import systemmodelheating as smh
from uesgraphs.examples import e11_model_generation_example as exm
from uesgraphs.systemmodels.utilities import *


# @pytest.fixture(scope="module", params=["Ibpsa"])

@pytest.fixture(scope="module", params=["Ibpsa", "Pinola"])
def datadir(tmpdir_factory, request):
    """Fixture for temporary directory creation

    From https://stackoverflow.com/questions/29627341/ , but using
    `tmpdir_factory` because `tmpdir` is only function-scoped.

    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    assert os.path.isdir(test_dir), "No reference directory"
    dir_network = os.path.join(test_dir, request.param)
    dir_tmp = tmpdir_factory.mktemp("data")
    copytree(dir_network, str(dir_tmp), dirs_exist_ok=True)
    return dir_tmp


def test_network_model_open_loop_dt_var(datadir):
    """Writes network model mo-files and compares to previous versions'
    """

    # Make sure files are present
    json_nodes = datadir.join("nodes.json")
    print("datadir =", datadir)
    assert os.path.exists(str(datadir))
    assert os.path.exists(str(json_nodes))

    # Get the network's name from the JSON input
    with open(str(json_nodes), "r") as input_file:
        data_input = json.load(input_file)
        name_network = data_input["meta"]["name"]

    dir_modelgen = str(datadir)
    dir_model = os.path.join(str(datadir), "model")
    if not os.path.exists(dir_model):
        os.mkdir(dir_model)

    exm.model_generation_ibpsa(dir_modelgen, dir_model)
    exm.model_generation_pinola(dir_modelgen, dir_model)

    references = ["open-loop-dT-var"]

    for reference in references:
        dir_ref = os.path.join(str(datadir), "reference-models", reference)
        for filename in os.listdir(dir_ref):
            print(filename)

            file_ref = os.path.join(dir_ref, filename)
            file_created = os.path.join(
                dir_model, filename.replace("_inputs", "").replace(".mo", ""), filename
            )

            with open(file_ref, "r") as ref:
                lines_ref = ref.read().split("\n")
            with open(file_created, "r") as created:
                lines_created = created.read().split("\n")

            for line_ref, line_created in zip(lines_ref, lines_created):
                description = "Model automatically generated with uesgraphs"
                doc = "&nbsp;</i> uesgraphs "
                if (
                    description not in line_ref
                    and doc not in line_ref
                    and "<li><i>" not in line_ref
                    and "StopTime" not in line_ref
                ):
                    assert line_ref == line_created, "Lines not matching"


def test_network_model_t_ground_var(datadir):
    """Writes network model mo-files and compares to previous versions'
    """

    # Make sure files are present
    json_nodes = datadir.join("nodes.json")
    print("datadir =", datadir)
    assert os.path.exists(str(datadir))
    assert os.path.exists(str(json_nodes))

    # Get the network's name from the JSON input
    with open(str(json_nodes), "r") as input_file:
        data_input = json.load(input_file)
        name_network = data_input["meta"]["name"]

    dir_modelgen = str(datadir)
    dir_model = os.path.join(str(datadir), "model")
    if not os.path.exists(dir_model):
        os.mkdir(dir_model)

    exm.model_generation_ibpsa(dir_modelgen, dir_model)
    exm.model_generation_pinola(dir_modelgen, dir_model)

    references = ["t_ground_var"]

    for reference in references:
        dir_ref = os.path.join(str(datadir), "reference-models", reference)
        for filename in os.listdir(dir_ref):
            print(filename)

            file_ref = os.path.join(dir_ref, filename)
            file_created = os.path.join(
                dir_model, filename.replace("_inputs", "").replace(".mo", ""), filename
            )

            with open(file_ref, "r") as ref:
                lines_ref = ref.read().split("\n")
            with open(file_created, "r") as created:
                lines_created = created.read().split("\n")

            for line_ref, line_created in zip(lines_ref, lines_created):
                description = "Model automatically generated with uesgraphs"
                doc = "&nbsp;</i> uesgraphs "
                if (
                    description not in line_ref
                    and doc not in line_ref
                    and "<li><i>" not in line_ref
                    and "StopTime" not in line_ref
                ):
                    assert line_ref == line_created, "Lines not matching"


def test_network_model_low_temp(datadir):
    """Writes network model mo-files and compares to previous versions'
    """

    # Make sure files are present
    json_nodes = datadir.join("nodes.json")
    print("datadir =", datadir)
    assert os.path.exists(str(datadir))
    assert os.path.exists(str(json_nodes))

    # Get the network's name from the JSON input
    with open(str(json_nodes), "r") as input_file:
        data_input = json.load(input_file)
        name_network = data_input["meta"]["name"]

    dir_modelgen = str(datadir)
    dir_model = os.path.join(str(datadir), "model")
    if not os.path.exists(dir_model):
        os.mkdir(dir_model)

    exm.model_generation_ibpsa(dir_modelgen, dir_model)
    exm.model_generation_pinola(dir_modelgen, dir_model)

    references = ["low_temp_network"]

    for reference in references:
        dir_ref = os.path.join(str(datadir), "reference-models", reference)
        for filename in os.listdir(dir_ref):
            print(filename)

            file_ref = os.path.join(dir_ref, filename)
            file_created = os.path.join(
                dir_model, filename.replace("_inputs", "").replace(".mo", ""), filename
            )

            with open(file_ref, "r") as ref:
                lines_ref = ref.read().split("\n")
            with open(file_created, "r") as created:
                lines_created = created.read().split("\n")

            for line_ref, line_created in zip(lines_ref, lines_created):
                description = "Model automatically generated with uesgraphs"
                doc = "&nbsp;</i> uesgraphs "
                if (
                    description not in line_ref
                    and doc not in line_ref
                    and "<li><i>" not in line_ref
                    and "StopTime" not in line_ref
                ):
                    assert line_ref == line_created, "Lines not matching"

def test_doc_string():
    """Test doc-string generation and setter"""
    model = smh.SystemModelHeating()
    
    # Test auto-generated format (simple but robust)
    doc_string = model.doc_string
    assert "Model automatically generated with uesgraphs version" in doc_string
    assert str(datetime.now().year) in doc_string
    
    # Test setter functionality  
    model.doc_string = "a" * 75  # OK
    assert model.doc_string == "a" * 75
    
    model.doc_string = "a" * 76  # Still OK
    assert model.doc_string == "a" * 76
    
    # Test length limit
    with pytest.raises(ValueError):
        model.doc_string = "a" * 77

def test_medium():
    """Test the getter and setter of medium in UESModel
    """
    model = smh.SystemModelHeating()

    assert model.medium == "AixLib.Media.Water"

    model.medium = "AixLib.Media.Water"

    with pytest.raises(ValueError):
        model.medium = "Some medium"
