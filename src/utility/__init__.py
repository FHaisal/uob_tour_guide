#!/usr/bin/env python3

import json
import os
import math
script_dir = os.path.dirname(__file__)


def get_map_nodes(file_path=f'{script_dir}/map_nodes.json'):
    with open(file_path) as json_file:
        map_nodes = json.load(json_file)
    json_file.close()
    
    return map_nodes

def xy_dist(x1, y1, x2, y2):
    X2 = abs(max(x1, x2) - min(x1, x2))
    Y2 = abs(max(y1, y2) - min(y1, y2))
    return math.sqrt(X2**2 + Y2**2)

def get_tour_nodes(map_nodes, location, nodes_len=0, tour_nodes=None):
    if tour_nodes is None:
        tour_nodes = []
        map_nodes = [map_node for map_node in map_nodes if map_node['in_tour']]
    else:
        location = {
            'x': tour_nodes[len(tour_nodes) - 1]['position']['x'],
            'y': tour_nodes[len(tour_nodes) - 1]['position']['y']
        }

    if nodes_len <= 0:
        nodes_len = len(map_nodes)

    def sort_by_distance(item):
        return item['distance']

    for i, node in enumerate(map_nodes):
        dist = xy_dist(location['x'], location['y'], node['position']['x'], node['position']['y'])
        map_nodes[i]['distance'] = dist

    map_nodes.sort(key=sort_by_distance, reverse=False)

    tour_nodes.append(map_nodes[0])
    map_nodes.pop(0)

    if len(tour_nodes) >= nodes_len:
        return tour_nodes
    else:
        return get_tour_nodes(map_nodes=map_nodes, location=location, nodes_len=nodes_len, tour_nodes=tour_nodes)
