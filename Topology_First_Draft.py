import csv
import argparse
import textwrap
import netmiko
from pyvis.network import Network
import re

parser = argparse.ArgumentParser(description='Process some information.')

# Add mandatory arguments
parser.add_argument('path', type=str, help='File path of CSV')

args = parser.parse_args()

print(args.path)

Device_Info = []


def csv_to_dict(filename):
    result = []
    with open(args.path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            result.append(row)
    return result

# Example usage
filename = 'Hosts.csv'  # Replace with your CSV file path
CSV_File = csv_to_dict(filename)
for row in CSV_File:
    print(row)

print('------')
print(CSV_File)

for Connection in CSV_File:
    Connection_Dict = {}
    if len(Connection.get('IP')) != 0:
        Connection_Dict['host'] = str(Connection.get('IP'))
    else:
        pass
    if len(Connection.get('Username')) != 0:
        Connection_Dict['username'] = str(Connection.get('Username'))
    else:
        pass
    if len(Connection.get('Password')) != 0:
        Connection_Dict['password'] = str(Connection.get('Password'))
    else:
        pass
    if len(Connection.get('Secret')) != 0:
        Connection_Dict['secret'] = str(Connection.get('Secret'))
    else:
        pass
    if len(Connection.get('Port')) != 0:
        Connection_Dict['port'] = str(Connection.get('Port'))
    else:
        Connection_Dict['port'] = str(22)
    if len(Connection.get('IOS')) != 0:
        Connection_Dict['device_type'] = str(Connection.get('IOS'))
    else:
        pass
    Connection_Dict['verbose'] = 'True'

    print(Connection_Dict)

    try:
        Connection_Action = netmiko.ConnectHandler(**Connection_Dict)
        if Connection_Action.is_alive() == True:
            print(f'{Connection_Dict.get("host")} has passed!')
        else:
            raise Exception('Failed')
    except Exception:
        print(f'''{Connection_Dict.get("host")} has failed
Check Ports, IP, Configurations; if using Telnet go back to your CSV and add "_telnet" to end of your IOS. If failure continues check Netmiko documentation.''')
    Priviledge_Level = Connection_Action.find_prompt()
    if ">" in Priviledge_Level:
        Connection_Action.send_command('enable')
    else:
        pass


    Hostname = Priviledge_Level.strip('#')
    CDP_Neighbors = Connection_Action.send_command('''show cdp neighbors detail''')

    Router_Or_Switch = Connection_Action.send_command('show ip route')
    if 'Invalid input detected' in Router_Or_Switch:
        Router_Or_Switch = 'Switch'
    else:
        Router_Or_Switch = 'Router'

    Connection_Action.disconnect()
    Device_Info.append({'CDP_Neighbor':str(textwrap.dedent(CDP_Neighbors)),"Hostname":Hostname,'Host':Connection_Dict.get('host'),'Type':str(Router_Or_Switch)
    ,'Port':Connection_Dict.get('port')})
#---------------------------------------------------------

net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", select_menu=True)

Nodes_Relationship = {}
for Nodes in Device_Info:
    if Nodes.get('Type') == 'Router':
        net.add_node(Nodes.get('Hostname'), label=f"""
        IP = {Nodes.get('Host')}:{Nodes.get('Port')}
        Type = {Nodes.get('Type')},
        Hostname = {Nodes.get('Hostname')}
        """, shape='dot', title=f'{Nodes.get("Hostname")}',color="red")  # node id = 1 and label = Node 1

        Find_Pattern = (re.findall(r"(Device ID:.*?)(\n|$)", Nodes.get('CDP_Neighbor')))
        Nodes_Relationship[Nodes.get('Hostname')] = Find_Pattern
    else:
            net.add_node(Nodes.get('Hostname'), label=f"""
            IP = {Nodes.get('Host')}:{Nodes.get('Port')}
            Type = {Nodes.get('Type')},
            Hostname = {Nodes.get('Hostname')}
            """, shape='dot', title=f'{Nodes.get("Hostname")}', color="blue")  # node id = 1 and label = Node 1

            Find_Pattern = (re.findall(r"(Device ID:.*?)(\n|$)", Nodes.get('CDP_Neighbor')))
            Nodes_Relationship[Nodes.get('Hostname')] = Find_Pattern



#print(Nodes_Relationship)
for Connect_Nodes in Nodes_Relationship:
    List_Nodes = Nodes_Relationship.get(Connect_Nodes)
    for Nodes_Entries in List_Nodes:
        net.add_edge(Connect_Nodes,Nodes_Entries[0].split(':')[1].strip(' '),length=200)

net.toggle_physics(True)
net.show('myTopology.html')


