import asycio
import json
import subprocess
import time

class ClabInfoCollector:

    def __init__(self):
        self.info = {}
        self.info['clab'] = {}
        self.info['clab']['version'] = '0.1'
        self.info['clab']['time'] = time.time()
        self.info['clab']['data'] = {}
    
    def inspect_clab_topo(self, topo_file_name):
        """
        Inspect the topology file and store the data in the info dictionary
        """
        curr_dir = os.getcwd()
        output = subprocess.run(
            ['clab', 'inspect', '-t', '{}/topologies/{}'.format(curr_dir, topo_file_name), '--format', 'json'],
            capture_output=True,
            text=True,
        )
        topo_name = topo_file_name.split('.')[0]
        self.info['clab']['data']['topo-{}'.format(topo_name)] = json.loads(output.stdout)
    
    def gather_startup_configs(self, topo_file_name):
        """
        Gather the startup-configs from the devices in the topology
        """
        for device in self.info['clab']['data']['topo-{}'.format(topo_name)]['containers']:
            node_name = device['name']
            output = subprocess.run(
                ['clab', 'exec', node_name, 'cat', '/config/startup-config'],
                capture_output=True,
                text=True,
            )
            device['startup-config'] = output.stdout
        print(self.info['clab']['data']['topo-{}'.format(topo_name)]['containers'])
        
    