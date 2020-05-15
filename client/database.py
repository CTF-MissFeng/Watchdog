import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://postgres:687fb677c784ce2a0b273263bfe778be@127.0.0.1/src')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class SrcCustomer(Base):
    '''Src客户管理'''

    __tablename__ = 'src_customer'
    cus_name = Column(String(80), primary_key=True)  # 厂商名
    cus_home = Column(String(100))  # 厂商主页
    cus_time = Column(String(30))  # 添加时间
    src_assets = relationship('SrcAssets', back_populates='src_customer', cascade='all, delete-orphan')
    src_task = relationship('SrcTask', back_populates='src_customer', cascade='all, delete-orphan')
    src_ports = relationship('SrcPorts', back_populates='src_customer', cascade='all, delete-orphan')

    def __init__(self, cus_name, cus_home):
        self.cus_name = cus_name
        self.cus_home = cus_home
        self.cus_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class SrcTask(Base):
    '''SRC 任务管理'''

    __tablename__ = 'src_task'
    id = Column(Integer, primary_key=True)
    task_name = Column(String(80), ForeignKey('src_customer.cus_name', ondelete='CASCADE'))  # 厂商名
    task_domain = Column(String(100), unique=True)  # 单条任务资产/子域名/IP/主域名
    task_time = Column(String(30))  # 添加时间
    task_flag = Column(Boolean)  # 是否探测标识
    src_customer = relationship('SrcCustomer', back_populates='src_task')

    def __init__(self, task_name, task_domain, task_flag=False):
        self.task_name = task_name
        self.task_domain = task_domain
        self.task_time = self.cus_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.task_flag = task_flag

class SrcAssets(Base):
    '''Src资产管理'''

    __tablename__ = 'src_assets'
    id = Column(Integer, primary_key=True)
    asset_name = Column(String(80), ForeignKey('src_customer.cus_name', ondelete='CASCADE'))   # 厂商名
    asset_host = Column(String(200), unique=True)  # 主机/url
    asset_subdomain = Column(String(200))  # 子域名
    asset_title = Column(Text)  # 网页标题
    asset_ip = Column(String(16))  # IP地址
    asset_area = Column(Text)  # 地区
    asset_waf = Column(String(100))  # waf
    asset_cdn = Column(Boolean)  # cdn
    asset_banner = Column(Text)  # banner
    asset_info = Column(Text)  # web指纹
    asset_whois = Column(Text)  # whois信息
    asset_time = Column(String(30))  # 添加时间
    asset_xray_flag = Column(Boolean)  # 是否爬虫/xary被动扫描
    asset_burp_flag = Column(Boolean)  # Burpsuite是否扫描
    asset_port_flag = Column(Boolean)  # 是否进行端口扫描
    asset_info_flag = Column(Boolean)  # 是否进行web信息收集
    src_customer = relationship('SrcCustomer', back_populates='src_assets')

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

class SrcPorts(Base):
    '''Src 端口管理'''

    __tablename__ = 'src_ports'
    id = Column(Integer, primary_key=True)
    port_name = Column(String(80), ForeignKey('src_customer.cus_name', ondelete='CASCADE'))  # 厂商名
    port_host = Column(String(200))  # 主机/子域名/url
    port_ip = Column(String(20))  # ip
    port_port = Column(String(20))  # 端口
    port_service = Column(String(30))  # 协议
    port_product = Column(String(100))  # 端口服务
    port_version = Column(String(100))  # 服务版本
    port_time = Column(String(30))  # 添加时间
    port_brute = Column(Boolean)  # 是否暴力破解
    port_url_scan = Column(Boolean)  # 是否进行HTTP探测
    src_customer = relationship('SrcCustomer', back_populates='src_ports')

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

class SrcVul(Base):
    '''Src 漏洞信息表'''

    __tablename__ = 'src_vul'
    id = Column(Integer, primary_key=True)
    vul_subdomain = Column(String(150))  # 子域名
    vul_plugin = Column(String(200))  # 插件
    vul_url = Column(Text)  # URL
    vul_payload = Column(Text)
    vul_raw = Column(Text)
    vul_time = Column(String(30))
    vul_scan_name = Column(String(30))  # 扫描器
    vul_flag = Column(Boolean)  # 标记已提交
    vul_mail = Column(Boolean)  # 是否发发送邮件

    def __init__(self, vul_subdomain, vul_plugin, vul_url, vul_payload, vul_raw, vul_scan_name, vul_flag=False,
                 vul_mail=False):
        self.vul_subdomain = vul_subdomain
        self.vul_plugin = vul_plugin
        self.vul_url = vul_url
        self.vul_payload = vul_payload
        self.vul_raw = vul_raw
        self.vul_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.vul_scan_name = vul_scan_name
        self.vul_flag = vul_flag
        self.vul_mail = vul_mail