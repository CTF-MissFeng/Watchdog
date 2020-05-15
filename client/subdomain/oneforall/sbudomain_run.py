import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../../')

import pkgutil
import json
import time
import datetime
import socket

from client.database import session, SrcTask, SrcAssets
from client.subdomain.oneforall.oneforall import OneForAll as OneForAll
from client.webinfo.run import SelectIP, Check_Waf
from client.urlscan.url_probe.urlscan_run import UrlProbe

class SubDomain:

    def __init__(self, host):
        self.host = host.replace('*.', '')

    def run(self):
        OneForAll(self.host).run()

    def pars_dns(self):
        try:
            data_bytes = pkgutil.get_data('client.subdomain.oneforall', f'results/{self.host}.json')
        except Exception as error:
            print(f'[-]子域名[{self.host}]扫描-读取结果失败,{error}')
        else:
            data_str = data_bytes.decode('utf-8')
            try:
                dns_dict = json.loads(data_str)
            except Exception as error:
                print(f'[-]子域名[{self.host}]扫描-解析结果失败,{error}')
            else:
                return dns_dict

def ReadTask():
    '''读取任务'''
    task_sql = session.query(SrcTask).filter(SrcTask.task_flag == False).first()
    session.commit()  # 提交事务，刷新查询缓存
    if task_sql:
        task_sql.task_flag = True  # 修改任务状态
        task_sql.task_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        session.refresh(task_sql, ['task_flag'])
    return task_sql

def WriteAssets(dns_list, task_name):
    for info in dns_list:
        ip = info.get('content', '')
        try:
            if ip.find(','):
                ip = ip.split(',')[0]
        except Exception as e:
            print(f'[-]子域名多IP获取失败:{e}')
        host = info.get('url', None)
        status = info.get('status', None)
        if ip and host and status:
            asset_count = session.query(SrcAssets).filter(SrcAssets.asset_host == host).count()
            session.commit()
            if not asset_count:
                area = SelectIP(ip)
                flag, waf = Check_Waf(host)
                srcasset_sql = SrcAssets(asset_name=task_name, asset_host=host, asset_subdomain=info.get('subdomain'),
                                         asset_title=info.get('title'),
                                         asset_ip=ip, asset_area=area, asset_waf=waf, asset_cdn=False,
                                         asset_banner=info.get('banner'), asset_info='', asset_whois='')
                session.add(srcasset_sql)
                try:
                    session.commit()
                except Exception as error:
                    session.rollback()
                    print(f'[-]子域名入库异常{error}')
    print(f'[+]子域名[{task_name}]入库完成')

def main():
    print(f'[+]子域名扫描启动')
    while True:
        task_sql = ReadTask()
        if not task_sql:
            time.sleep(30)
        else:
            if task_sql.task_domain.startswith('*'):
                subdomain = SubDomain(task_sql.task_domain)
                subdomain.run()
                dns_list = subdomain.pars_dns()
                if dns_list:
                    WriteAssets(dns_list, task_sql.task_name)
            else:
                subdomain_scan(task_sql.task_domain, task_sql.task_name)

def subdomain_scan(host, asset_name):
    '''host探测'''
    ip = domain_ip(host)
    if not ip:
        return None
    ip_dict = {'ip': host, 'port': 80}
    http_info = UrlProbe(ip_dict)
    info = http_info.run()
    if not info:
        return None
    area = SelectIP(ip)
    flag, waf = Check_Waf(info['host'])
    info['area'] = area
    info['waf'] = waf
    info['subdomain'] = host
    info['ip'] = ip
    print('[+]Url探测完成')
    WriteAsset(info, asset_name)

def domain_ip(subdomain):
    '''域名转IP'''
    try:
        ip =socket.gethostbyname(subdomain)
    except:
        return None
    else:
        return ip

def WriteAsset(http_info, asset_name):
    asset_count = session.query(SrcAssets).filter(SrcAssets.asset_host == http_info['host']).count()
    if not asset_count:
        srcasset_sql = SrcAssets(asset_name=asset_name, asset_host=http_info['host'],
                                 asset_subdomain=http_info['subdomain'],
                                 asset_title=http_info['title'],
                                 asset_ip=http_info['ip'], asset_area=http_info['area'], asset_waf=http_info['waf'],
                                 asset_cdn=False,
                                 asset_banner=http_info['banner'], asset_info='', asset_whois='')
        session.add(srcasset_sql)
        try:
            session.commit()
        except Exception as error:
            session.rollback()
            print(f'[-]Url探测-子域名入库异常{error}')

if __name__ == '__main__':
    main()