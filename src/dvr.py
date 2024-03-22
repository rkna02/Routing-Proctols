class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.neighbors = {}  # neighbor_id: link_cost
        self.routing_table = {}  # destination_id: (next_hop_id, path_cost)

class Network:
    def __init__(self):
        self.nodes = {}  # node_id: Node()

    def add_link(self, node1_id, node2_id, cost):
        if node1_id not in self.nodes:
            self.nodes[node1_id] = Node(node1_id)
        if node2_id not in self.nodes:
            self.nodes[node2_id] = Node(node2_id)
        self.nodes[node1_id].neighbors[node2_id] = cost
        self.nodes[node2_id].neighbors[node1_id] = cost

def read_topology(file_name, network):
    with open(file_name, 'r') as file:
        for line in file:
            node1_id, node2_id, cost = map(int, line.split())
            network.add_link(node1_id, node2_id, cost)

def initial_routing_table_setup(network):
    for node in network.nodes.values():
        # Initialize the routing table for direct connections
        node.routing_table[node.node_id] = ([node.node_id], 0)  # Path to itself
        for neighbor_id, cost in node.neighbors.items():
            node.routing_table[neighbor_id] = ([neighbor_id], cost)  # Direct neighbor path

def update_distance_vectors(network):
    # Flag to track if any updates were made in the current iteration
    updated = True
    while updated:
        updated = False
        # Iterate over all nodes in the network
        for node in network.nodes.values():
            # Iterate over all neighbors of the current node
            for neighbor_id, link_cost in node.neighbors.items():
                neighbor = network.nodes[neighbor_id]
                # Iterate over all destination entries in the neighbor's routing table
                for dest, (neighbor_path, path_cost) in neighbor.routing_table.items():
                    # Calculate new cost to destination via this neighbor
                    new_cost = link_cost + path_cost
                    # If the destination is not in the node's routing table or a cheaper path is found
                    if dest not in node.routing_table or node.routing_table[dest][1] > new_cost:
                        # Create a new path that includes this node and the path from the neighbor
                        new_path = [node.node_id] + neighbor_path
                        # Update the node's routing table with this new path and its total cost
                        node.routing_table[dest] = (new_path, new_cost)
                        updated = True

def forward_messages(file_name, network, file_path):
    with open(file_name, 'r') as msg_file, open(file_path, 'a') as out_file:
        for line in msg_file:
            source_id, dest_id, message = line.split(maxsplit=2)
            source_id, dest_id = int(source_id), int(dest_id)
            if dest_id in network.nodes[source_id].routing_table:
                path, cost = network.nodes[source_id].routing_table[dest_id]
                hops = " ".join(map(str, path[:-1]))  # Path excluding the destination
                out_file.write(f"from {source_id} to {dest_id} cost {cost} hops {hops} message {message.strip()}\n")
            else:
                out_file.write(f"from {source_id} to {dest_id} cost infinite hops unreachable message {message.strip()}\n")
        out_file.write("\n")  # Newline for readability before any changes

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
        if node1_id in network.nodes and node2_id in network.nodes[node1_id].neighbors:
            del network.nodes[node1_id].neighbors[node2_id]
            del network.nodes[node2_id].neighbors[node1_id]
    else:  # Link addition or update
        network.nodes[node1_id].neighbors[node2_id] = cost
        network.nodes[node2_id].neighbors[node1_id] = cost

def write_forwarding_tables(network, file_path):
    with open(file_path, 'a') as file:
        for node_id in sorted(network.nodes):
            node = network.nodes[node_id]
            for dest_id in sorted(node.routing_table):
                path, cost = node.routing_table[dest_id]
                # Extract next hop from path
                next_hop = path[1] if len(path) > 1 else node_id
                file.write(f"{dest_id} {next_hop} {cost}\n")
            file.write("\n")  # Newline for readability between node entries

def main(topology_file, message_file, change_file, output_file):
    network = Network()
    read_topology(topology_file, network)
    initial_routing_table_setup(network)  # Ensure this function sets up initial routing tables
    update_distance_vectors(network)
    
    # Write initial forwarding tables and message forwarding outcomes
    write_forwarding_tables(network, output_file)
    forward_messages(message_file, network, output_file)

    # Handle changes
    changes = read_changes(change_file)
    for node1_id, node2_id, cost in changes:
        apply_change(network, node1_id, node2_id, cost)
        update_distance_vectors(network)
        write_forwarding_tables(network, output_file)  # Append updated forwarding tables
        forward_messages(message_file, network, output_file)  # Append updated message outcomes

if __name__ == "__main__":
    import sys
    topology_file, message_file, change_file = sys.argv[1:4]
    output_file = 'output.txt'  # Define the output file path
    main(topology_file, message_file, change_file, output_file)

