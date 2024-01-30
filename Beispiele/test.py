import uesgraphs as ug
from shapely.geometry import Point

graph = ug.simple_dhc_model()
graph = ug.add_more_networks(graph)

vis = ug.Visuals(example_district)
fig = vis.show_network(
    show_plot=True,
    scaling_factor=10,
)
