import datetime
from flask import escape
from werkzeug.security import generate_password_hash

from web import DB

class User(DB.Model):
    '''User表'''

    __tablename__ = 'src_user'
    username = DB.Column(DB.String(20), primary_key=True)
    password = DB.Column(DB.String(128), nullable=False)
    phone = DB.Column(DB.String(20))
    email = DB.Column(DB.String(50))
    remark = DB.Column(DB.Text)
    src_user_login_logs = DB.relationship('UserLoginLogs', back_populates='src_user', cascade='all, delete-orphan')
    src_user_logs = DB.relationship('UserLogs', back_populates='src_user', cascade='all, delete-orphan')

    def __init__(self, username, password, phone, email, remark):
        self.username = escape(username)
        self.password = generate_password_hash(password)
        self.phone = escape(phone)
        self.email = escape(email)
        self.remark = escape(remark)

class UserLoginLogs(DB.Model):
    '''User登录日志表'''

    __tablename__ = 'src_user_login_logs'
    id = DB.Column(DB.Integer, primary_key=True)
    username = DB.Column(DB.String(20), DB.ForeignKey('src_user.username', ondelete='CASCADE'))  # 外键
    login_time = DB.Column(DB.String(30))
    login_ip = DB.Column(DB.String(15))
    useragent = DB.Column(DB.Text)
    src_user = DB.relationship('User', back_populates='src_user_login_logs')

    def __init__(self, username, login_ip, useragent):
        self.username = username
        self.login_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.login_ip = escape(login_ip)
        self.useragent = escape(useragent)

class UserLogs(DB.Model):
    '''User操作日志表'''

    __tablename__ = 'src_user_logs'
    id = DB.Column(DB.Integer, primary_key=True)
    username = DB.Column(DB.String(20), DB.ForeignKey('src_user.username', ondelete='CASCADE'))
    logs_time = DB.Column(DB.String(30))
    logs_ip = DB.Column(DB.String(15))
    logs_text = DB.Column(DB.String(500))
    src_user = DB.relationship('User', back_populates='src_user_logs')  # 双向关系

    def __init__(self, username, logs_ip, logs_text):
        self.username = username
        self.logs_ip = logs_ip
        self.logs_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs_text = logs_text

class MailSetting(DB.Model):
    '''邮箱SMTP配置'''

    __tablename__ = 'src_mail_setting'
    id = DB.Column(DB.Integer, primary_key=True)
    smtp_ip = DB.Column(DB.String(100))
    smtp_port = DB.Column(DB.Integer)
    smtp_username = DB.Column(DB.String(100))
    smtp_password = DB.Column(DB.String(100))
    smtp_ssl = DB.Column(DB.Boolean)
    address_email = DB.Column(DB.String(100))  # 收件人

    def __init__(self, smtp_ip, smtp_port, smtp_username, smtp_password, address_email, smtp_ssl=False):
        self.smtp_ip = smtp_ip
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.ssl = smtp_ssl
        self.address_email = address_email


class SrcCustomer(DB.Model):
    '''Src客户管理'''

    __tablename__ = 'src_customer'
    cus_name = DB.Column(DB.String(80), primary_key=True)  # 厂商名
    cus_home = DB.Column(DB.String(100))  # 厂商主页
    cus_time = DB.Column(DB.String(30))  # 添加时间
    src_assets = DB.relationship('SrcAssets', back_populates='src_customer', cascade='all, delete-orphan')
    src_task = DB.relationship('SrcTask', back_populates='src_customer', cascade='all, delete-orphan')
    src_ports = DB.relationship('SrcPorts', back_populates='src_customer', cascade='all, delete-orphan')

    def __init__(self, cus_name, cus_home):
        self.cus_name = cus_name
        self.cus_home = cus_home
        self.cus_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class SrcTask(DB.Model):
    '''SRC 任务管理'''

    __tablename__ = 'src_task'
    id = DB.Column(DB.Integer, primary_key=True)
    task_name = DB.Column(DB.String(80), DB.ForeignKey('src_customer.cus_name', ondelete='CASCADE'))  # 厂商名
    task_domain = DB.Column(DB.String(100), unique=True)  # 单条任务资产/子域名/IP/主域名
    task_time = DB.Column(DB.String(30))  # 添加时间
    task_flag = DB.Column(DB.Boolean)  # 是否探测标识
    src_customer = DB.relationship('SrcCustomer', back_populates='src_task')

    def __init__(self, task_name, task_domain, task_flag=False):
        self.task_name = task_name
        self.task_domain = task_domain
        self.task_time = self.cus_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.task_flag = task_flag

class SrcAssets(DB.Model):
    '''Src资产管理'''

    __tablename__ = 'src_assets'
    id = DB.Column(DB.Integer, primary_key=True)
    asset_name = DB.Column(DB.String(80), DB.ForeignKey('src_customer.cus_name', ondelete='CASCADE'))   # 厂商名
    asset_host = DB.Column(DB.String(200), unique=True)  # 主机/url
    asset_subdomain = DB.Column(DB.String(200))  # 子域名
    asset_title = DB.Column(DB.Text)  # 网页标题
    asset_ip = DB.Column(DB.String(16))  # IP地址
    asset_area = DB.Column(DB.Text)  # 地区
    asset_waf = DB.Column(DB.String(100))  # waf
    asset_cdn = DB.Column(DB.Boolean)  # cdn
    asset_banner = DB.Column(DB.Text)  # banner
    asset_info = DB.Column(DB.Text)  # web指纹
    asset_whois = DB.Column(DB.Text)  # whois信息
    asset_time = DB.Column(DB.String(30))  # 添加时间
    asset_xray_flag = DB.Column(DB.Boolean)  # 是否爬虫/xary被动扫描
    asset_burp_flag = DB.Column(DB.Boolean)  # Burpsuite是否扫描
    asset_port_flag = DB.Column(DB.Boolean)  # 是否进行端口扫描
    asset_info_flag = DB.Column(DB.Boolean)  # 是否进行web信息收集
    src_customer = DB.relationship('SrcCustomer', back_populates='src_assets')

    def __init__(self, asset_name, asset_host, asset_subdomain, asset_title, asset_ip, asset_area, asset_waf, asset_cdn,
                 asset_banner, asset_info, asset_whois, asset_xray_flag=False, asset_burp_flag=False,
                 asset_port_flag=False, asset_info_flag=False):
        self.asset_name = asset_name
        self.asset_host = asset_host
        self.asset_subdomain = asset_subdomain
        self.asset_title = asset_title
        self.asset_ip = asset_ip
        self.asset_area = asset_area
        self.asset_waf = asset_waf
        self.asset_cdn = asset_cdn
        self.asset_banner = asset_banner
        self.asset_info = asset_info
        self.asset_whois = asset_whois
        self.asset_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.asset_xray_flag = asset_xray_flag
        self.asset_burp_flag = asset_burp_flag
        self.asset_port_flag = asset_port_flag
        self.asset_info_flag = asset_info_flag

class SrcPorts(DB.Model):
    '''Src 端口管理'''

    __tablename__ = 'src_ports'
    id = DB.Column(DB.Integer, primary_key=True)
    port_name = DB.Column(DB.String(80), DB.ForeignKey('src_customer.cus_name', ondelete='CASCADE'))  # 厂商名
    port_host = DB.Column(DB.String(200))  # 主机/子域名/url
    port_ip = DB.Column(DB.String(20))  # ip
    port_port = DB.Column(DB.String(20))  # 端口
    port_service = DB.Column(DB.String(30))  # 协议
    port_product = DB.Column(DB.String(100))  # 端口服务
    port_version = DB.Column(DB.String(100))  # 服务版本
    port_time = DB.Column(DB.String(30))  # 添加时间
    port_brute = DB.Column(DB.Boolean)  # 是否暴力破解
    port_url_scan = DB.Column(DB.Boolean)  # 是否进行HTTP探测
    src_customer = DB.relationship('SrcCustomer', back_populates='src_ports')

    def __init__(self, port_name, port_host, port_ip, port_port, port_service, port_product, port_version, port_brute=False,
                 port_url_scan=False):
        self.port_name = port_name
        self.port_host = port_host
        self.port_ip = port_ip
        self.port_port = port_port
        self.port_service = port_service
        self.port_product = port_product
        self.port_version = port_version
        self.port_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.port_brute = port_brute
        self.port_url_scan = port_url_scan

class SrcVul(DB.Model):
    '''Src 漏洞信息表'''

    __tablename__ = 'src_vul'
    id = DB.Column(DB.Integer, primary_key=True)
    vul_subdomain = DB.Column(DB.String(150))  # 子域名
    vul_plugin = DB.Column(DB.String(200))  # 插件
    vul_url = DB.Column(DB.Text)  # URL
    vul_payload = DB.Column(DB.Text)
    vul_raw = DB.Column(DB.Text)
    vul_time = DB.Column(DB.String(30))
    vul_scan_name = DB.Column(DB.String(30))  # 扫描器
    vul_flag = DB.Column(DB.Boolean)  # 标记已提交
    vul_mail = DB.Column(DB.Boolean)  # 是否发发送邮件

    def __init__(self, vul_subdomain, vul_plugin, vul_url, vul_payload, vul_raw, vul_scan_name, vul_flag=False, vul_mail=False):
        self.vul_subdomain = vul_subdomain
        self.vul_plugin = vul_plugin
        self.vul_url = vul_url
        self.vul_payload = vul_payload
        self.vul_raw = vul_raw
        self.vul_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.vul_scan_name = vul_scan_name
        self.vul_flag = vul_flag
        self.vul_mail = vul_mail