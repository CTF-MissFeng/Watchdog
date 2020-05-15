import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')

import ipdb
from pathlib import Path

from client.webinfo.wafw00f.main import main1 as WafMain

ipdata = Path(__file__).parent.joinpath('ipdata.ipdb')
if not ipdata.is_file():
    print('[-]web信息收集-ipdata.ipdb IP数据库不存在')
    exit(0)
else:
    IPDB = ipdb.City(ipdata.resolve())

def SelectIP(ip):
    '''查询IP归属地'''
    try:
        result = IPDB.find_map(ip, 'CN')
    except Exception as e:
        print(f'{ip}查询归属地失败:{e}')
        return ''
    else:
        if result['region_name'] == result['city_name']:
            ipinfo = result['country_name'] + result['region_name'] + result['isp_domain']
        else:
            ipinfo = result['country_name'] + result['region_name'] + result['city_name'] + result['isp_domain']
        return ipinfo

def Check_Waf(host):
    '''waf检测'''
    info = WafMain(host)
    return info





if __name__ == '__main__':
    Check_Waf('https://www.189.cn')