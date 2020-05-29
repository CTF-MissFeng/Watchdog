import uuid

class Config(object):
    '''Flask数据配置'''
    #SECRET_KEY = str(uuid.uuid4())
    SECRET_KEY = '123456'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:687fb677c784ce2a0b273263bfe778be@127.0.0.1/src'  # 数据库连接字符串
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_ADDRES = '1767986993@qq.com'  # 接收邮件