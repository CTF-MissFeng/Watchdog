from flask import render_template

from web import APP
from web.utils.auxiliary import login_required
from web.models import SrcCustomer, SrcVul

@APP.route('/src/customer')
@login_required
def html_src_customer():
    '''厂商页面'''
    return render_template('src/src_customer.html')

@APP.route('/src/customer_add')
@login_required
def html_src_customer_add():
    '''厂商添加页面'''
    return render_template('src/src_customer_add.html')

@APP.route('/src/task')
@login_required
def html_src_task():
    '''资产任务页面'''
    return render_template('src/src_task.html')

@APP.route('/src/task_add')
@login_required
def html_src_task_add():
    '''任务资产添加页面'''

    srctask_query = SrcCustomer.query.all()
    task_list = []
    if srctask_query:
        for i in srctask_query:
            task_list.append(i.cus_name)
    return render_template('src/src_task_add.html', task=task_list)

@APP.route('/src/ports')
@login_required
def html_src_ports():
    '''端口服务页面'''
    return render_template('src/src_ports.html')

@APP.route('/src/urls')
@login_required
def html_src_urls():
    '''资产页面'''
    return render_template('src/src_urls.html')

@APP.route('/src/vuls')
@login_required
def html_src_vuls():
    '''漏洞页面'''

    srcvul_query = SrcVul.query.with_entities(SrcVul.vul_plugin).distinct().all()
    plugin_list = []
    if srcvul_query:
        for i in srcvul_query:
            plugin_list.append(i.vul_plugin)
    return render_template('src/src_vul.html', vuls=plugin_list)