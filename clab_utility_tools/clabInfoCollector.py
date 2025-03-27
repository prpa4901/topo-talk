import json
import time
from .constants import (
    REMOTE_HOST, REMOTE_USERNAME, REMOTE_PASSWORD, REMOTE_PORT, REMOTE_TOPOLOGY_DIRECTORY
)
from .paramikoSSHClient import ParamikoSSHClient
import os


class ClabInfoCollector:

    def __init__(self):
        self.info = {}
        self.info['clab'] = {}
        self.info['clab']['version'] = '0.1'
        self.info['clab']['time'] = time.time()
        self.info['clab']['data'] = {}
        self.ssh_client = ParamikoSSHClient(REMOTE_HOST,
                                            REMOTE_USERNAME,
                                            REMOTE_PASSWORD,
                                            REMOTE_PORT)


    def inspect_clab_topo(self, topo_name):
        """
        Inspect the topology file and store the data in the info dictionary
        """
        cmd = f"clab inspect -t {REMOTE_TOPOLOGY_DIRECTORY}/{topo_name}.yaml --format json"
        # print(cmd)
        self.ssh_client.connect()
        output = self.ssh_client.exec_command(cmd)
        self.ssh_client.close()
        self.info['clab']['data'][f"topo-{topo_name}"] = json.loads(output)


    def gather_startup_configs(self, topo_name):
        """
        Gather the startup-configs from the devices in the topology
        """
        self.ssh_client.connect()
        for device in self.info['clab']['data'][f"topo-{topo_name}"]['containers']:
            node_name = device['name']
            if device['kind'] == 'ceos':
                config_path = "/mnt/flash/startup-config"
            else:
                config_path = "/config/startup-config.cfg"
            output = self.ssh_client.exec_command(f"docker exec {node_name} cat {config_path}")
            # print(output)
            device['startup-config'] = output
        self.ssh_client.close()
        # print(self.info['clab']['data'][f"topo-{topo_name}"]['containers'])

    def save_gather_info(self, topo_file_name, file_save_path):
        """
        Save the gathered info dictionary to a file
        """
        try:
            topo_name = topo_file_name.split('.')[0]
            self.inspect_clab_topo(topo_name)
            self.gather_startup_configs(topo_name)
            file_name = f"{file_save_path}/topology_data/{topo_name}_info.json"
            with open(file_name, "w", encoding='utf-8') as f:
                f.write(json.dumps(self.info['clab']['data'][f"topo-{topo_name}"], indent=4))
            print(f"Info saved to {topo_name}_info.json")
            return True
        except Exception as e:
            print(f"Error: {e}")
        
    