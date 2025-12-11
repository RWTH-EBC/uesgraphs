import os
import csv
from uesgraphs import UESGraph



def UESgraph_to_HNScsv(graph, save_path):
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
    edges_file = os.path.join(save_path, 'pipelines.csv')
    substations_file = os.path.join(save_path, 'substations.csv')
    nodes_file = os.path.join(save_path, 'nodes.csv')
    EBU_file = os.path.join(save_path, 'energybalancingunit.csv')

    pipelines_fields = ['pipeline_index', 'inlet_index', 'outlet_index','diameter_m', 'length_m', 'roughness_m', 'thickness_insulation_m', 'heat_conductivity_insulation', 'pipe_mode']
    nodes_fields = ['node_index', 'pressure_pa', 'altitude_m', 'node_type', 'node_mode']
    EBU_fields = ['ebu_index', 'inlet_index', 'outlet_index']
    subst_fields = ['substation_index', 'inlet_index', 'outlet_index', 'T_set_sec', 'delta_T_sec', 'delta_T_pri', 'heat_exchange', 'cooling_exchange']


    # Write all files in a single context manager to avoid re-opening multiple times
    with open(edges_file, 'w', newline='') as ef, \
         open(nodes_file, 'w', newline='') as nf, \
         open(EBU_file, 'w', newline='') as bf, \
         open(substations_file, 'w', newline='') as sf:

        writer_edges = csv.DictWriter(ef, fieldnames=pipelines_fields)
        writer_nodes = csv.DictWriter(nf, fieldnames=nodes_fields)
        writer_ebu = csv.DictWriter(bf, fieldnames=EBU_fields)
        writer_subs = csv.DictWriter(sf, fieldnames=subst_fields)

        writer_edges.writeheader()
        writer_nodes.writeheader()
        writer_ebu.writeheader()
        writer_subs.writeheader()

        # write pipelines - check, ok
        pipeline_index = 0
        for mode, offset in (("warm", 0), ("cold", 1000)):
            for u, v, data in graph.edges(data=True):
                pipeline_index += 1

                # swap direction for cold pipes
                if mode == "cold":
                    inlet = v + offset
                    outlet = u + offset
                else:
                    inlet = u + offset
                    outlet = v + offset

                edge_row = {
                    'pipeline_index': data.get('pipeID', pipeline_index),
                    'inlet_index': inlet,
                    'outlet_index': outlet,
                    'diameter_m': data.get('diameter', data.get('diameter_inner', '')),
                    'length_m': data.get('length', 0),
                    'roughness_m': data.get('roughness', data.get('G', '')),
                    'thickness_insulation_m': data.get('thickness_insulation', ''),
                    'heat_conductivity_insulation': data.get(
                        'lambda_insulation',
                        data.get('heat_conductivity_insulation', '')
                    ),
                    'pipe_mode': mode,
                }

                writer_edges.writerow(edge_row)



        # write nodes, ebu and substations by scanning nodes once
        OUTLET_OFFSET = 1000
        written_nodes = set()
        ebu_counter = 0
        subs_counter = 0

        for node_id, data in graph.nodes(data=True):
            node_type = data.get('node_type', '')
            pressure = data.get('pressure_pa', '') #N/A
            altitude = data.get('altitude_m', '') #N/A

            if node_id not in written_nodes:
                # Network nodes
                if node_type and 'network' in node_type:
                      # write warm + cold nodes
                    for mode, offset in (("warm", 0), ("cold", 1000)):
                        writer_nodes.writerow({
                            'node_index': node_id + offset,
                            'pressure_pa': pressure,
                            'altitude_m': altitude,
                            'node_type': node_type,
                            'node_mode': mode,
                        })

                    written_nodes.add(node_id)

                # Building nodes (demand or supply)
                elif 'building' in node_type:
                    # Create an outlet node index for the building (avoid collision for strings)
                    if isinstance(node_id, int):
                        outlet_id = node_id + OUTLET_OFFSET
                    else:
                        outlet_id = f"{node_id}_out"

                    if data.get('is_supply_heating', False) is True:
                        ebu_counter += 1
                        writer_ebu.writerow({
                            'ebu_index': ebu_counter,
                            'inlet_index': node_id,
                            'outlet_index': outlet_id,
                        })
                        # add nodes for inlet and outlet
                        if node_id not in written_nodes:
                            writer_nodes.writerow({
                                'node_index': node_id,
                                'pressure_pa': pressure,
                                'altitude_m': altitude,
                                'node_type': 'building',
                                'node_mode': 'reference',
                            })
                            written_nodes.add(node_id)
                        if outlet_id not in written_nodes:
                            writer_nodes.writerow({
                                'node_index': outlet_id,
                                'pressure_pa': '',
                                'altitude_m': '',
                                'node_type': 'building_outlet',
                                'node_mode': 'reference',
                            })
                            written_nodes.add(outlet_id)
                    else:
                        subs_counter += 1
                        writer_subs.writerow({
                            'substation_index': subs_counter,
                            'inlet_index': node_id,
                            'outlet_index': outlet_id,
                            'T_set_sec': '',
                            'delta_T_sec': '',
                            'delta_T_pri': '',
                            'heat_exchange': '',
                            'cooling_exchange': '',
                        })
                        if node_id not in written_nodes:
                            writer_nodes.writerow({
                                'node_index': node_id,
                                'pressure_pa': pressure,
                                'altitude_m': altitude,
                                'node_type': 'building',
                                'node_mode': '',
                            })
                            written_nodes.add(node_id)
                        if outlet_id not in written_nodes:
                            writer_nodes.writerow({
                                'node_index': outlet_id,
                                'pressure_pa': '',
                                'altitude_m': '',
                                'node_type': 'building_outlet',
                                'node_mode': '',
                            })
                            written_nodes.add(outlet_id)

                else:
                    # fallback for any other node type
                    node_mode = data.get('node_mode', '')
                    if node_id not in written_nodes:
                        writer_nodes.writerow({
                            'node_index': node_id,
                            'pressure_pa': pressure,
                            'altitude_m': altitude,
                            'node_type': node_type or '',
                            'node_mode': node_mode,
                        })
                        written_nodes.add(node_id)




    
    print(f"HNS CSV files saved to {save_path}")