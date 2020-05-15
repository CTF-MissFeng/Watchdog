from flask import session, redirect, url_for, render_template, jsonify, request

from web import APP
from web.utils.auxiliary import login_required, addlog, logger
from web.models import User, MailSetting

@APP.route('/')
def html_system_login():
    '''用户登录页面'''
    if 'status' in session:
        return redirect(url_for('html_system_index'), 302)
    return render_template('system/user_login.html')

@APP.route('/system/index')
@login_required
def html_system_index():
    '''框架首页'''
    return render_template('/system/index.html', username=session['username'])

@APP.route('/api/user/logout')
@login_required
def api_user_logout():
    '''用户注销'''
    addlog(session.get('username'), session.get('login_ip'), '注销登录成功')
    logger.log('INFOR', f"用户注销接口-用户[{session.get('username')}]注销成功")
    session.pop('status')
    session.pop('username')
    session.pop('login_ip')
    return redirect(url_for('html_system_login'), 302)

@APP.route('/system/setting')
@login_required
def html_system_setting():
    '''用户资料修改'''
    user_query = User.query.filter(User.username == session.get('username')).first()  # 查询该用户信息
    if not user_query:
        return redirect(url_for('html_user_login'), 302)
    info_dict = {
        'username': session.get('username'),
        'phone': user_query.phone,
        'email': user_query.email,
        'remark': user_query.remark
    }
    return render_template('system/user_setting.html', user=info_dict)

@APP.route('/system/password')
@login_required
def html_system_password():
    '''修改用户密码'''
    return render_template('system/user_password.html')

@APP.route('/system/usermanager')
@login_required
def html_system_usermanager():
    '''用户管理'''
    return render_template('system/user_manager.html')

@APP.route('/system/useradd')
@login_required
def html_system_useradd():
    '''新增用户'''
    return render_template('system/user_add.html')

@APP.route('/system/useredit')
@login_required
def html_system_useredit():
    '''修改用户信息'''
    username = request.args.get("username")
    if session.get('username') != 'root':
        return render_template('system/404.html')
    if not username:
        return render_template('error/404.html')
    user_query = User.query.filter(User.username == username).first()  # 查询该用户信息
    if not user_query:
        return redirect(url_for('html_user_login'), 302)
    info_dict = {
        'username': user_query.username,
        'phone': user_query.phone,
        'email': user_query.email,
        'remark': user_query.remark
    }
    return render_template('system/user_edit.html', user=info_dict)

@APP.route('/system/login_logs')
@login_required
def html_system_loginlogs():
    '''用户日志登录查询页面'''
    return render_template('system/user_login_logs.html')

@APP.route('/system/logs')
@login_required
def html_system_logs():
    '''用户操作日志查询页面'''
    return render_template('system/user_logs.html')

@APP.route('/system/mail')
@login_required
def html_system_mail():
    '''邮箱SMTP页面'''
    mail_query = MailSetting.query.first()
    if not mail_query:
        return render_template('system/mail_setting.html', mail={})
    info_dict = {
        'smtp_ip': mail_query.smtp_ip,
        'smtp_port': str(mail_query.smtp_port),
        'smtp_username': mail_query.smtp_username,
        'smtp_password': mail_query.smtp_password,
        'smtp_ssl': mail_query.smtp_ssl,
        'address_email': mail_query.address_email
    }
    return render_template('system/mail_setting.html', mail=info_dict)


@APP.route('/api/system/clear')
@login_required
def api_caching_clear():
    return jsonify({'code': 1, 'msg': '服务端缓存清理成功'})

@APP.errorhandler(404)
def page_not_found(e):
    return render_template('system/404.html'), 404

@APP.errorhandler(500)
def internal_server_error(e):
    return render_template('system/500.html'), 500

@APP.route('/system/init')
@login_required
def api_menu_init():
    '''菜单栏目'''
    home_menu = {'title': '主页', 'icon': 'fa fa-home', 'href': ''}  # 主页菜单
    logo_menu = {'title': '看门狗', 'image': url_for('static', filename='images/logo.png'), 'href': ''}  # logo菜单
    assets_menu = {'title': '资产管理', 'icon': 'fa fa-address-book', 'child': [
        {'title': '厂商管理', 'href': url_for('html_src_customer'), 'icon': 'fa fa-tachometer', 'target': '_self'},
        {'title': '资产任务管理', 'href': url_for('html_src_task'), 'icon': 'fa fa-globe', 'target': '_self'},
        {'title': 'URL管理', 'href': url_for('html_src_urls'), 'icon': 'fa fa-paw', 'target': '_self'},
        {'title': '端口服务管理', 'href': url_for('html_src_ports'), 'icon': 'fa fa-cube', 'target': '_self'},
        {'title': 'Web漏洞管理', 'href': url_for('html_src_vuls'), 'icon': 'fa fa-user-secret', 'target': '_self'},
    ]}
    system_menu = {'title': '系统管理', 'icon': 'fa fa-gears', 'child': [
        {'title': '用户管理', 'href': url_for('html_system_usermanager'), 'icon': 'fa fa-users', 'target': '_self'},
        {'title': '日志管理', 'href': '', 'icon': 'fa fa-building-o', 'target': '_self', 'child': [
            {'title': '操作日志', 'href': url_for('html_system_logs'), 'icon': 'fa fa-area-chart', 'target': '_self'},
            {'title': '登录日志', 'href': url_for('html_system_loginlogs'), 'icon': 'fa fa-bar-chart', 'target': '_self'}
        ]},
        {'title': '邮箱设置', 'href': url_for('html_system_mail'), 'icon': 'fa fa-envelope-o', 'target': '_self'}
    ]}
    menu_dict = {'homeInfo': home_menu, 'logoInfo': logo_menu, 'menuInfo': [assets_menu, system_menu]}
    return jsonify(menu_dict)