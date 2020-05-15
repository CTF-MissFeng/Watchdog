import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')
import time

from client.portscan.ShodanScan import Scan
from client.portscan.NmapScan import Nmap_Portscan
from client.database import session, SrcAssets, SrcPorts

class PortScan:

    def __init__(self, ip):
        self.ip = ip

    def run(self):
        port_list, vulns_list = Scan(ip=self.ip)
        port_dict = Nmap_Portscan(ip=self.ip, port_info_list=port_list)
        return port_dict, vulns_list

def ReadAssets():
    '''读取资产数据'''
    assets_sql = session.query(SrcAssets).filter(SrcAssets.asset_port_flag == False).first()
    session.commit()
    if assets_sql:
        ip = assets_sql.asset_ip
        assets_sql1 = session.query(SrcAssets).filter(SrcAssets.asset_ip == ip).all()
        for sql in assets_sql1:
            sql.asset_port_flag = True
            session.add(sql)
        try:
            session.commit()
        except Exception as error:
            print(f'[-]端口扫描-修改IP扫描状态异常{error}')
            session.rollback()
    return assets_sql

def WritePosts(port_dict, assets_sql):
    '''端口扫描入库'''
    for info in port_dict:
        port_sql = SrcPorts(port_name=assets_sql.asset_name, port_host=assets_sql.asset_host, port_ip=assets_sql.asset_ip,
                            port_port=port_dict[info]['port'], port_service=port_dict[info]['name'],
                            port_product=port_dict[info]['product'], port_version=port_dict[info]['version'])
        session.add(port_sql)
        try:
            session.commit()
        except Exception as error:
            session.rollback()
            print(f'[-]端口入库异常{error}')
    print(f'[+]端口[{assets_sql.asset_ip}]入库完成')

def main():
    print('[+]端口扫描启动')
    while True:
        assets_sql = ReadAssets()
        if not assets_sql:
            time.sleep(30)
        else:
            portscan = PortScan(assets_sql.asset_ip)
            port_dict, vulns_list = portscan.run()
            if port_dict:
                WritePosts(port_dict, assets_sql)

if __name__ == '__main__':
    main()