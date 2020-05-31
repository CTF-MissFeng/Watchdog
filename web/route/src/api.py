from flask_restful import reqparse, Resource
from flask import session, json, redirect, url_for, escape, send_file
from urllib.parse import quote
import os

from web.utils.logs import logger
from web.models import SrcCustomer, SrcTask, SrcPorts, SrcAssets, SrcVul
from web import DB
from web.utils.auxiliary import addlog, WriteWebAssetsExcel, WriteWebPortExcel

class SrcCustomerAPI(Resource):
    '''src 厂商管理类'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("cus_name", type=str, location='json')
        self.parser.add_argument("cus_home", type=str, location='json')
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)

    def put(self):
        '''添加厂商'''

        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_cus_name = args.cus_name
        key_cus_home = args.cus_home
        src_customer_query = SrcCustomer.query.filter(SrcCustomer.cus_name == key_cus_name).first()
        if src_customer_query:
            return {'status_code': 201, 'msg': f'已存在[{key_cus_name}]厂商名'}
        src_customer_query = SrcCustomer(key_cus_name, key_cus_home)
        DB.session.add(src_customer_query)
        try:
            DB.session.commit()
        except Exception as e:
            logger.log('ALERT', '厂商添加接口SQL错误:%s' % e)
            DB.session.rollback()
            return {'status_code': 500, 'msg': '添加厂商失败，原因:SQL错误'}
        addlog(session.get('username'), session.get('login_ip'), f'[{key_cus_name}]厂商添加成功')
        logger.log('INFOR', f'[{key_cus_name}]厂商添加成功')
        return {'status_code': 200, 'msg': '添加厂商成功'}

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = SrcCustomer.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = SrcCustomer.query.limit(20).offset(0).all()
            else:
                paginate = SrcCustomer.query.limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = SrcCustomer.query.limit(20).offset(0).all()
            else:
                if 'cus_name' not in search_dict or 'cus_home' not in search_dict:  # 查询参数有误
                    paginate = SrcCustomer.query.limit(20).offset(0).all()
                else:
                    paginate1 = SrcCustomer.query.filter(
                        SrcCustomer.cus_name.like("%" + search_dict['cus_name'] + "%"),
                        SrcCustomer.cus_home.like("%" + search_dict['cus_home'] + "%"),
                    )
                    paginate = paginate1.limit(key_limit).offset((key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['cus_name'] = i.cus_name
                data1['cus_home'] = i.cus_home
                data1['cus_time'] = i.cus_time
                data1['cus_number'] = len(i.src_assets)
                data1['cus_number_port'] = len(i.src_ports)
                num = 0
                if len(i.src_task) > 0:
                    for j in i.src_task:
                        if not j.task_flag:
                            num += 1
                data1['cus_number_task'] = num
                num = 0
                if len(i.src_assets) > 0:
                    for j in i.src_assets:
                        if not j.asset_xray_flag:
                            num += 1
                data1['cus_number_vul'] = num
                data.append(data1)
                index += 1
            jsondata.update({'data': data})
            return jsondata
        else:
            jsondata = {'code': 0, 'msg': '', 'count': 0}
            jsondata.update({'data': []})
            return jsondata

    def delete(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_cus_name = args.cus_name
        user_query = SrcCustomer.query.filter(SrcCustomer.cus_name == key_cus_name).first()
        if not user_query:  # 删除的厂商不存在
            addlog(session.get('username'), session.get('login_ip'), f'删除厂商:[{key_cus_name}] 失败，原因:该厂商不存在')
            return {'status_code': 500, 'msg': '删除厂商失败，无此厂商'}
        DB.session.delete(user_query)
        try:
            DB.session.commit()
        except:
            DB.session.rollback()
            return {'status_code': 500, 'msg': '删除厂商失败，SQL错误'}
        addlog(session.get('username'), session.get('login_ip'), f'删除厂商:[{key_cus_name}] 成功')
        return {'status_code': 200, 'msg': '删除厂商成功'}

class SrcTaskAPI(Resource):
    '''src 资产任务管理'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("task_name", type=str, location='json')
        self.parser.add_argument("task_domain", type=str, location='json')
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)

    def put(self):
        '''添加任务资产'''
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_task_name = args.task_name
        key_task_domain = args.task_domain
        src_task_query = SrcCustomer.query.filter(SrcCustomer.cus_name == key_task_name).first()
        if not src_task_query:
            return {'status_code': 201, 'msg': f'不存在[{key_task_name}]厂商名，请检查'}
        domain_list = list(set(key_task_domain.split()))  # 过滤重复内容
        for domain in domain_list:
            domain1 = domain.strip()
            if domain1:
                srctask_sql = SrcTask.query.filter(SrcTask.task_domain == domain1).first()  # 过滤已有重复任务
                if srctask_sql:
                    continue
                src_task_queryadd = SrcTask(key_task_name, domain1)
                DB.session.add(src_task_queryadd)
        try:
            DB.session.commit()
        except Exception as e:
            logger.log('ALERT', '资产任务添加接口SQL错误:%s' % e)
            DB.session.rollback()
            return {'status_code': 500, 'msg': f'添加资产任务失败，可能已存在该任务资产，原因:{e}'}
        addlog(session.get('username'), session.get('login_ip'), f'添加任务资产[{key_task_name}]：[{len(domain_list)}]个')
        logger.log('INFOR', f'添加任务资产[{len(domain_list)}]个')
        return {'status_code': 200, 'msg': '添加厂商成功'}

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = SrcTask.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = SrcTask.query.order_by(SrcTask.id.desc()).limit(20).offset(0).all()
            else:
                paginate = SrcTask.query.order_by(SrcTask.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = SrcTask.query.order_by(SrcTask.id.desc()).limit(20).offset(0).all()
            else:
                if 'task_name' not in search_dict or 'task_domain' not in search_dict:  # 查询参数有误
                    paginate = SrcTask.query.order_by(SrcTask.id.desc()).limit(20).offset(0).all()
                else:
                    paginate1 = SrcTask.query.filter(
                        SrcTask.task_name.like("%" + search_dict['task_name'] + "%"),
                        SrcTask.task_domain.like("%" + search_dict['task_domain'] + "%"),
                    )
                    paginate = paginate1.order_by(SrcTask.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['task_name'] = i.task_name
                data1['task_domain'] = i.task_domain
                if i.task_flag:
                    data1['task_flag'] = '已探测'
                else:
                    data1['task_flag'] = '未探测'
                data1['task_time'] = i.task_time
                data.append(data1)
                index += 1
            jsondata.update({'data': data})
            return jsondata
        else:
            jsondata = {'code': 0, 'msg': '', 'count': 0}
            jsondata.update({'data': []})
            return jsondata

    def delete(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_task_domain = args.task_domain
        user_query = SrcTask.query.filter(SrcTask.task_domain == key_task_domain).first()
        if not user_query:  # 删除的任务不存在
            addlog(session.get('username'), session.get('login_ip'), f'删除资产[{key_task_domain}]任务失败，原因:该任务不存在')
            return {'status_code': 500, 'msg': '删除资产任务失败，此任务不存在'}
        DB.session.delete(user_query)
        try:
            DB.session.commit()
        except:
            DB.session.rollback()
            return {'status_code': 500, 'msg': '删除资产任务失败，SQL错误'}
        addlog(session.get('username'), session.get('login_ip'), f'删除资产任务[{key_task_domain}]成功')
        return {'status_code': 200, 'msg': '删除资产任务成功'}

class SrcPortAPI(Resource):
    '''src 端口服务管理'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)
        self.parser.add_argument("id", type=str)

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        if args.id:
            save_path = WriteWebPortExcel()
            filename = quote(f'端口服务资产表.xlsx')
            rv = send_file(save_path, as_attachment=True, attachment_filename=filename)
            rv.headers['Content-Disposition'] += "; filename*=utf-8''{}".format(filename)
            os.remove(save_path)
            return rv
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = SrcPorts.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = SrcPorts.query.order_by(SrcPorts.id.desc()).limit(20).offset(0).all()
            else:
                paginate = SrcPorts.query.order_by(SrcPorts.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = SrcPorts.query.order_by(SrcPorts.id.desc()).limit(20).offset(0).all()
            else:
                if 'port_name' not in search_dict or 'port_ip' not in search_dict or 'port_port' not in search_dict or 'port_service' not in search_dict:  # 查询参数有误
                    paginate = SrcPorts.query.order_by(SrcPorts.id.desc()).limit(20).offset(0).all()
                else:
                    paginate1 = SrcPorts.query.filter(
                        SrcPorts.port_name.like("%" + search_dict['port_name'] + "%"),
                        SrcPorts.port_ip.like("%" + search_dict['port_ip'] + "%"),
                        SrcPorts.port_port.like("%" + search_dict['port_port'] + "%"),
                        SrcPorts.port_service.like("%" + search_dict['port_service'] + "%")
                    )
                    paginate = paginate1.order_by(SrcPorts.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['port_name'] = i.port_name
                data1['port_host'] = i.port_host
                data1['port_ip'] = i.port_ip
                data1['port_port'] = i.port_port
                data1['port_service'] = i.port_service
                data1['port_product'] = i.port_product
                data1['port_version'] = i.port_version
                data1['port_brute'] = i.port_brute
                data1['port_url_scan'] = i.port_url_scan
                data1['port_time'] = i.port_time
                data.append(data1)
                index += 1
            jsondata.update({'data': data})
            return jsondata
        else:
            jsondata = {'code': 0, 'msg': '', 'count': 0}
            jsondata.update({'data': []})
            return jsondata

class SrcUrlAPI(Resource):
    '''src 资产管理'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)
        self.parser.add_argument("urls", type=str, location='json')
        self.parser.add_argument("id", type=str)

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        if args.id:
            save_path = WriteWebAssetsExcel()
            filename = quote(f'web资产表.xlsx')
            rv = send_file(save_path, as_attachment=True, attachment_filename=filename)
            rv.headers['Content-Disposition'] += "; filename*=utf-8''{}".format(filename)
            os.remove(save_path)
            return rv
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = SrcAssets.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = SrcAssets.query.order_by(SrcAssets.id.desc()).limit(20).offset(0).all()
            else:
                paginate = SrcAssets.query.order_by(SrcAssets.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = SrcAssets.query.order_by(SrcAssets.id.desc()).limit(20).offset(0).all()
            else:
                if 'asset_name' not in search_dict or 'asset_host' not in search_dict or 'asset_ip' not in search_dict or 'asset_banner' not in search_dict:  # 查询参数有误
                    paginate = SrcAssets.query.order_by(SrcAssets.id.desc()).limit(20).offset(0).all()
                else:
                    paginate1 = SrcAssets.query.filter(
                        SrcAssets.asset_name.like("%" + search_dict['asset_name'] + "%"),
                        SrcAssets.asset_host.like("%" + search_dict['asset_host'] + "%"),
                        SrcAssets.asset_ip.like("%" + search_dict['asset_ip'] + "%"),
                        SrcAssets.asset_banner.like("%" + search_dict['asset_banner'] + "%")
                    )
                    paginate = paginate1.order_by(SrcAssets.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['asset_name'] = i.asset_name
                data1['asset_host'] = i.asset_host
                data1['asset_title'] = escape(i.asset_title)
                data1['asset_ip'] = i.asset_ip
                data1['asset_area'] = i.asset_area
                data1['asset_waf'] = i.asset_waf
                data1['asset_banner'] = escape(i.asset_banner)
                data1['asset_xray_flag'] = i.asset_xray_flag
                data1['asset_burp_flag'] = i.asset_burp_flag
                data1['asset_time'] = i.asset_time
                data.append(data1)
                index += 1
            jsondata.update({'data': data})
            return jsondata
        else:
            jsondata = {'code': 0, 'msg': '', 'count': 0}
            jsondata.update({'data': []})
            return jsondata

    def delete(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_scan_dict = args.urls.replace("'", '"')
        try:
            key_scan_dict = json.loads(key_scan_dict)
        except:
            return {'status_code': 500, 'msg': '删除资产失败'}
        for key, value in key_scan_dict.items():
            url_query = SrcAssets.query.filter(SrcAssets.asset_time == key_scan_dict[key]['time']).first()
            if not url_query:
                continue
            else:
                DB.session.delete(url_query)
        try:
            DB.session.commit()
        except Exception as e:
            DB.session.rollback()
            logger.log('ALERT', f'批量删除资产失败,{e}')
            return {'status_code': 500, 'msg': '删除资产失败'}
        addlog(session.get('username'), session.get('login_ip'), f'批量删除资产成功')
        logger.log('INFOR', f'批量删除资产成功')
        return {'status_code': 200, 'msg': '删除资产成功'}

class SrcVulAPI(Resource):
    '''src 漏洞管理'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)
        self.parser.add_argument("vlus", type=str, location='json')

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = SrcVul.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = SrcVul.query.order_by(SrcVul.id.desc()).limit(20).offset(0).all()
            else:
                paginate = SrcVul.query.order_by(SrcVul.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = SrcVul.query.order_by(SrcVul.id.desc()).limit(20).offset(0).all()
            else:
                if 'vul_url' not in search_dict or 'vul_plugin' not in search_dict:  # 查询参数有误
                    paginate = SrcVul.query.order_by(SrcVul.id.desc()).limit(20).offset(0).all()
                else:
                    paginate1 = SrcVul.query.filter(
                        SrcVul.vul_url.like("%" + search_dict['vul_url'] + "%"),
                        SrcVul.vul_plugin.like("%" + search_dict['vul_plugin'] + "%")
                    )
                    paginate = paginate1.order_by(SrcVul.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['vul_subdomain'] = i.vul_subdomain
                data1['vul_plugin'] = i.vul_plugin
                data1['vul_flag'] = i.vul_flag
                data1['vul_url'] = escape(i.vul_url)
                data1['vul_payload'] = escape(i.vul_payload)
                if i.vul_raw:
                    data1['vul_raw'] = i.vul_raw.replace('\n', '<br/>')
                else:
                    data1['vul_raw'] = ''
                data1['vul_scan_name'] = i.vul_scan_name
                data1['vul_time'] = i.vul_time
                data.append(data1)
                index += 1
            jsondata.update({'data': data})
            return jsondata
        else:
            jsondata = {'code': 0, 'msg': '', 'count': 0}
            jsondata.update({'data': []})
            return jsondata

    def put(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_scan_dict = args.vlus.replace("'", '"')
        try:
            key_scan_dict = json.loads(key_scan_dict)
        except:
            return {'status_code': 500, 'msg': '标记更新失败'}
        for key, value in key_scan_dict.items():
            url_query = SrcVul.query.filter(SrcVul.vul_time == key_scan_dict[key]['time']).first()
            if not url_query:
                continue
            else:
                url_query.vul_flag = True
                DB.session.add(url_query)
        try:
            DB.session.commit()
        except Exception as e:
            DB.session.rollback()
            logger.log('ALERT', f'批量标记漏洞任务失败,{e}')
            return {'status_code': 500, 'msg': '更新标记失败'}
        addlog(session.get('username'), session.get('login_ip'), f'批量更新漏洞标记成功')
        logger.log('INFOR', f'批量更新漏洞标记成功')
        return {'status_code': 200, 'msg': '更新标记成功，请刷新'}

    def delete(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_scan_dict = args.vlus.replace("'", '"')
        try:
            key_scan_dict = json.loads(key_scan_dict)
        except:
            return {'status_code': 500, 'msg': '删除漏洞失败'}
        for key, value in key_scan_dict.items():
            url_query = SrcVul.query.filter(SrcVul.vul_time == key_scan_dict[key]['time']).first()
            if not url_query:
                continue
            else:
                DB.session.delete(url_query)
        try:
            DB.session.commit()
        except Exception as e:
            DB.session.rollback()
            logger.log('ALERT', f'批量删除漏洞任务失败,{e}')
            return {'status_code': 500, 'msg': '删除漏洞失败'}
        addlog(session.get('username'), session.get('login_ip'), f'批量删除漏洞成功')
        logger.log('INFOR', f'批量删除漏洞成功')
        return {'status_code': 200, 'msg': '删除漏洞成功'}