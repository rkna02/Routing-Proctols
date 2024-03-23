"""
@file dvr.py

@brief This file contains implementations for Distance Vector Routing algorithms.
This module defines classes and functions related to Distance Vector Routing algorithms.

@author Peter Na (rkna02)
@author Eason Feng (Eason1223)

@bug No known bugs
"""


class Node:
    """
    @brief Represents a node in the graph network.

    This class represents a node in the network participating in distance vector routing.
    """

    def __init__(self, node_id):
        self.node_id = node_id
        self.neighbors = {}  # neighbor_id: link_cost
        self.routing_table = {}  # destination_id: (next_hop_id, path_cost)


class Network:
    """
    @brief Represents a network of nodes.

    This class represents a graph network of nodes.
    """

    def __init__(self):
        self.nodes = {}  # node_id: Node()

    def add_link(self, node1_id, node2_id, cost):
        """
        @brief Adds a link between two nodes in the network.

        @param node1_id: The ID of the first node.
        @param node2_id: The ID of the second node.
        @param cost: The cost of the link.

        @return Void
        """
        if node1_id not in self.nodes:
            self.nodes[node1_id] = Node(node1_id)
        if node2_id not in self.nodes:
            self.nodes[node2_id] = Node(node2_id)
        self.nodes[node1_id].neighbors[node2_id] = cost
        self.nodes[node2_id].neighbors[node1_id] = cost


def read_topology(file_name, network):
    """
    @brief Reads the network topology from a file and constructs the internal network object.

    @param file_name: The name of the file containing the topology.
    @param network: The Network object to store the topology.

    @return Void
    """
    with open(file_name, 'r') as file:
        for line in file:
            node1_id, node2_id, cost = map(int, line.split())
            network.add_link(node1_id, node2_id, cost)


def initial_routing_table_setup(network):
    """
    @brief Initializes the routing table for each node in the network.

    @param network: The Network object containing nodes.

    @return Void 
    """
    for node in network.nodes.values():
        # Initialize the routing table for direct connections
        node.routing_table[node.node_id] = ([node.node_id], 0)  # Path to itself
        for neighbor_id, cost in node.neighbors.items():
            node.routing_table[neighbor_id] = ([neighbor_id], cost)  # Direct neighbor path


def update_distance_vectors(network):
    """
    @brief Updates the distance vectors for each node in the network.

    @param network: The Network object containing nodes.

    @return Void
    """
    updated = True  # Flag to track if any updates were made in the current iteration

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
    """
    @brief Forwards messages from source to destination nodes in the network. Writes the message outputs to file_path 

    @param file_name: The name of the file containing messages.
    @param network: The Network object containing nodes.
    @param file_path: The path of the output file to write message forwarding results.

    @return Void
    """
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
    """
    @brief Reads changes to the network topology from the change file.

    @param change_file: The name of the file containing changes.

    @return: A list of tuples representing the changes.
    """
    changes = []
    with open(change_file, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) == 3:
                node1_id, node2_id, cost = map(int, parts)
                changes.append((node1_id, node2_id, cost))
    return changes


def apply_change(network, node1_id, node2_id, cost):
    """
    @brief Applies a network link change to the network topology.

    @param network: The Network object containing nodes.
    @param node1_id: The ID of the first node in the change.
    @param node2_id: The ID of the second node in the change.
    @param cost: The cost of the link between the nodes (-999 for link removal).

    @return Void
    """
    if cost == -999:  # Link removal
        if node1_id in network.nodes and node2_id in network.nodes[node1_id].neighbors:
            del network.nodes[node1_id].neighbors[node2_id]
            del network.nodes[node2_id].neighbors[node1_id]
    else:  # Link addition or update
        network.nodes[node1_id].neighbors[node2_id] = cost
        network.nodes[node2_id].neighbors[node1_id] = cost


def write_forwarding_tables(network, file_path):
    """
    @brief Writes forwarding tables to an output file.

    @param network: The Network object containing nodes.
    @param file_path: The path of the output file to write forwarding tables.

    @return Void
    """
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
    """
    @brief Main function to run the Distance Vector Routing algorithm.

    @param topology_file: The name of the file containing the network topology.
    @param message_file: The name of the file containing messages to forward.
    @param change_file: The name of the file containing changes to the network topology.
    @param output_file: The path of the output file to write results.

    @return Void
    """
    # Open output file and erase file content if there are any
    with open(output_file, 'w') as file:
        file.truncate()

    network = Network()
    read_topology(topology_file, network)
    initial_routing_table_setup(network)
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
    topology_file, message_file, change_file, output_file = sys.argv[1:5]
    main(topology_file, message_file, change_file, output_file)

