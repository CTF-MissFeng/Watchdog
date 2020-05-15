from flask import session, redirect, url_for, current_app
from functools import wraps
import threading
import time

from web import DB, APP
from web.utils.logs import logger
from web.models import UserLogs, MailSetting, SrcVul
from flask_mail import Message, Mail

def login_required(func):
    '''登录验证装饰器'''
    @wraps(func)
    def inner(*args, **kwargs):
        user = session.get('status')
        if not user:
            return redirect(url_for('html_system_login'), 302)
        return func(*args, **kwargs)
    return inner

def addlog(username, logs_ip, logs_text):
    '''添加用户操作日志'''
    try:
        logs = UserLogs(username, logs_ip, logs_text)
        DB.session.add(logs)
        DB.session.commit()
    except Exception as e:
        logger.log('ALERT', f'用户操作日志添加失败，错误代码:{e}')
        DB.session.rollback()

class SMail:
    def __init__(self):
        self.mail = Mail(current_app)

    def send_mail(self, address_email, mail_title, mail_txt):
        '''发送邮件'''
        message = Message()
        message.subject = mail_title
        message.recipients = [address_email]
        message.body = mail_txt
        try:
            self.mail.send(message)
        except Exception as e:
            logger.log('ALERT', f'发送邮件失败，错误代码:{e}')
            return False, e
        else:
            logger.log('INFOR', f'发送邮件成功:{mail_title}')
            return True, None

def update_config():
    '''初始化SMTP服务参数'''
    mail_query = MailSetting.query.first()
    if mail_query:
        APP.config.update(
            MAIL_SERVER=mail_query.smtp_ip,
            MAIL_PORT=mail_query.smtp_port,
            MAIL_USERNAME=mail_query.smtp_username,
            MAIL_PASSWORD=mail_query.smtp_password,
            MAIL_DEFAULT_SENDER=(mail_query.smtp_username, mail_query.smtp_username),
            MAIL_USE_TLS=mail_query.smtp_ssl
    )
        return True
    else:
        return False

# def Vul_SendMail(MAPP, Message1):
#     '''监控漏洞，发送邮件'''
#     while True:
#         mail_query = MailSetting.query.first()
#         if not mail_query:
#             time.sleep(60)
#             continue
#         vul_sql = SrcVul.query.filter(SrcVul.vul_mail == False).all()
#         if vul_sql:
#             mail_txt1 = f'主人，发现【{len(vul_sql)}】条新漏洞，请查收：\r\n'
#             for vuls in vul_sql:
#                 mail_txt1 += f'主机[{vuls.vul_subdomain}]  漏洞类型[{vuls.vul_plugin}]  URL[{vuls.vul_url}]\r\n'
#                 vuls.vul_mail = True
#                 DB.session.add(vuls)
#             try:
#                 DB.session.commit()
#             except Exception as e:
#                 DB.session.rollback()
#             else:
#                 print('[+]检测到新漏洞，开始发送邮件')
#                 try:
#                     with MAPP.app_context():
#                         message = Message1()
#                         message.subject = '主人,看门狗来看您了,请打开门'
#                         message.recipients = [APP.config['MAIL_ADDRES']]
#                         message.body = mail_txt1
#                         Vul_Mail.send(message)
#                 except Exception as e:
#                     logger.log('ALERT', f'发送邮件失败，错误代码:{e}')
#                 else:
#                     logger.log('INFOR', f'发送邮件成功')
#
#
# if update_config():
#     Vul_Mail = Mail(APP)
#     print(f'[+]邮件监控启动')
#     thread_mail = threading.Thread(target=Vul_SendMail, name='mail_send', args=(APP, Message))
#     thread_mail.start()