import os
import csv
from uesgraphs import UESGraph
import json




# NOTE: This version includes node sorting functionality
# Changes made (2026-01-28):
# - Added nodes_to_write list to collect all node dictionaries
# - Changed all writer_nodes.writerow() calls to append to nodes_to_write
# - Added sorting by node_index in ascending order before writing
# - Nodes are now written in order after collection instead of being written immediately


def create_demand_template(substation_file):
    """
    Generate a demand template CSV from substations.csv.
    
    Creates a CSV with first row: "time" in first column, then all 
    substation_index values in subsequent columns (one per column).
    Saves as demand_template.csv in the same directory as input file.
    
    Parameters
    ----------
    substation_file : str
        Path to the substations.csv file (e.g., 'output/heat_substations.csv')
    """
    import pandas as pd
    import os
    
    # Read substations file
    df = pd.read_csv(substation_file, delimiter=';')
    
    # Extract substation indices
    substation_indices = df['substation_index'].tolist()
    
    # Create header: ['time', 'substation1', 'substation2', ...]
    header = ['Time'] + [str(idx) for idx in substation_indices]
    
    # Get directory of input file
    output_dir = os.path.dirname(substation_file)
    output_path = os.path.join(output_dir, 'z_demand_template.csv')
    
    # Write CSV with only header (no data rows)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(header)
    
    print(f"Demand template created: {output_path}")



# optional: enable template here 
def UESgraph_to_HNScsv(graph, save_path, pressure=300000, pressure2=300000, diamteter=0.1, rough=0.0002, thickness_insulation=0.04, heat_cond=0.026, t_set_sec=333.15, delta_t_prim=10, delta_t_sec=10, template=False):
    """Convert UESGraph to HNS CSV format and save to specified path.

    Parameters
    ----------
    graph : UESGraph
        The UESGraph object to convert.
    save_path : str
        The directory path where the CSV files will be saved.
    """
    # Ensure the save path exists
    os.makedirs(save_path, exist_ok=True)


    ########## 1 Export edges (pipelines), nodes, EBU, substation files
    edges_file = os.path.join(save_path, 'heat_pipelines.csv')
    substations_file = os.path.join(save_path, 'heat_substations.csv')
    nodes_file = os.path.join(save_path, 'heat_nodes.csv')
    EBU_file = os.path.join(save_path, 'heat_energybalancingunit.csv')

    pipelines_fields = ['pipeline_index', 'inlet_index', 'outlet_index','diameter_m', 'length_m', 'roughness_m', 'thickness_insulation_m', 'heat_conductivity_insulation', 'pipe_mode', 'drawing_pipe_id']
    nodes_fields = ['node_index', 'pressure_pa', 'altitude_m', 'node_type', 'node_mode', "node_id"]
    EBU_fields = ['ebu_index', 'inlet_index', 'outlet_index', "ebu_name"]
    subst_fields = ['substation_index', 'inlet_index', 'outlet_index', 'T_set_sec', 'delta_T_sec', 'delta_T_pri', 'heat_exchange', 'cooling_exchange', 'substation name']


    len_nodes= len(graph.nodes)
    len_pipes= len(graph.edges)
    print( "nr of nodes & edges: ", str(len_nodes) ," & ", str(len_pipes))
    node_id_index_dict={}


    # Write all files in a single context manager to avoid re-opening multiple times
    with open(edges_file, 'w', newline='') as ef, \
         open(nodes_file, 'w', newline='') as nf, \
         open(EBU_file, 'w', newline='') as bf, \
         open(substations_file, 'w', newline='') as sf:

        writer_edges = csv.DictWriter(ef, fieldnames=pipelines_fields, delimiter=';')
        writer_nodes = csv.DictWriter(nf, fieldnames=nodes_fields, delimiter=';')
        writer_ebu = csv.DictWriter(bf, fieldnames=EBU_fields, delimiter=';')
        writer_subs = csv.DictWriter(sf, fieldnames=subst_fields, delimiter=';')

        writer_edges.writeheader()
        writer_nodes.writeheader()
        writer_ebu.writeheader()
        writer_subs.writeheader()

        


        # write nodes, ebu and substations by scanning nodes once
        OUTLET_OFFSET = 1000
        written_nodes = set()
        ebu_counter = 0
        subs_counter = 0
        node_count=1
        nodes_to_write = []  # Collect nodes before writing


        ## NODES ->  creates EBU and substation
        for node_id, data in graph.nodes(data=True):
            #creating dict so that nodes are indexed 1 ff
            node_id_index_dict[node_id]=node_count

            #reading data form node dicts
            node_type = data.get('node_type', '')
            name = data.get('name', '')
            supply_heating= data.get("is_supply_heating", "")
            altitude= data.get("altitude", "")
            #pressure and altitude are not usually attached here. although this could be interestingg

                # Network nodes
            if node_type and 'network' in node_type:
                    # write warm + cold nodes
                for mode, offset in (("warm", 0), ("cold", len_nodes)):
                    nodes_to_write.append({
                        'node_index': node_count + offset,
                        'pressure_pa': '', #for normal nodes no pressure is set
                        'altitude_m': '',
                        'node_type': node_type,
                        'node_mode': mode,
                        "node_id": node_id  # not sure how to fix doubling for now. used to use offset to dublicate id for retrun network.
                    })
                written_nodes.add(node_count)
                node_count+=1

            # Building nodes (demand or supply) -> V2 removing them from nodelist!
            elif 'building' in node_type:
                if supply_heating == True:
                    ebu_counter += 1
                    writer_ebu.writerow({
                        'ebu_index': ebu_counter,
                        'inlet_index': node_count,  ## no idea what node to use here! which one is connected to this building?
                        'outlet_index': node_count+len_nodes,
                        "ebu_name": name
                    })
                    
                    nodes_to_write.append({
                        'node_index': node_count,
                        'pressure_pa': pressure,
                        'altitude_m': altitude,
                        'node_type': 'reference',
                        'node_mode': 'reference',
                        "node_id": node_id
                    })
                    written_nodes.add(node_count)
                
                    nodes_to_write.append({
                        'node_index': node_count+len_nodes,
                        'pressure_pa': pressure2,
                        'altitude_m': '',
                        'node_type': 'reference',
                        'node_mode': 'reference',
                        "node_id": node_id
                    })   
                    node_count+=1


                else:  #normal buildings (supplystations)
                    subs_counter += 1
                    writer_subs.writerow({
                        'substation_index': subs_counter,
                        'inlet_index': node_count,
                        'outlet_index': node_count+len_nodes,
                        'T_set_sec': t_set_sec, #maybe get from geojson
                        'delta_T_sec': delta_t_sec, #maybe get from geojson
                        'delta_T_pri': delta_t_prim, #maybe get from geojson
                        'heat_exchange': 'heat_exchanger', #maybe get from geojson
                        'cooling_exchange': 'cooling_exchanger',
                        'substation name': name
                    })
                    
                    nodes_to_write.append({
                        'node_index': node_count,
                        'pressure_pa': '',
                        'altitude_m': altitude,
                        'node_type': 'building_inlet',
                        'node_mode': 'warm',
                        "node_id": node_id
                    })
                                    
                    nodes_to_write.append({
                        'node_index': node_count+len_nodes,
                        'pressure_pa': '',
                        'altitude_m': altitude,
                        'node_type': 'building_outlet',
                        'node_mode': 'cold',
                        "node_id": node_id
                    })
                    node_count+=1

            else:
                # fallback for any other node type
                nodes_to_write.append({
                    'node_index': node_count,
                    'pressure_pa': '',
                    'altitude_m': altitude,
                    'node_type': 'unspecified',
                    'node_mode': ' ',
                    'node_id': node_id
                })

                nodes_to_write.append({
                    'node_index': node_count+len_nodes,
                    'pressure_pa': '',
                    'altitude_m': altitude,
                    'node_type': 'unspecified',
                    'node_mode': ' ',
                    'node_id': node_id
                })
                node_count+=1

        # Sort nodes by node_index in ascending order before writing
        nodes_to_write.sort(key=lambda x: x['node_index'])
        
        # Write sorted nodes to CSV
        for node_row in nodes_to_write:
            writer_nodes.writerow(node_row)

        print(node_id_index_dict)

# write pipelines - check, ok
        pipeline_index = 0
        for mode, offset in (("warm", 0), ("cold", len_nodes)):
            for u, v, data in graph.edges(data=True):
                pipeline_index += 1

                # swap direction for cold pipes
                if mode == "cold": #use offset to cpoy lines
                    inlet = node_id_index_dict[v] + offset #v + offset
                    outlet = node_id_index_dict[u] + offset
                else: # no offset - original node_id as index
                    inlet = node_id_index_dict[u] + offset
                    outlet = node_id_index_dict[v] + offset

                edge_row = {
                    'pipeline_index': data.get('pipeID', pipeline_index),
                    'inlet_index': inlet,
                    'outlet_index': outlet,
                    'diameter_m': data.get('attr_dict', {}).get('dn', data.get('diameter_inner', diamteter)),
                    'length_m': data.get('length', 0),
                    'roughness_m': data.get('roughness', data.get('G', rough)),
                    'thickness_insulation_m': data.get('thickness_insulation', thickness_insulation),
                    'heat_conductivity_insulation': data.get(
                        'lambda_insulation',
                        data.get('heat_conductivity_insulation', heat_cond)
                    ),
                    'pipe_mode': mode,
                    "drawing_pipe_id": data.get('attr_dict', {}).get('id', data.get('diameter_inner', diamteter))
                }

                writer_edges.writerow(edge_row)


    
    print(f"HNS CSV files saved to {save_path}")
    if template == True:
        create_demand_template(substation_file=substations_file)



def compare_substations_with_buildings():
    """
    Compare substation indices from output/substations.csv with building names 
    from input/buildings.geojson (case-insensitive) and print those that are 
    not in substations.csv
    """
    
    # Read substation indices
    substation_indices = set()
    with open('output\heat_substations.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            substation_indices.add(row['substation_index'].lower())
    
    # Read building names from GeoJSON
    building_names = []
    with open('input/buildings.geojson', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
        for feature in geojson_data['features']:
            building_name = feature['properties'].get('name')
            if building_name:
                building_names.append(building_name)
    
    # Compare and find buildings not in substations
    buildings_not_in_substations = []
    for building_name in building_names:
        if building_name.lower() not in substation_indices:
            buildings_not_in_substations.append(building_name)
    
    # Print results
    print(f"comparing geojson buildings with substations.vsv:---\nTotal substation indices: {len(substation_indices)}")
    print(f"Total buildings: {len(building_names)}")
    print(f"Buildings NOT in substations.csv ({len(buildings_not_in_substations)}):")
    for building in buildings_not_in_substations:
        print(f"  {building}")
    
    return buildings_not_in_substations
