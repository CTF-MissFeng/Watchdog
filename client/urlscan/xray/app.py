from flask import Flask, request
from urllib.parse import urlparse

from client.database import session, SrcVul

app = Flask(__name__)

NUM_SCAN = 1

@app.route('/webhook', methods=['POST'])
def xray_webhook():
    try:
        vuln = request.json

    except:
        pass
    else:
        if 'create_time' in str(vuln):
            plugin = vuln['data']['plugin']
            url = vuln['data']['detail']['addr']
            payload = vuln['data']['detail']['payload']
            raws = vuln['data']['detail']['snapshot'][0][0]

            print(f'Xray新漏洞：[{plugin}]-{url}')
            WriteVul(plugin, url, payload, raws, scan_name='xray')
        else:
            if 'num_found_urls' in str(vuln):
                num_found_urls = vuln['data']['num_found_urls']
                num_scanned_urls = vuln['data']['num_scanned_urls']
                pending = int(num_found_urls) - int(num_scanned_urls)
                global NUM_SCAN
                NUM_SCAN = pending
                print(f'Xray当前队列[{NUM_SCAN}]')
    finally:
        return str(NUM_SCAN)

def WriteVul(plugin, url, payload, raw, scan_name):
    '''漏洞入库'''
    try:
        host = urlparse(url).hostname
    except Exception as e:
        print(f'Xray解析url格式失败:{url}')
        host = ''
    else:
        vul_sql = SrcVul(vul_subdomain=host, vul_plugin=plugin, vul_url=url, vul_payload=payload, vul_raw=raw,
                         vul_scan_name=scan_name)
        session.add(vul_sql)
        try:
            session.commit()
        except Exception as e:
            print(f'xray漏洞入库失败:{e}')
        else:
            print(f'Xray漏洞入库成功:{url}')

def main():
    app.run(port=8899)

if __name__ == '__main__':
    main()