import json
import time
from .constants import (
    REMOTE_HOST, REMOTE_USERNAME, REMOTE_PASSWORD, REMOTE_PORT, REMOTE_TOPOLOGY_DIRECTORY
)
from .paramikoSSHClient import ParamikoSSHClient


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


    def inspect_clab_topo(self, topo_file_name):
        """
        Inspect the topology file and store the data in the info dictionary
        """
        cmd = f"clab inspect {REMOTE_TOPOLOGY_DIRECTORY}/{topo_file_name} --format json"
        output = self.ssh_client.exec_command(cmd)
        topo_name = topo_file_name.split('.')[0]
        self.info['clab']['data'][f"topo-{topo_name}"] = json.loads(output)


    def gather_startup_configs(self, topo_file_name):
        """
        Gather the startup-configs from the devices in the topology
        """
        topo_name = topo_file_name.split('.')[0]
        for device in self.info['clab']['data'][f"topo-{topo_name}"]['containers']:
            node_name = device['name']
            output = self.ssh_client.exec_command(f"docker exec -it {node_name} cat /config/startup-config")
            device['startup-config'] = output
        print(self.info['clab']['data'][f"topo-{topo_name}"]['containers'])

    def save_gather_info(self, topo_file_name):
        """
        Save the gathered info dictionary to a file
        """
        self.inspect_clab_topo(topo_file_name)
        self.gather_startup_configs(topo_file_name)
        topo_name = topo_file_name.split('.')[0]
        with open(f"{topo_name}_info.json", "w", encoding='utf-8') as f:
            f.write(json.dumps(self.info['clab']['data'][f"topo-{topo_name}"], indent=4))
        print(f"Info saved to {topo_name}_info.json")
        
    