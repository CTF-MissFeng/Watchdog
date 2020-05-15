from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api

from web.config import Config

APP = Flask(__name__)
APP.config.from_object(Config)
DB = SQLAlchemy(APP)
API = Api(APP)

from web.route.system import html
from web.route.src import html

from web.route.system.api import UserLogin, UserSetting, UserPassword, UserManager, UserLog, UserLoginLog, MailApi
from web.route.src.api import SrcCustomerAPI, SrcTaskAPI, SrcPortAPI, SrcUrlAPI, SrcVulAPI

API.add_resource(UserLogin, '/api/user/login', endpoint='api_user_login')
API.add_resource(UserSetting, '/api/user/setting', endpoint='api_user_setting')
API.add_resource(UserPassword, '/api/user/password', endpoint='api_user_password')
API.add_resource(UserManager, '/api/user/manager', endpoint='api_user_manager')
API.add_resource(UserLog, '/api/user/logs', endpoint='api_user_logs')
API.add_resource(UserLoginLog, '/api/user/login_logs', endpoint='api_user_login_logs')
API.add_resource(MailApi, '/api/user/mail', endpoint='api_user_mail')

API.add_resource(SrcCustomerAPI, '/api/src/customer', endpoint='api_src_customer')
API.add_resource(SrcTaskAPI, '/api/src/task', endpoint='api_src_task')
API.add_resource(SrcPortAPI, '/api/src/port', endpoint='api_src_port')
API.add_resource(SrcUrlAPI, '/api/src/url', endpoint='api_src_url')
API.add_resource(SrcVulAPI, '/api/src/vul', endpoint='api_src_vul')
