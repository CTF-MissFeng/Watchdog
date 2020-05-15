'''探测端口是否为HTTP服务，在加入到web资产表'''
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../../')

import requests
import chardet
from bs4 import BeautifulSoup
import random
import ipaddress
from concurrent import futures
import time
from urllib.parse import urlparse
import threading

from client.database import session, SrcPorts, SrcAssets
from client.webinfo.run import SelectIP, Check_Waf

requests.packages.urllib3.disable_warnings()
LOCK = threading.RLock()
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/68.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) '
    'Gecko/20100101 Firefox/68.0',
    'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/68.0']

class UrlProbe:

    def __init__(self, ip_dict):
        '''{'ip': 'xxx', 'port': 123}'''
        self.ip_dict = ip_dict

    def _gen_random_ip(self):
        """生成随机的点分十进制的IP字符串"""
        while True:
            ip = ipaddress.IPv4Address(random.randint(0, 2 ** 32 - 1))
            if ip.is_global:
                return ip.exploded

    def _gen_fake_header(self):
        """生成伪造请求头"""
        ua = random.choice(user_agents)
        ip = self._gen_random_ip()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,'
                      'application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Referer': 'https://www.google.com/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': ua,
            'X-Forwarded-For': ip,
            'X-Real-IP': ip
        }
        return headers

    def _check_http(self):
        '''HTTP服务探测'''
        url = f"http://{self.ip_dict['ip']}:{self.ip_dict['port']}"
        headers = self._gen_fake_header()
        try:
            response = requests.get(url, timeout=20, headers=headers)
        except requests.exceptions.SSLError:
            url = f"https://{self.ip_dict['ip']}:{self.ip_dict['port']}"
            try:
                response = requests.get(url, timeout=20, verify=False, headers=headers)
            except Exception as e:
                return None
            else:
                return response
        except Exception as e:
            return None
        else:
            return response

    def _get_banner(self, headers):
        server = headers.get('Server')
        Powered = headers.get('X-Powered-By')
        if server or Powered:
            return f'{server},{Powered}'
        else:
            return ''

    def _get_title(self, markup):
        '''获取网页标题'''
        try:
            soup = BeautifulSoup(markup, 'lxml')
        except:
            return None
        title = soup.title
        if title:
            return title.text.strip()
        h1 = soup.h1
        if h1:
            return h1.text.strip()
        h2 = soup.h2
        if h2:
            return h2.text.strip()
        h3 = soup.h3
        if h2:
            return h3.text.strip()
        desc = soup.find('meta', attrs={'name': 'description'})
        if desc:
            return desc['content'].strip()
        word = soup.find('meta', attrs={'name': 'keywords'})
        if word:
            return word['content'].strip()
        if len(markup) <= 200:
            return markup.strip()
        text = soup.text
        if len(text) <= 200:
            return text.strip()
        return None

    def run(self):
        print(f'[+]URL开始探测:[{self.ip_dict}]')
        response = self._check_http()
        if response == None:  # 非HTTP服务
            print(f'[-]URL探测:[{self.ip_dict}]非HTTP服务')
            return None
        if response.status_code == 200:
            mychar = chardet.detect(response.content)
            bianma = mychar['encoding']  # 自动识别编码
            response.encoding = bianma
            title = self._get_title(markup=response.text)
            banner = self._get_banner(response.headers)
            assets_dict = self.ip_dict
            assets_dict['title'] = title
            assets_dict['banner'] = banner
            assets_dict['host'] = response.url
            return assets_dict
        else:
            print(f'[-]URL探测:[{self.ip_dict}]状态码非200')
            return None

def ReadPorts():
    '''读取端口数据'''
    port_sql = session.query(SrcPorts).filter(SrcPorts.port_url_scan == False).limit(10).all()
    session.commit()
    if port_sql:
        for port in port_sql:
            port.port_url_scan = True
            session.add(port)
            try:
                session.commit()
            except Exception as error:
                print(f'[-]URL扫描-修改端口扫描状态异常{error}')
            else:
                session.refresh(port, ['port_url_scan'])
    return port_sql

def WriteAsset(http_info, port_sql):
    LOCK.acquire()
    asset_count = session.query(SrcAssets).filter(SrcAssets.asset_host == http_info['host']).count()
    session.commit()
    if not asset_count:
        srcasset_sql = SrcAssets(asset_name=port_sql.port_name, asset_host=http_info['host'],
                                 asset_subdomain=http_info['subdomain'],
                                 asset_title=http_info['title'],
                                 asset_ip=port_sql.port_ip, asset_area=http_info['area'], asset_waf=http_info['waf'],
                                 asset_cdn=False,
                                 asset_banner=http_info['banner'], asset_info='', asset_whois='')
        session.add(srcasset_sql)
        try:
            session.commit()
        except Exception as error:
            session.rollback()
            print(f'[-]Url探测-子域名入库异常{error}')
        finally:
            LOCK.release()
    else:
        LOCK.release()

def main():
    print('[+]URL扫描启动')
    pool = futures.ThreadPoolExecutor(max_workers=10)
    while True:
        port_sql = ReadPorts()
        if not port_sql:
            time.sleep(30)
        else:
            wait_for = [pool.submit(action, sql_port) for sql_port in port_sql]
            for f in futures.as_completed(wait_for):
                f.result()

def action(sql_port):
    if sql_port.port_port == 80:
        return None
    try:
        host = urlparse(sql_port.port_host)
    except:
        return None
    host = host.netloc
    print(f'[+]URL开始探测:{host}:{sql_port.port_port}')
    ip_dict = {'ip': host, 'port': sql_port.port_port}
    http_info = UrlProbe(ip_dict)
    info = http_info.run()
    if info:
        area = SelectIP(sql_port.port_ip)
        flag, waf = Check_Waf(info['host'])
        info['area'] = area
        info['waf'] = waf
        info['subdomain'] = host
        WriteAsset(info, sql_port)


if __name__ == '__main__':
    main()