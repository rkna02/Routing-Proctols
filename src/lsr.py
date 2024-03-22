class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.links = {}  # node_id: cost
        self.routing_table = {}  # Initialize the routing table here


class Network:
    def __init__(self):
        self.nodes = {}  # node_id: Node()

    def add_link(self, node1_id, node2_id, cost):
        if node1_id not in self.nodes:
            self.nodes[node1_id] = Node(node1_id)
        if node2_id not in self.nodes:
            self.nodes[node2_id] = Node(node2_id)
        self.nodes[node1_id].links[node2_id] = cost
        self.nodes[node2_id].links[node1_id] = cost

import heapq

def dijkstra(network, start_id):
    distances = {node_id: float('inf') for node_id in network.nodes}
    distances[start_id] = 0
    previous_nodes = {node_id: None for node_id in network.nodes}
    full_paths = {node_id: [] for node_id in network.nodes}  # Initialize full paths
    full_paths[start_id] = [start_id]  # Path to itself

    pq = [(0, start_id, [start_id])]  # Include start path in priority queue
    while pq:
        current_distance, current_node, current_path = heapq.heappop(pq)
        if current_distance > distances[current_node]:
            continue
        
        for neighbor, weight in network.nodes[current_node].links.items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                new_path = current_path + [neighbor]  # Construct new path
                full_paths[neighbor] = new_path  # Update full path
                heapq.heappush(pq, (distance, neighbor, new_path))
    
    return distances, previous_nodes, full_paths  # Return full paths as well

def build_routing_tables(network):
    routing_tables = {}
    for node_id in network.nodes:
        distances, previous_nodes, full_paths = dijkstra(network, node_id)
        routing_table = {}
        for dest_id, path in full_paths.items():
            if not path:
                continue
            cost = distances[dest_id]
            next_hop = path[1] if len(path) > 1 else node_id
            routing_table[dest_id] = (next_hop, cost, path[:-1])  # Store next_hop, cost, and path without destination
        routing_tables[node_id] = routing_table
    return routing_tables


def read_topology(file_name, network):
    with open(file_name, 'r') as file:
        for line in file:
            node1_id, node2_id, cost = map(int, line.split())
            network.add_link(node1_id, node2_id, cost)

def forward_messages(file_name, routing_tables, file_path):
    with open(file_name, 'r') as msg_file, open(file_path, 'a') as out_file:
        for line in msg_file:
            source_id, dest_id, message = line.split(maxsplit=2)
            source_id, dest_id = int(source_id), int(dest_id)
            # Directly use routing_tables, which maps source IDs to their routing tables
            if source_id in routing_tables and dest_id in routing_tables[source_id]:
                next_hop, cost, path = routing_tables[source_id][dest_id]
                hops = " ".join(map(str, path))  # path is already calculated in build_routing_tables
                out_file.write(f"from {source_id} to {dest_id} cost {cost} hops {hops} message {message.strip()}\n")
            else:
                out_file.write(f"from {source_id} to {dest_id} cost infinite hops unreachable message {message.strip()}\n")
        out_file.write("\n")


def read_changes(change_file):
    changes = []
    with open(change_file, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) == 3:
                node1_id, node2_id, cost = map(int, parts)
                changes.append((node1_id, node2_id, cost))
    return changes

def apply_change(network, node1_id, node2_id, cost):
    if cost == -999:  # Link removal
        if node1_id in network.nodes and node2_id in network.nodes[node1_id].links:
            del network.nodes[node1_id].links[node2_id]
            del network.nodes[node2_id].links[node1_id]
    else:  # Link addition or update
        network.add_link(node1_id, node2_id, cost)

def write_forwarding_tables(routing_tables, file_path):
    with open(file_path, 'a') as file:  # Consider 'w' for overwrite or 'a' for append based on your need
        for node_id in sorted(routing_tables.keys()):
            for dest_id, (next_hop, cost, _) in sorted(routing_tables[node_id].items()):
                file.write(f"{dest_id} {next_hop} {cost}\n")
            file.write("\n")


def main(topology_file, message_file, change_file, output_file):
    network = Network()
    read_topology(topology_file, network)
    routing_tables = build_routing_tables(network)  # Compute routing tables
    
    # Write initial forwarding tables to the output file
    write_forwarding_tables(routing_tables, output_file)
    
    # Forward messages based on initial routing tables
    forward_messages(message_file, routing_tables, output_file)
    
    # Handle topology changes and update output after each change
    changes = read_changes(change_file)
    for node1_id, node2_id, cost in changes:
        apply_change(network, node1_id, node2_id, cost)
        routing_tables = build_routing_tables(network)  # Re-compute routing tables after change
        write_forwarding_tables(routing_tables, output_file)  # Append updated tables to output file
        forward_messages(message_file, routing_tables, output_file)  # Forward messages based on updated tables


if __name__ == "__main__":
    import sys
    topology_file, message_file, change_file = sys.argv[1:4]
    output_file = 'output.txt'  # Define the output file path
    main(topology_file, message_file, change_file, output_file)