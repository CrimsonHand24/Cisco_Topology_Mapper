import csv
import argparse
import textwrap
import netmiko
from pyvis.network import Network
import re

# Arguments Parser
parser = argparse.ArgumentParser(description='Process some information.')
parser.add_argument('path', type=str, help='File path of CSV')
args = parser.parse_args()

# Constants
REQUIRED_FIELDS = ['IP', 'Username', 'Password', 'Secret', 'Port', 'IOS']
DEVICE_TYPES = {'Switch': 'blue', 'Router': 'red'}
CONNECTION_DEFAULTS = {'port': '22', 'verbose': 'True'}

# Function to convert CSV to Dictionary
def csv_to_dict(filename):
    with open(filename, 'r') as file:
        return list(csv.DictReader(file))

# Function to establish a connection
def establish_connection(connection_dict):
    try:
        connection_action = netmiko.ConnectHandler(**connection_dict)
        if connection_action.is_alive():
            print(f'{connection_dict.get("host")} has passed!')
            return connection_action
    except Exception:
        print(f'''{connection_dict.get("host")} has failed
Check Ports, IP, Configurations; if using Telnet go back to your CSV and add "_telnet" to end of your IOS. If failure continues check Netmiko documentation.''')

# Function to add a node
def add_node(network, node_dict):
    node_label = f"""
        IP = {node_dict.get('Host')}:{node_dict.get('Port')}
        Type = {node_dict.get('Type')},
        Hostname = {node_dict.get('Hostname')}
        """
    network.add_node(
        node_dict.get('Hostname'),
        label=node_label,
        shape='dot',
        title=f'{node_dict.get("Hostname")}',
        color=DEVICE_TYPES.get(node_dict.get('Type'), 'blue')
    )

# Get connection details and make connections
device_info = []
filename = 'Hosts.csv'  # Replace with your CSV file path
csv_file = csv_to_dict(filename)

for connection in csv_file:
    connection_dict = CONNECTION_DEFAULTS.copy()
    for field in REQUIRED_FIELDS:
        connection_dict[field.lower()] = str(connection.get(field)) if connection.get(field) else connection_dict.get(field.lower(), '')
    connection_action = establish_connection(connection_dict)

    if connection_action:
        priviledge_level = connection_action.find_prompt()
        if ">" in priviledge_level:
            connection_action.send_command('enable')
        hostname = priviledge_level.strip('#')
        cdp_neighbors = connection_action.send_command('show cdp neighbors detail')
        router_or_switch = 'Switch' if 'Invalid input detected' in connection_action.send_command('show ip route') else 'Router'
        connection_action.disconnect()
        device_info.append({'CDP_Neighbor':str(textwrap.dedent(cdp_neighbors)), "Hostname":hostname, 'Host':connection_dict.get('host'), 'Type':router_or_switch, 'Port':connection_dict.get('port')})

# Generate Network Topology
net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", select_menu=True)

nodes_relationship = {}
for node in device_info:
    add_node(net, node)
    find_pattern = re.findall(r"(Device ID:.*?)(\n|$)", node.get('CDP_Neighbor'))
    nodes_relationship[node.get('Hostname')] = find_pattern

for connect_nodes in nodes_relationship:
    for nodes_entries in nodes_relationship.get(connect_nodes):
        net.add_edge(connect_nodes, nodes_entries[0].split(':')[1].strip(' '), length=200)

net.toggle_physics(True)
net.show('myTopology.html')