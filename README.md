### Watchdog
> Watchdog是bayonet修改版，重新设计了数据库及web及扫描程序,目前正在开发中

### 安装方法
> 以ubuntu16全新系统为例

```bash
# 1、安装python3环境,这里推荐使用minicoda方式安装：
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sh Miniconda3-latest-Linux-x86_64.sh  # 根据提示进行安装

# 2、默认miniconda环境为python3.7，这里新创建一个python3.8环境
conda create --name python python=3.8  # 创创建环境
conda activate python   # 激活环境，现在你应该在python3.8环境中

# 3、apt安装必备环境
apt-get update
apt install build-essential libssl-dev libffi-dev python3-dev  # python相关环境
apt install nmap  # 安装nmap
sudo apt-get install chromium-browser  # 安装chromium浏览器

# 4、安装相关Python模块
git clone https://github.com/CTF-MissFeng/Watchdog.git
cd Watchdog
pip install -r requirements.txt

# 5、安装并设置postgres数据库
apt install postgresql postgresql-contrib  # 安装postgres数据库
sudo -u postgres psql  # 进入psql命令行
\password postgres  # 设置postgres用户密码

# 6、设置postgresql数据库允许远程访问
参考：http://lazybios.com/2016/11/how-to-make-postgreSQL-can-be-accessed-from-remote-client/
 修改postgresql.conf
 修改pg_hba.conf
现在使用数据库管理工具连接postgresql数据库，应该可以连接成功。在创建一个空的src数据库

# 7、修改项目配置文件
vim Watchdog/web/config.py  # 修改数据库连接配置
vim Watchdog/client/database.py  # 修改数据库连接配置

8、运行Watchdog
cd Watchdog
export FLASK_APP=app.py:APP  # 配置flaskAPP
flask --help  # 现在你应该可以Commands看到有3个自定义命令
flask createdb  # 创建数据库
flask createuser  # 创建测试账户，root/qazxsw@123
flask run -p 80 -h 0.0.0.0  # 启动后，打开该服务器外网ip，访问http://外网ip 是否可以成功访问并登录web环境
ontrol + C 结束flask运行，使用后台运行

nohup flask run -p 80 -h 0.0.0.0 > web.log 2>&1 &

# 9、配置并启动各工具模块：子域名扫描、端口扫描、URL探测、xray扫描
vim client/subdomain/oneforall/config.py # 必须配置shodan api，其他参数自己选填

# 启动子域名扫描
cd client/subdomain/oneforall
nohup python -u sbudomain_run.py > dns.log 2>&1 &
cat dns.log  # 查看日志是否正常

# 启动端口扫描
cd client/portscan
nohup python -u portscan_run.py > port.log 2>&1 &  
cat port.log  # 查看日志是否正常

# 启动url扫描
cd client/urlscan/url_probe  
nohup python -u urlscan_run.py > url.log 2>&1 & 
cat url.log # 查看日志是否正常

# 启动xray
cd client/urlscan/xray
nohup python -u xray_run.py > xray.log 2>&1 &
cat xray.log # 查看日志是否正常
```

### 多节点部署
> 其他节点不需要数据库、web,所以只需要安装相应环境，配置database.py里数据库连接为主节点的ip，在后台执行client里的工具即可

#### 演示效果
> 这里我部署了3台vps,其中a为主节点运行数据库、web、client工具，其他b和c节点只需要运行client里相应工具

![index](https://github.com/CTF-MissFeng/Watchdog/blob/master/images/1.png)

![index](https://github.com/CTF-MissFeng/Watchdog/blob/master/images/2.png)

![index](https://github.com/CTF-MissFeng/Watchdog/blob/master/images/3.png)

![index](https://github.com/CTF-MissFeng/Watchdog/blob/master/images/4.png)

![index](https://github.com/CTF-MissFeng/Watchdog/blob/master/images/5.png)