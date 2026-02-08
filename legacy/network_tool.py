import sys
sys.path.append('/root/edge')
import requests
import socket
import netifaces
import psutil
import ipaddress
from pkg.command_tool import shell_command
        
def test_ping(address: str, count: int = 1, timeout: float = 1.0) -> bool:
    try:
        command = f'ping {address} -c {count} -W {timeout}'
        result = shell_command(command)
        if '1 received' in result.stdout:
            return True
        else:
            return False
    except:
        return False

def test_port(host: str, port: int, timeout: float = 1.0) -> bool:
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.settimeout(timeout)
    result = socket_.connect_ex((host, port))
    socket_.close()
    if result == 0:
        status = True
    else:
        status = False
    return status
    
def get_private_networks() -> dict:
    results = {}
    interface = netifaces.interfaces()
    for item in interface:
        try:
            addresses = netifaces.ifaddresses(item)
            address = addresses[netifaces.AF_INET][0]['addr']
            netmask = addresses[netifaces.AF_INET][0]['netmask']
            results[item] = {'address': address,
                             'netmask': netmask,}
        except Exception as exc:
            pass
    return results
    
def get_public_ip(address: str, timeout: float = 1.0) -> str | None:
    try:
        response = requests.get(address, timeout=timeout)
        response.raise_for_status()
        public_ip = response.text.strip()
        return public_ip
    except Exception as exc:
        return None
    
def translate_netmask(netmask: str) -> int | None:
    try:
        parts = [int(part) for part in netmask.split('.')]
        if not all(0 <= part <= 255 for part in parts):
            return None
        postfix = sum(bin(part).count('1') for part in parts)
        return postfix
    except:
        return None

def get_network_address(ip_address: str, netmask: int) -> str:
    network = ipaddress.IPv4Network(f'{ip_address}/{netmask}', strict=False)
    network_address = str(network.network_address)
    return network_address

def get_default_gateway() -> str:
    gateways = netifaces.gateways()
    gateway_default = gateways.get('default')
    if gateway_default is not None:
        gateway_ip, gateway_interface = gateway_default[netifaces.AF_INET]
        return gateway_ip, gateway_interface
    else:
        return None

def get_gateway_origin_ip() -> str:
    gateway_ip, gateway_interface = get_default_gateway()
    if gateway_interface is None:
        return None
    else:
        interfaces = psutil.net_if_addrs()
        contents = interfaces[gateway_interface]
        for snicaddr in contents:
            if snicaddr.family == socket.AF_INET:
                this_ip = snicaddr.address
                this_subnet = snicaddr.netmask
                this_network_address = get_network_address(this_ip, this_subnet)
                gatway_network_address = get_network_address(gateway_ip, this_subnet)
                if this_network_address == gatway_network_address:
                    return this_ip
        return None

def update_ip_octet(ip_address: str, sequence: int, octet: int) -> str:
    ip_parts = ip_address.split('.')
    if 4 >= sequence >= 1:
        ip_parts[sequence - 1] = str(octet)
        ip_updated = '.'.join(ip_parts)
        return ip_updated
    else:
        return ip_address

if __name__ == '__main__':

    print(update_ip_octet('192.168.10.123', 4, 0))