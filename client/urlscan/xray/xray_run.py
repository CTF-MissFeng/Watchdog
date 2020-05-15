import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../../')

import pathlib
import subprocess
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import time

from client.database import session, SrcAssets, SrcTask
from client.subdomain.oneforall.config import crawlergo
from client.urlscan.xray.app import main as web_main, NUM_SCAN

crawlergo_path = str(pathlib.Path(__file__).parent.joinpath(crawlergo.crawlergo_path).resolve())

def ReadAssets():
    '''读取一条资产数据'''
    assets_sql = session.query(SrcAssets).filter(SrcAssets.asset_xray_flag == False).first()
    session.commit()
    if assets_sql:
        assets_sql.asset_xray_flag = True
        session.add(assets_sql)
        try:
            session.commit()
        except Exception as error:
            print(f'[-]Xray扫描-修改扫描状态异常{error}')
            session.rollback()
        else:
            session.refresh(assets_sql, ['asset_xray_flag'])
    return assets_sql

def action(assets_sql):
    '''子程序执行'''
    target = assets_sql.asset_host
    task_name = assets_sql.asset_name
    cmd = [crawlergo_path, "-c", crawlergo.chromium_path, "-o", "json", '-t', crawlergo.max_tab_count, '-f',
           crawlergo.filter_mode, '-m', crawlergo.max_crawled_count, '--push-pool-max', '4', '--fuzz-path', "--push-to-proxy", "http://127.0.0.1:7778/", target]
    rsp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = rsp.communicate()
    try:
        result = json.loads(output.decode().split("--[Mission Complete]--")[1])
        #req_list = result["req_list"]
        req_subdomain = result["sub_domain_list"]
    except Exception as e:
        print('ALERT', '爬虫异常:%s' % e)
    else:
        WriteTask(req_subdomain, task_name)
    finally:
        print(f'{target}爬虫完毕')

def WriteTask(dns_list, task_name):
    '''爬虫获取的子域名再次入任务管理库'''
    if dns_list:
        for dns in dns_list:
            assets_sql = session.query(SrcAssets).filter(SrcAssets.asset_subdomain == dns).count()
            session.commit()
            if assets_sql:  # 过滤已有子域名
                continue
            task_sql = SrcTask(task_name=task_name, task_domain=dns)
            session.add(task_sql)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                print('ALERT', '爬虫子域名入库异常:%s' % e)
        print('[+]爬虫子域名入库完成')

def xray_main():
    xraypath = str(pathlib.Path(__file__).parent.resolve()) + '/./' + crawlergo.xray_path
    cmd = [xraypath, "webscan", "--listen", "127.0.0.1:7778", "--webhook-output", "http://127.0.0.1:8899/webhook"]
    try:
        completed = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as err:
        print('[-]xray ERROR:', err)
    else:
        print(completed.returncode)

def crawlergo_main():
    print('[+]爬虫服务启动')
    pool = ThreadPoolExecutor(max_workers=1)
    while True:
        if NUM_SCAN > 2500:
            time.sleep(30)
            print('[-]xray当前队列过多，等待扫描完')
            continue
        assets_sql = ReadAssets()
        if not assets_sql:
            time.sleep(30)
        else:
            print(f'{assets_sql.asset_host}开始爬虫')
            futurel = pool.submit(action, assets_sql)
            req_result = futurel.result()

def main():
    # 启动flask
    web = threading.Thread(target=web_main)
    web.start()
    time.sleep(2)
    # 启动Xray漏洞扫描器
    scanner = threading.Thread(target=xray_main)
    scanner.setDaemon(True)
    scanner.start()
    time.sleep(2)
    # 启动爬虫
    crawlergo_main()


if __name__ == '__main__':
    main()