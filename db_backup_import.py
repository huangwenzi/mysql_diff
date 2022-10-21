import MySQLdb
import os

# 需要配置
# vi /etc/my.cnf
# [mysqldump]
# user=root
# password="Ylunnvh)G4La"
# [client]
# host=127.0.0.1
# user=root
# password=Ylunnvh)G4La
user = "root"
password = "Ylunnvh)G4La"
sql_path = "./game_p1_s1_backup.sql"


# 连接数据库 
def connect(host, user, password):
    db = MySQLdb.Connect(         
        host = host      
        , user = user         
        , password = password         
        , charset = 'utf8'     
        )     
    cursor = db.cursor()     
    return cursor  

# 备份数据库 
def backup_db(base_name, save_path):     
    ret = os.popen("mysqldump -uroot --single-transaction --no-create-db -R %s > %s"%(base_name, save_path)).read()
    print(ret)

# 导入数据库 
def import_db(sql_path, base_name, user):
    do_str = "create database if not exists %s;"%(base_name)
    recover = "mysql -u%s -e\"%s\""%(user, do_str)
    ret = os.popen(recover).read()
    print(ret)
       
    recover = "mysql -u%s %s < %s"%(user, base_name, sql_path)
    ret = os.popen(recover).read()
    print(ret)
    # cursor.execute("source %s;"%(sql_path))

# 测试例子
backup_db("game_p1_s1", sql_path)
import_db(sql_path, "game_p1_s1_copy", user)