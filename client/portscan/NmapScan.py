import nmap

from client.subdomain.oneforall.config import PortScan

def Nmap_Portscan(ip, port_info_list=None):
    print(f'[+]端口扫描-开始nmap端口扫描[{ip}]')
    try:
        nm = nmap.PortScanner(nmap_search_path=PortScan.nmap_search_path)
    except Exception as e:
        print(f'[-]端口扫描-nmap初始化失败[{ip}];{e}')
        return None
    if port_info_list:
        ports = ','.join([str(tmp) for tmp in port_info_list])
        nm.scan(hosts=ip, ports=ports, arguments='-Pn -T 4 -sV --version-intensity=5')
    else:
        nm.scan(hosts=ip, arguments='-Pn -T 4 -sV --version-intensity=5')
    try:
        port_list = nm[ip]['tcp'].keys()
    except Exception as e:
        print(f'[-]端口扫描-nmap扫描异常[{ip}];{e}')
        return None
    else:
        port_dict = {}
        for port in port_list:
            if nm[ip].has_tcp(port):
                port_info = nm[ip]['tcp'][port]
                state = port_info.get('state', 'no')
                if state == 'open':
                    name = port_info.get('name', '')
                    product = port_info.get('product', '')
                    version = port_info.get('version', '')
                    port_dict[port] = {'ip': ip, 'port': port, 'name': name, 'product': product, 'version': version}
                    print(f'[+]端口扫描-nmap扫描成功：{ip}:{port} {name} {product} {version}')
        print(f'[+]端口扫描-nmap扫描完毕')
        return port_dict

if __name__ == '__main__':
    info = Nmap_Portscan('1.1.1.1')
    print(info)