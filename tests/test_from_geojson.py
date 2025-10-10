"""Test GeoJSON import functionality"""

import os
import pytest

from uesgraphs import UESGraph


@pytest.fixture(scope="module")
def datadir():
    """Return path to test data directory"""
    test_file = os.path.abspath(__file__)
    test_dir = os.path.dirname(test_file)
    data_dir = os.path.join(test_dir, 'test_from_geojson')
    
    assert os.path.isdir(data_dir), f"Test data directory not found: {data_dir}"
    
    return data_dir


def test_from_geojson_basic(datadir):
    """Test basic GeoJSON import functionality"""
    
    # Import from GeoJSON
    graph = UESGraph()
    graph.from_geojson(
        network_path=os.path.join(datadir, 'network.geojson'),
        buildings_path=os.path.join(datadir, 'buildings.geojson'),
        supply_path=os.path.join(datadir, 'supply.geojson'),
        name='test_network'
    )
    
    # Load reference graph
    ref_graph = UESGraph()
    ref_graph.from_json(
        path=os.path.join(datadir, 'reference.json'),
        network_type='heating'
    )
    
    # Test node counts
    assert graph.number_of_nodes('heating') == ref_graph.number_of_nodes('heating'), \
        "Number of heating network nodes doesn't match"
    
    assert graph.number_of_nodes('building') == ref_graph.number_of_nodes('building'), \
        "Number of building nodes doesn't match"
    
    # Test edge count
    assert len(list(graph.edges())) == len(list(ref_graph.edges())), \
        "Number of edges doesn't match"
    
    # Test network length (with small tolerance for floating point)
    graph_length = graph.calc_network_length('heating')
    ref_length = ref_graph.calc_network_length('heating')
    assert abs(graph_length - ref_length) < 0.01, \
        f"Network length mismatch: {graph_length} vs {ref_length}"
    
    # Test that supply node exists and is marked correctly
    supply_nodes = [n for n in graph.nodelist_building 
                    if graph.nodes[n].get('is_supply_heating', False)]
    ref_supply_nodes = [n for n in ref_graph.nodelist_building 
                        if ref_graph.nodes[n].get('is_supply_heating', False)]
    assert len(supply_nodes) == len(ref_supply_nodes), \
        "Number of supply nodes doesn't match"


def test_from_geojson_diameters(datadir):
    """Test that DN values are correctly converted to inner diameters"""
    
    # Import from GeoJSON
    graph = UESGraph()
    graph.from_geojson(
        network_path=os.path.join(datadir, 'network.geojson'),
        buildings_path=os.path.join(datadir, 'buildings.geojson'),
        supply_path=os.path.join(datadir, 'supply.geojson'),
        name='test_network'
    )
    
    # Load reference graph
    ref_graph = UESGraph()
    ref_graph.from_json(
        path=os.path.join(datadir, 'reference.json'),
        network_type='heating'
    )
    """Extract edge properties independent of node IDs"""
    graph_edges = []
    for u, v in graph.edges():
        pos_u = graph.nodes[u]['position']
        pos_v = graph.nodes[v]['position']
        diameter = graph.edges[u, v].get('diameter')
        length = graph.edges[u, v].get('length')
        
        # Sort positions to make edge direction-independent
        edge_key = tuple(sorted([
            (round(pos_u.x, 6), round(pos_u.y, 6)),
            (round(pos_v.x, 6), round(pos_v.y, 6))
        ]))
        
        graph_edges.append({
            'positions': edge_key,
            'diameter': diameter,
            'length': round(length, 6)
        })

    ref_edges = []
    for u, v in ref_graph.edges():
        pos_u = ref_graph.nodes[u]['position']
        pos_v = ref_graph.nodes[v]['position']
        diameter = ref_graph.edges[u, v].get('diameter')
        length = ref_graph.edges[u, v].get('length')
        
        # Sort positions to make edge direction-independent
        edge_key = tuple(sorted([
            (round(pos_u.x, 6), round(pos_u.y, 6)),
            (round(pos_v.x, 6), round(pos_v.y, 6))
        ]))
        
        ref_edges.append({
            'positions': edge_key,
            'diameter': diameter,
            'length': round(length, 6)
        })
    
    # Compare edge counts
    assert len(graph_edges) == len(ref_edges), \
        f"Edge count mismatch: {len(graph_edges)} vs {len(ref_edges)}"
    
    # Compare each edge by position
    for ref_edge in ref_edges:
        matching = [e for e in graph_edges if e['positions'] == ref_edge['positions']]
        assert len(matching) == 1, \
            f"Could not find matching edge for positions {ref_edge['positions']}"
        
        graph_edge = matching[0]
        assert graph_edge['diameter'] == ref_edge['diameter'], \
            f"Diameter mismatch at {ref_edge['positions']}: {graph_edge['diameter']} vs {ref_edge['diameter']}"
        assert abs(graph_edge['length'] - ref_edge['length']) < 0.01, \
            f"Length mismatch at {ref_edge['positions']}: {graph_edge['length']} vs {ref_edge['length']}"
    
    # Verify specific DN conversions are present
    expected_diameters = {0.2101, 0.0539, 0.1325, 0.0697, 0.1071}
    actual_diameters = {e['diameter'] for e in graph_edges}
    
    assert expected_diameters.issubset(actual_diameters), \
        f"Missing expected diameter values"