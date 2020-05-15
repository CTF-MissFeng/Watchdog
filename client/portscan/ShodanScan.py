import shodan
import time

from client.subdomain.oneforall.config import PortScan

check = True
if not PortScan.shodan_api:
    print('[-]端口扫描-未填写shodan api秘钥')
    check = False
else:
    API = shodan.Shodan(PortScan.shodan_api)
    try:
        time.sleep(1)
        API.info()
    except shodan.exception.APIError as e:
        print(f'[-]端口扫描-shodan api秘钥错误:{e}')
        check = False
    except Exception as e:
        print(f'[-]端口扫描-shodan api接口异常：{e}')
        check = False

def Scan(ip):
    print(f'[+]端口扫描-开始shodan端口扫描')
    try:
        ipinfo = API.host(ip)
    except Exception as e:
        print(f'[-]端口扫描-shodan查询{ip}失败，原因:{e}')
        return None, None
    port_list = ipinfo.get('ports', None)
    vulns_list = ipinfo.get('vulns', None)
    if port_list:
        print(f'[+]端口扫描-shodan端口扫描[{ip}]完成:{port_list}')
        return port_list, vulns_list
    else:
        return None, None

if __name__ == '__main__':
    port_list, vulns_list = Scan('123.147.194.210')
    print(port_list, vulns_list)