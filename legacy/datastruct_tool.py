from typing import Any, Union

def find_value(data: Union[dict, list], target: Any, _paths: Union[None, list]=None):
    """Find value from dict and list complex data structure"""
    
    # Initiate paths list
    if _paths is None:
        _paths = []
    
    # Search in case data is dict
    if isinstance(data, dict):
        for key, value in data.items():
            
            # Target is same as or contained in key
            if key == target or (isinstance(key, str) and isinstance(target, str) and target in key):
                found = key
                shape = 'key'
                _paths.insert(0, [dict, key])
                return found, shape, _paths
            
            # Target is same as or contained in value
            elif value == target or (isinstance(value, str) and isinstance(target, str) and target in value):
                found = value
                shape = 'value'
                _paths.insert(0, [dict, key])
                return found, shape, _paths
            
            # If no match, recursively search next data structure
            elif isinstance(value, list) or isinstance(value, dict):
                result = find_value(value, target, _paths)
                
                # If found, return result
                if result is not None:
                    found, shape, _paths = result
                    _paths.insert(0, [dict, key])
                    return found, shape, _paths
    
    # Search in case data is list
    elif isinstance(data, list):
        for index, value in enumerate(data):
            
            # Target is same as or contained in value
            if value == target or (isinstance(value, str) and isinstance(target, str) and target in value):
                found = value
                shape = 'value'
                _paths.insert(0, [list, index])
                return found, shape, _paths
            
            # If no match, recursively search next data structure
            elif isinstance(value, list) or isinstance(value, dict):
                result = find_value(value, target, _paths)
                
                # If found, return result
                if result is not None:
                    found, shape, _paths = result
                    _paths.insert(0, [list, index])
                    return found, shape, _paths
    
    # If no match, return none
    return None

def find_indices(data: list, target: Any) -> list[int]:
    """Find all indices of target value from list data"""
    
    result = []
    for index, element in enumerate(data):
        if element == target:
            result.append(index)
    return result


if __name__ == '__main__':
    data = {
        'network': {
            'ethernets': {
                'enp2s0': {
                    'addresses': ['192.168.2.123/24'],
                    'dhcp4': False,
                    'optional': True
                },
                'enp3s0': {
                    'addresses': ['192.168.10.123/24'],
                    'dhcp4': False,
                    'nameservers': {
                        'addresses': ['1.1.1.1', '8.8.8.8', '9.9.9.9']
                    },
                    'optional': 66.6,
                    'routes': [
                        {'to': '0.0.0.0/0', 'via': '192.168.10.254'}
                    ]
                }
            },
            'version': 2
        }
    }
    target = False
    print(find_value(data, target))
    
    data = [1, 2, 3, 2, 4, 2, 5]
    print(find_indices(data, 2))
    
