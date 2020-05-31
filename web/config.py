import uuid
import pathlib
import os

class Config(object):
    '''Flask数据配置'''
    SECRET_KEY = str(uuid.uuid4())
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:687fb677c784ce2a0b273263bfe778be@127.0.0.1/src'  # 数据库连接字符串
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_ADDRES = '1767986993@qq.com'  # 接收邮件
    UPLOAD_FOLDER = pathlib.Path(__file__).parent.joinpath('upload').resolve()
    if not os.path.isdir(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    UPLOAD_FOLDER_TMP = os.path.join(UPLOAD_FOLDER, 'tmp')
    if not os.path.isdir(UPLOAD_FOLDER_TMP):
        os.mkdir(UPLOAD_FOLDER_TMP)