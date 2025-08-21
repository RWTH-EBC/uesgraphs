"""""Write example district heating cooling network to JSON file."""

import os
import uesgraphs as ug

from uesgraphs.examples import e1_readme_example as e1
from uesgraphs.examples import e2_simple_dhc_example as e2



def main():

    to_json()

def to_json():
    """Demos the output of an uesgraph to JSON"""

    # Generate workspace directory using the make_workspace function.

    workspace = e1.workspace_example("e4")
    
    # The simple_dhc_model function is runned to create an example district
    # heating cooling network.

    example_district = e2.simple_dhc_model()

    # The district heating cooling network is saved to a JSON file using the
    # example_district.to_json function from 'uesgraph.py'.

    fil_path_1 = example_district.to_json(path=workspace, name=None)

    # create_subgraphs is used to generate a list of the subgraph 'heating'.

    heating_network = example_district.create_subgraphs("heating")["default"]

    ug.Visuals(heating_network).show_network(
        save_as=os.path.join(workspace, "e4_heating_network.png"), scaling_factor=30
    )

    ug.Visuals(example_district).show_network(
        save_as=os.path.join(workspace, "e4_example_district.png"), scaling_factor=30
    )
    # The subgraph heating is saved to a JSON file.

    fil_path_2 = heating_network.to_json(
        path=os.path.abspath(os.path.join(workspace, "only_heating.json")),
        name="only_heating",
        prettyprint=True,
    )
    print(f"JSON Files: {fil_path_1} and {fil_path_2}")


    return fil_path_1, fil_path_2


# Main function
if __name__ == "__main__":
    print("*** Generating simple dhc model ***")
    print("*** Saving uesgraphs to json ***")
    main()
    print("*** Done ***")
