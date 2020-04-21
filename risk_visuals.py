from math import cos, radians, sin
from tkinter import Tk

from matplotlib import pyplot
import networkx


def create_node_positions(base_pos, node_distance, num_neighbors):
    node_positions = []
    degree_increment = 90 // num_neighbors
    for i in range(num_neighbors):
        branching_angle = radians(45 - i * degree_increment)
        # Position neighbors based on polar coordinates branching out from given node
        node_positions.append((
            base_pos[0] + node_distance * cos(branching_angle),
            base_pos[1] + node_distance * sin(branching_angle),
        ))
    return node_positions


def draw_risk_map(territory_list, continent_dict, title):
    risk_map = networkx.Graph()
    colors = []
    positions = dict()
    labels = dict()
    distance = 3 / len(territory_list)
    # Breadth first traversal
    territory_queue = []
    visited = {t.name: {'checked': False, 'pos': (0, 0)} for t in territory_list}
    territory_queue.append(territory_list[0])
    visited[territory_list[0].name]['checked'] = True
    visited[territory_list[0].name]['pos'] = (0.1, 0.5)
    while territory_queue:
        territory = territory_queue.pop(0)
        # Include territory in map
        risk_map.add_node(territory.name)
        # Specify color based on continent
        colors.append(continent_dict[territory.continent])
        # Position territory in map
        positions[territory.name] = visited[territory.name]['pos']
        army_tag = 'army' if territory.occupying_armies == 1 else 'armies'
        occupier = '' if not territory.occupying_player else territory.occupying_player.name
        # Label territory with name, army count, and occupying player
        labels[territory.name] = '{}\n{} {}\n{}'.format(territory.name, territory.occupying_armies, army_tag, occupier)
        neighbor_positions = create_node_positions(visited[territory.name]['pos'], distance, len(territory.neighbors))
        for i, neighbor in enumerate(territory.neighbors):
            if not visited[neighbor.name]['checked']:
                risk_map.add_edge(territory.name, neighbor.name)
                territory_queue.append(neighbor)
                visited[neighbor.name]['checked'] = True
                visited[neighbor.name]['pos'] = neighbor_positions[i]
    pyplot.figure(title, figsize=get_window_dimensions())
    networkx.draw(
        risk_map,
        pos=positions,
        node_size=2000,
        node_color=colors,
        edge_color='#bdc2c9',
        labels=labels,
        font_size=8,
        font_weight='bold',
        title=title,
    )
    pyplot.show()


def get_window_dimensions():
    tk_window = Tk()
    # Match window dimensions to aspect ratio of computer
    dimensions = (tk_window.winfo_screenmmwidth() / 30, tk_window.winfo_screenmmheight() / 40)
    tk_window.destroy()
    return dimensions
