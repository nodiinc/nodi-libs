import yaml

class Yaml:
    """yaml Controller"""
    
    def __init__(self, path):
        self.path = path
    
    def read_yaml(self):
        """Read yaml file, convert to string"""
        with open(self.path, 'r') as file:
            raw = yaml.load(file, Loader=yaml.FullLoader)
            data = yaml.dump(raw)
            return data
    
    def write_yaml(self, data):
        """Get string, write to yaml file"""
        with open(self.path, 'w') as file:
            data = yaml.load(data, Loader=yaml.FullLoader)
            yaml.dump(data, file)

    def yaml_to_dict(self, yaml_data):
        """Convert dict to yaml format"""
        dict_data =  yaml.safe_load(yaml_data)
        return dict_data

    def dict_to_yaml(self, dict_data):
        """Convert to yaml format to dict"""
        yaml_data = yaml.dump(dict_data)
        return yaml_data
    
if __name__ == '__main__':
    
    test_yaml = '''
network:
  version: 2
  renderer: networkd
  ethernets:
    enp3s0:
      addresses:
        - 10.100.1.37/24
        - 10.100.1.38/24:
            label: "enp3s0:0"
        - 10.100.1.39/24:
            label: "enp3s0:some-label"
            '''
     
    yaml_obj = Yaml()
    import pprint
    pprint.pprint(yaml_obj.yaml_to_dict(test_yaml))
    
    # yaml_str = yaml_obj.read_yaml('/etc/netplan/nodi.yaml')
    # print(yaml_str)
    # print(type(yaml_str))
    # yaml_dc = yaml_obj.yaml_to_dict(yaml_str)
    # print(yaml_dc)
    # print(type(yaml_dc))
    # yaml_str = yaml_obj.dict_to_yaml(yaml_dc)
    # print(yaml_str)
    # print(type(yaml_str))
    # yaml_obj.write_yaml(yaml_str, '/etc/netplan/nodi.yaml')
    
    