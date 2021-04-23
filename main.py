import MySQLdb



import db_tool as dbToolMd




def run():
    # 解析sql文件
    table_map = dbToolMd.analysis_sql_file("sql\\db.sql")
    # 导出数据库表结构
    db = MySQLdb.Connect(
        host = "127.0.0.1", 
        user = "root", 
        password = "123456", 
        # db = tmp_db_name, 
        charset='utf8' )
    cursor = db.cursor()
    db_table_map = dbToolMd.analysis_db_table(cursor, "test")
    # 对比差异,生成sql文件
    sql_str = dbToolMd.create_diff_sql(table_map, db_table_map)
    # 导出一份到本地
    with open("diff_sql.sql", 'w', encoding = 'utf8') as f:
        f.write(sql_str)
    # 执行修改
    cursor.execute(sql_str)

run()

