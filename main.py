import MySQLdb
import time


import db_tool as dbToolMd
import cfg as cfgMd



def run(db_name):
    db_cfg = cfgMd.db_map[db_name]
    # 解析sql文件
    table_map = dbToolMd.analysis_sql_file(db_cfg["sql_path"])
    # 导出数据库表结构
    db = MySQLdb.Connect(
        host = db_cfg["host"], 
        user = db_cfg["user_name"], 
        password = db_cfg["user_pass"], 
        # db = tmp_db_name, 
        charset='utf8' )
    cursor = db.cursor()
    db_table_map = dbToolMd.analysis_db_table(cursor, db_cfg["db_name"])
    # 对比差异,生成sql文件
    sql_str = dbToolMd.create_diff_sql(table_map, db_table_map)
    # 没有可执行的sql语句
    sql_str = sql_str.lstrip()
    if sql_str == "":
        return 
    
    # 导出一份到本地
    with open(db_cfg["out_path"], 'w+', encoding = 'utf8') as f:
        f.write("-- %s\n"%(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        f.write(sql_str)
    # 执行修改
    cursor.execute(sql_str)

run("web_svr")
