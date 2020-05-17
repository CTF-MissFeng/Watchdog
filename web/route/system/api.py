from flask_restful import reqparse, Resource
from flask import session, request, json, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from web.utils.logs import logger
from web.models import User, UserLoginLogs, UserLogs, MailSetting
from web import DB, APP
from web.utils.auxiliary import addlog, SMail

class UserLogin(Resource):
    '''user login类'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("username", type=str, required=True, location='json')
        self.parser.add_argument("password", type=str, required=True, location='json')
        self.parser.add_argument("rememberme", type=bool, location='json')

    def post(self):
        '''登录接口'''
        args = self.parser.parse_args()
        key_username = args.username
        key_password = args.password
        key_remember = args.rememberme
        try:  # 获取客户端IP地址
            login_ip = request.headers['X-Forwarded-For'].split(',')[0]
        except:
            login_ip = request.remote_addr
        user_query = User.query.filter(User.username == key_username).first()
        if not user_query:  # 若不存在此用户
            logger.log('INFOR', f'用户登录接口-用户[{key_username}]登录失败，原因：用户名不存在，IP:{login_ip}')
            return {'status_code': 201, 'msg': '用户名或密码错误'}
        if check_password_hash(user_query.password, key_password):  # 进行密码核对
            session['status'] = True  # 登录成功设置session
            session['username'] = key_username
            session['login_ip'] = login_ip
            useragent = request.user_agent.string
            userlogins = UserLoginLogs(username=key_username, login_ip=login_ip, useragent=useragent)
            try:
                DB.session.add(userlogins)
                DB.session.commit()
            except Exception as e:
                logger.log('ALERT', f'用户登录接口-SQL错误:{e}')
                DB.session.rollback()
            logger.log('INFOR', f'用户登录接口-用户[{key_username}]登录成功，IP:{login_ip}')
            addlog(key_username, login_ip, '登录系统成功')
            if key_remember:  # 若选择了记住密码选项
                session.permanent = True
                APP.permanent_session_lifetime = datetime.timedelta(weeks=7)  # 设置session到期时间7天
            return {'status_code': 200}
        else:
            logger.log('INFOR', f'用户登录接口-用户[{key_username}]登录失败，原因:密码错误;IP{login_ip}')
            addlog(key_username, login_ip, '登录失败，原因:密码错误')
            return {'status_code': 201, 'msg': '用户名或密码错误'}

class UserSetting(Resource):
    '''user 修改用户资料类'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("phone", type=str, required=True, location='json')
        self.parser.add_argument("email", type=str, required=True, location='json')
        self.parser.add_argument("remark", type=str, location='json')

    def post(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_phone = args.phone
        key_email = args.email
        key_remark = args.remark
        user_query = User.query.filter(User.username == session.get('username')).first()
        if not user_query:
            addlog(session.get('username'), session.get('login_ip'), '修改用户资料失败，原因:越权修改其他用户')
            return {'status_code': 500, 'msg': '禁止越权修改用户信息'}
        user_query.phone = key_phone
        user_query.email = key_email
        if key_remark:
            user_query.remark = key_remark
        try:
            DB.session.commit()
        except Exception as e:
            logger.log('ALERT', f'用户修改资料接口SQL错误:{e}')
            DB.session.rollback()
            addlog(session.get('username'), session.get('login_ip'), '修改用户资料失败，原因:SQL错误')
            return {'status_code': 500, 'msg': '修改用户资料失败，SQL出错'}
        addlog(session.get('username'), session.get('login_ip'), '修改用户资料成功')
        logger.log('INFOR', f"[{session.get('username')}]修改用户资料成功")
        return {'status_code': 200}

class UserPassword(Resource):
    '''user 修改用户密码类'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("old_password", type=str, required=True, location='json')
        self.parser.add_argument("new_password", type=str, required=True, location='json')
        self.parser.add_argument("again_password", type=str, required=True, location='json')

    def post(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_old_password = args.old_password
        key_new_password = args.new_password
        key_again_password = args.again_password
        if key_new_password != key_again_password:
            return {'status_code': 201, 'msg': '两次输入的新密码不一致'}
        if key_old_password == key_new_password:
            return {'status_code': 201, 'msg': '新密码不能和旧密码一致'}
        user_query = User.query.filter(User.username == session.get('username')).first()
        if not user_query:
            addlog(session.get('username'), session.get('login_ip'), '修改用户密码失败，原因:不存在此账户')
            return {'status_code': 201, 'msg': '修改密码失败，session失效'}
        if not check_password_hash(user_query.password, key_old_password):  # 检测原密码
            addlog(session.get('username'), session.get('login_ip'), '修改用户密码失败，原因:原密码不正确')
            return {'status_code': 201, 'msg': '修改密码失败，旧密码不正确'}
        user_query.password = generate_password_hash(key_new_password)  # 更新密码
        try:
            DB.session.commit()
        except Exception as e:
            logger.log('ALERT', f'用户修改密码接口SQL错误:{e}')
            DB.session.rollback()
            return {'status_code': 201, 'msg': '修改密码失败，SQL错误'}
        addlog(session.get('username'), session.get('login_ip'), '修改用户密码成功')
        logger.log('INFOR', f"[{session.get('username')}]修改用户密码成功")
        return {'status_code': 200, 'msg': '修改密码成功'}

class UserManager(Resource):
    '''user 用户管理类'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)
        self.parser.add_argument("username", type=str, location='json')
        self.parser.add_argument("password", type=str, location='json')
        self.parser.add_argument("phone", type=str, location='json')
        self.parser.add_argument("email", type=str, location='json')
        self.parser.add_argument("remark", type=str, location='json')

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = User.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = User.query.limit(20).offset(0).all()
            else:
                paginate = User.query.limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = User.query.limit(20).offset(0).all()
            else:
                if 'username' not in search_dict or 'phone' not in search_dict or 'email' not in search_dict:  # 查询参数有误
                    paginate = User.query.limit(20).offset(0).all()
                else:
                    paginate1 = User.query.filter(
                        User.username.like("%" + search_dict['username'] + "%"),
                        User.phone.like("%" + search_dict['phone'] + "%"),
                        User.email.like("%" + search_dict['email'] + "%"),
                    )
                    paginate = paginate1.limit(key_limit).offset((key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['username'] = i.username
                data1['phone'] = i.phone
                data1['email'] = i.email
                data1['remark'] = i.remark
                data1['login_count'] = len(i.src_user_login_logs)
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
        key_username = args.username
        if not key_username:
            return {'status_code': 500, 'msg': '参数错误'}
        if session['username'] != 'root':
            addlog(session.get('username'), session.get('login_ip'), f'删除用户:[{key_username}] 失败，原因:非root用户')
            return {'status_code': 201, 'msg': '当前账户无删除用户权限'}
        if 'root' == key_username:  # 不能删除root用户
            addlog(session.get('username'), session.get('login_ip'), f'删除用户:[{key_username}] 失败，原因:不能删除内置用户')
            return {'status_code': 201, 'msg': '不能删除root内置用户'}
        user_query = User.query.filter(User.username == key_username).first()
        if not user_query:  # 删除的用户不存在
            addlog(session.get('username'), session.get('login_ip'), f'删除用户:[{key_username}] 失败，原因:该用户不存在')
            return {'status_code': 500, 'msg': '删除用户失败，无此用户'}
        DB.session.delete(user_query)
        try:
            DB.session.commit()
        except:
            DB.session.rollback()
            return {'status_code': 500, 'msg': '删除用户失败，SQL错误'}
        addlog(session.get('username'), session.get('login_ip'), f'删除用户:[{key_username}] 成功')
        return {'status_code': 200, 'msg': '删除用户成功'}

    def post(self):
        '''新增用户'''
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_username = args.username
        key_password = args.password
        key_phone = args.phone
        key_email = args.email
        key_remark = args.remark
        if session['username'] != 'root':
            return {'status_code': 202, 'msg': '新增用户失败，不能新增root用户'}
        user_query = User.query.filter(User.username == key_username).first()
        if user_query:  # 用户名存在
            addlog(session.get('username'), session.get('login_ip'), f'新增用户[{key_username}]失败，原因:用户已存在')
            return {'status_code': 201, 'msg': f'新增用户失败，{key_username}用户名已存在'}
        user1 = User(username=key_username,
                     password=key_password, phone=key_phone, email=key_email, remark=key_remark)
        DB.session.add(user1)
        try:
            DB.session.commit()
        except Exception as e:
            logger.log('ALERT', f'用户新增接口SQL错误:{e}')
            DB.session.rollback()
            return {'status_code': 500, 'msg': '新增用户失败，sql错误'}
        addlog(session.get('username'), session.get('login_ip'), f'新增用户[{key_username}]成功')
        return {'status_code': 200, 'msg': '新增用户成功'}

    def put(self):
        '''修改用户信息'''
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_username = args.username
        key_phone = args.phone
        key_email = args.email
        key_remark = args.remark
        user_query = User.query.filter(User.username == key_username).first()
        if not user_query:
            return {'status_code': 202, 'msg': f'修改用户资料失败，{key_username}用户名不存在'}
        user_query.phone = key_phone
        user_query.email = key_email
        user_query.remark = key_remark
        try:
            DB.session.commit()
        except Exception as e:
            logger.log('ALERT', f'用户管理接口-修改用户信息接口SQL错误:{e}')
            DB.session.rollback()
            addlog(session.get('username'), session.get('login_ip'), '用户管理接口-修改用户资料失败，原因:SQL错误')
            return {'status_code': 202, 'msg': f'修改用户资料失败，SQL出错'}
        addlog(session.get('username'), session.get('login_ip'), '用户管理接口-修改用户资料成功')
        logger.log('INFOR', f"用户管理接口-[{session.get('username')}]修改用户资料成功")
        return {'status_code': 200, 'msg': f'修改用户资料成功'}

class UserLoginLog(Resource):
    '''user 用户登录日志类'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = UserLoginLogs.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = UserLoginLogs.query.order_by(UserLoginLogs.id.desc()).limit(20).offset(0).all()
            else:
                paginate = UserLoginLogs.query.order_by(UserLoginLogs.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = UserLoginLogs.query.order_by(UserLoginLogs.id.desc()).limit(20).offset(0).all()
            else:
                if 'username' not in search_dict or 'login_ip' not in search_dict:  # 查询参数有误
                    paginate = UserLoginLogs.query.order_by(UserLoginLogs.id.desc()).limit(20).offset(0).all()
                else:
                    paginate1 = UserLoginLogs.query.filter(
                        UserLoginLogs.username.like("%" + search_dict['username'] + "%"),
                        UserLoginLogs.login_ip.like("%" + search_dict['login_ip'] + "%")).order_by(UserLoginLogs.id.desc())
                    paginate = paginate1.limit(key_limit).offset(
                        (key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['username'] = i.username
                data1['login_ip'] = i.login_ip
                data1['login_time'] = i.login_time
                data1['useragent'] = i.useragent
                data1['phone'] = i.src_user.phone
                index += 1
                data.append(data1)
            jsondata.update({'data': data})
            return jsondata
        else:
            jsondata = {'code': 0, 'msg': '', 'count': 0}
            jsondata.update({'data': []})
            return jsondata

class UserLog(Resource):
    '''user 用户操作日志类'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("page", type=int)
        self.parser.add_argument("limit", type=int)
        self.parser.add_argument("searchParams", type=str)

    def get(self):
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_page = args.page
        key_limit = args.limit
        key_searchParams = args.searchParams
        count = UserLogs.query.count()
        jsondata = {'code': 0, 'msg': '', 'count': count}
        if count == 0:  # 若没有数据返回空列表
            jsondata.update({'data': []})
            return jsondata
        if not key_searchParams:  # 若没有查询参数
            if not key_page or not key_limit:  # 判断是否有分页查询参数
                paginate = UserLogs.query.order_by(UserLogs.id.desc()).limit(20).offset(0).all()
            else:
                paginate = UserLogs.query.order_by(UserLogs.id.desc()).limit(key_limit).offset((key_page - 1) * key_limit).all()
        else:
            try:
                search_dict = json.loads(key_searchParams)  # 解析查询参数
            except:
                paginate = UserLogs.query.order_by(UserLogs.id.desc()).limit(20).offset(0).all()
            else:
                if 'username' not in search_dict or 'login_ip' not in search_dict:  # 查询参数有误
                    paginate = UserLogs.query.order_by(UserLogs.id.desc()).limit(20).offset(0).all()
                else:
                    paginate1 = UserLogs.query.filter(
                        UserLogs.username.like("%" + search_dict['username'] + "%"),
                        UserLogs.logs_ip.like("%" + search_dict['login_ip'] + "%")).order_by(UserLogs.id.desc())
                    paginate = paginate1.limit(key_limit).offset((key_page - 1) * key_limit).all()
                    jsondata = {'code': 0, 'msg': '', 'count': len(paginate1.all())}
        data = []
        if paginate:
            index = (key_page - 1) * key_limit + 1
            for i in paginate:
                data1 = {}
                data1['id'] = index
                data1['username'] = i.username
                data1['log_ip'] = i.logs_ip
                data1['log_time'] = i.logs_time
                data1['log_text'] = i.logs_text
                data1['phone'] = i.src_user.phone
                index += 1
                data.append(data1)
            jsondata.update({'data': data})
            return jsondata
        else:
            jsondata = {'code': 0, 'msg': '', 'count': 0}
            jsondata.update({'data': []})
            return jsondata

class MailApi(Resource):
    '''mail SMTP设置'''

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("smtp_ip", type=str, location='json')
        self.parser.add_argument("smtp_port", type=str, location='json')
        self.parser.add_argument("smtp_username", type=str, location='json')
        self.parser.add_argument("smtp_password", type=str, location='json')
        self.parser.add_argument("smtp_ssl", type=bool, location='json')
        self.parser.add_argument("address_email", type=str, location='json')
        self.parser.add_argument("mail_title", type=str, location='json')
        self.parser.add_argument("mail_txt", type=str, location='json')

    def post(self):
        '''更新SMTP配置'''
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        args = self.parser.parse_args()
        key_smtp_ip = args.smtp_ip
        key_smtp_port = args.smtp_port
        key_smtp_username = args.smtp_username
        key_smtp_password = args.smtp_password
        key_smtp_ssl = args.smtp_ssl
        APP.config.update(
            MAIL_SERVER=key_smtp_ip,
            MAIL_PORT=key_smtp_port,
            MAIL_USERNAME=key_smtp_username,
            MAIL_PASSWORD=key_smtp_password,
            MAIL_DEFAULT_SENDER=(key_smtp_username, key_smtp_username),
            MAIL_USE_TLS=key_smtp_ssl
        )
        mail_query = MailSetting.query.first()
        if mail_query:
            mail_query.smtp_ip = key_smtp_ip
            mail_query.smtp_port = key_smtp_port
            mail_query.smtp_username = key_smtp_username
            mail_query.smtp_password = key_smtp_password
            mail_query.smtp_ssl = key_smtp_ssl
        else:
            mail_query = MailSetting(key_smtp_ip, key_smtp_port, key_smtp_username, key_smtp_password, key_smtp_ssl)
            DB.session.add(mail_query)
        try:
            DB.session.commit()
        except Exception as e:
            logger.log('ALERT', f'更新SMTP配置失败，原因:{e}')
            DB.session.rollback()
            return {'status_code': 500, 'msg': '更新SMTP配置失败，SQL错误'}
        addlog(session.get('username'), session.get('login_ip'), '更新SMTP配置成功')
        logger.log('INFOR', f'更新SMTP配置成功[{key_smtp_ip}]')
        return {'status_code': 200, 'msg': '更新SMTP配置成功'}

    def put(self):
        '''发送测试邮件'''
        if not session.get('status'):
            return redirect(url_for('html_system_login'), 302)
        mail_query = MailSetting.query.first()
        if not mail_query:
            return {'status_code': 201, 'msg': f'发送邮件失败,请完成上一步操作'}
        args = self.parser.parse_args()
        key_address_email = args.address_email
        key_mail_title = args.mail_title
        key_mail_txt = args.mail_txt
        smail = SMail()
        result, msg = smail.send_mail(key_address_email, key_mail_title, key_mail_txt)
        if result:
            addlog(session.get('username'), session.get('login_ip'), f'发送测试邮件成功：[{key_mail_title}]')
            return {'status_code': 200, 'msg': '发送邮件成功'}
        else:
            return {'status_code': 201, 'msg': f'发送邮件失败:{msg}'}