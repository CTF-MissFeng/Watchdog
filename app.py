from web.models import User
from web import DB, APP

@APP.cli.command()
def CreateDB():
    '''创建数据库'''
    DB.create_all()

@APP.cli.command()
def CreateUser():
    '''创建测试账户'''
    sql = User.query.filter(User.username == 'root').first()
    if not sql:
        user1 = User(username='root', password='qazxsw@123', phone='1388888888', email='admin@qq.com',
                     remark='渗透测试工程师')
        DB.session.add(user1)
        DB.session.commit()

@APP.cli.command()
def ResetDB():
    '''重置数据库'''
    DB.drop_all()

# export FLASK_APP=app.py:APP