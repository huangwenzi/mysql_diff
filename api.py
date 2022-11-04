import sys
import pymysql
import time

import db_tool as dbToolMd

def run():
    if len(sys.argv) < 1:
        print("参数缺少")
        return
    
    user = sys.argv[1]
    password = sys.argv[2]
    port = int(sys.argv[3]) 
    db_name = sys.argv[4]
    sql_path = sys.argv[5]
    out_path = sys.argv[6]
    
    # 解析sql文件
    table_map = dbToolMd.analysis_sql_file(sql_path)
    # 导出数据库表结构
    db = pymysql.Connect(
        port = port, 
        user = user, 
        password = password, 
        # database = db_name,   # 不指定，不存在会报错的
        charset='utf8' )
    cursor = db.cursor()
    db_table_map = dbToolMd.analysis_db_table(cursor, db_name)
    # 对比差异,生成sql文件
    sql_str = dbToolMd.create_diff_sql(table_map, db_table_map)
    # 没有可执行的sql语句
    sql_str = sql_str.lstrip()
    if sql_str == "":
        return 
    
    # 导出一份到本地
    with open(out_path, 'a+', encoding = 'utf8') as f:
        f.write("-- %s\n"%(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        f.write(sql_str)
        f.write("\n\n")
    sql_str = sql_str.replace("\n", "")
    sql_str = sql_str.expandtabs()
    # 执行修改
    # sql_str = sql_str.replace("\n", "")
    # print(sql_str)
    # cursor.execute(sql_str)
    
    sql_list = sql_str.split(";")
    for tmp_sql in sql_list:
        if tmp_sql.isspace() or tmp_sql == "":
            continue
        # time.sleep(0.1)
        cursor.execute(tmp_sql)
run()



















