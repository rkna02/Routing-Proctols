"""
@file dvr.py

@brief This file contains classes, functions, and their implementations for Distance Vector Routing algorithms.

@author Peter Na (rkna02)
@author Eason Feng (eason1223)

@bug No known bugs
"""


import sys
import copy


class NetworkSimulator:
    """
    @brief Simulates network behavior using the Distance Vector Routing algorithm.

    This class reads network topology, messages, and changes from files, and updates routing tables accordingly. It also
    simulates message forwarding based on the current network state. 
    """


    def __init__(self, topology_file, messages_file, changes_file):
        """
        @brief Initializes the NetworkSimulator object.
        topology: map mapping nodes to each other including their path costs
        messages: array of tuples containing source node, destination node, and actual message
        changes: array of tuples containing 2 nodes and their updated path cost
        routing_tables: 2D array with each entry being the cost and next hop of one node to another

        @param topology_file: The path to the file containing network topology.
        @param messages_file: The path to the file containing messages to be sent.
        @param changes_file: The path to the file containing changes to the network topology.

        @return Void
        """
        self.topology = self.read_topology(topology_file)
        self.messages = self.read_messages(messages_file)
        self.changes = self.read_changes(changes_file)
        self.routing_tables = {node: {node: (0, node)} for node in self.topology}


    def read_topology(self, file_path):
        """
        @brief Reads network topology from initial topology file into the topology map, and set path costs for nodes

        @param file_path: The path to the file containing network topology.
        
        @return: A map representing the network topology.
        """
        topology = {}
        with open(file_path, 'r') as file:
            for line in file:
                node1, node2, cost = line.strip().split()
                cost = int(cost)
                topology.setdefault(node1, {})[node2] = cost
                topology.setdefault(node2, {})[node1] = cost
        return topology


    def read_messages(self, file_path):
        """
        @brief Reads messages from a file and parses them into the messages array

        @param file_path: The path to the file containing messages.

        @return: An array of tuples representing messages.
        """
        messages = []
        with open(file_path, 'r') as file:
            for line in file:
                source, destination, message = line.strip().split(' ', 2)
                messages.append((source, destination, message))
        return messages


    def read_changes(self, file_path):
        """
        @brief Reads changes to the network topology from a file and parses them into the changes array

        @param file_path: The path to the file containing changes.

        @return: An array of tuples representing changes.
        """
        changes = []
        with open(file_path, 'r') as file:
            for line in file:
                node1, node2, cost = line.strip().split()
                changes.append((node1, node2, int(cost)))
        return changes


    def dvr_convergence(self):
        """
        @brief Performs Distance Vector Routing convergence when there is a network change applied.
        Keeps updating routing tables until no more changes were applied after an iteration 

        @return Void
        """
        changed = True
        while changed:
            changed = False
            # Copy the current state of routing tables to compare after potential updates
            previous_routing_tables = copy.deepcopy(self.routing_tables)
            for node, neighbors in self.topology.items():
                # updates routing tables based on nodes' neighbors
                if self.update_routing_table(node, neighbors):
                    changed = True
            # Check if any routing table has actually changed
            if previous_routing_tables == self.routing_tables:
                changed = False


    def update_routing_table(self, node, neighbors):
        """
        @brief Updates the routing table for a node based on its neighbors and path costs to neighbors

        @param node: The node for which to update the routing table.
        @param neighbors: The neighbors of the node.
        @return: True if the routing table was updated, False otherwise.
        """
        updated = False
        for neighbor, link_cost in neighbors.items():
            for dest, (neighbor_total_cost, next_hop) in self.routing_tables[neighbor].items():
                new_cost = link_cost + neighbor_total_cost
                # Check if a better path is found or if the same-cost path has a lower next-hop ID
                if dest not in self.routing_tables[node] or new_cost < self.routing_tables[node][dest][0]:
                    self.routing_tables[node][dest] = (new_cost, neighbor)
                    updated = True
                elif new_cost == self.routing_tables[node][dest][0]:
                    # Tie breaking: only update if the new next-hop ID is lower
                    if neighbor < next_hop:
                        self.routing_tables[node][dest] = (new_cost, neighbor)
                        updated = True
        return updated


    def simulate_messages(self):
        """
        @brief Simulates message forwarding in the network by traversing the next hops of path nodes

        @return: A list of strings representing the simulated messages sent with source, destination, cost, and hop path.
        """
        message_paths = []
        for source, destination, message_text in self.messages:
            if destination in self.routing_tables[source]:
                path_cost, _ = self.routing_tables[source][destination]
                path = [source]
                next_hop = self.routing_tables[source][destination][1]
                while next_hop != destination:
                    path.append(next_hop)
                    next_hop = self.routing_tables[next_hop][destination][1]
                # Adjusting the path output to exclude the destination and match the example
                hops_path = ' '.join(path) if len(path) > 1 else "unreachable"
                message_paths.append(f"from {source} to {destination} cost {path_cost} hops {hops_path} message {message_text}")
            else:
                message_paths.append(f"from {source} to {destination} cost infinite hops unreachable message {message_text}")
        return message_paths


    def print_routing_table(self, file=None):
        """
        @brief Writes the routing tables of nodes in sorted order (by node ID) to a file.

        @param file: The file to print the routing tables to. If None, prints to standard output.

        @return Void
        """
        for node in sorted(self.routing_tables.keys()):
            for destination in sorted(self.routing_tables[node].keys()):
                cost, next_hop = self.routing_tables[node][destination]
                print(f"{destination} {next_hop} {cost}", file=file)
            print(file=file)


    def run_simulation(self, output_file):
        """
        @brief Runs the network simulation, send messages, apply network changes, and writes each node's forwarding table and messages sent to the output file.

        @param output_file: The path to the output file.

        @return Void
        """
        with open(output_file, 'w') as f:
            self.dvr_convergence()
            # Print the initial routing tables directly without a preceding newline.
            self.print_routing_table(f)
            
            # Simulate and print initial messages.
            initial_message_simulation = self.simulate_messages()
            if initial_message_simulation:
                # Print a newline only if there are initial messages to ensure separation.
                print("\n".join(initial_message_simulation), file=f)

            for change in self.changes:
                node1, node2, new_cost = change
                if new_cost == -999:
                    self.topology[node1].pop(node2, None)
                    self.topology[node2].pop(node1, None)
                else:
                    self.topology[node1][node2] = new_cost
                    self.topology[node2][node1] = new_cost

                self.routing_tables = {node: {node: (0, node)} for node in self.topology}
                self.dvr_convergence()

                # The newline is printed here to separate the sections correctly.
                print(file=f)

                self.print_routing_table(f)

                # Simulate and print messages after change.
                messages_after_change = self.simulate_messages()
                if messages_after_change:
                    # Print a newline only if there are messages after the change to ensure proper separation.
                    print("\n".join(messages_after_change), file=f)

def main(argv):
    """
    @brief Main function to start the network simulation.

    @param argv: Command line arguments.

    @return Void
    """
    if len(argv) != 5:
        sys.exit(1)
    topology_file, messages_file, changes_file, output_file = argv[1:]
    simulator = NetworkSimulator(topology_file, messages_file, changes_file)
    simulator.run_simulation(output_file)


if __name__ == "__main__":
    main(sys.argv)
