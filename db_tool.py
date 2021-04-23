import re


# 字段对象
class KeyObj():
    sql_str = ""    # 原sql
    key_name = ""   # 字段名
    type = ""       # 类型
    len = ""        # 长度
    not_null = ""   # 是否null
    default = ""    # 默认值
    comment = ""    # 注释


# 表对象
class TableObj():
    sql_str = ""    # 原sql
    table_name = "" # 表名
    key_map = {}    # key:字段
    key_list = {}   # 普通键
    primary_key = []# 主键
    unique_key = {} # 联合键
    param = ""      # 表参数
    
    def __init__(self):
        self.key_map = {}
        self.key_list = {}
        self.primary_key = []
        self.unique_key = {}
        

# 解析sql文件
def analysis_sql_file(path):
    with open(path, 'r', encoding = 'utf8') as f:
        sql_str = f.readlines()
        sql_str = "".join(sql_str)
        return analysis_sql_str(sql_str)

# 解析sql str
def analysis_sql_str(sql_str):
    # 切割每一个表
    table_map = {}
    table_arr = sql_str.split("CREATE TABLE")
    for tmp_table_str in table_arr:
        # 填过空白行
        if tmp_table_str.isspace() or tmp_table_str == "":
            continue
        # 保持完整性
        table_obj = str_to_table_obj("CREATE TABLE" + tmp_table_str)
        table_map[table_obj.table_name] = table_obj
    return table_map

# 解析数据库表结构
def analysis_db_table(cursor, db_name):
    # 不存在就创建库
    cursor.execute("create database if not exists %s"%(db_name))
    cursor.execute("use %s"%(db_name))
    # 获取表名
    sql = "select table_name from information_schema.tables where table_schema='%s' and table_type='base table';"%(db_name)
    cursor.execute(sql)
    # 读取表名
    table_name_list = []
    results = cursor.fetchall()
    for row in results:
        table_name_list.append(row[0])
    
    # 获取创表sql
    sql_str = ""
    for table_name in table_name_list:
        cursor.execute("show create table %s"%(table_name))
        # results = cursor.fetchall()
        one_results = cursor.fetchone()
        sql_str += (one_results[1] + ";\n")
        
    return analysis_sql_str(sql_str)

# 创建差异变化sql
def create_diff_sql(table_map, db_table_map):
    # 新加的表
    add_table_sql = ""
    for table_name in table_map:
        if table_name not in db_table_map:
            add_table_sql += (table_map[table_name].sql_str + "\n")
        
    # 删除的表
    delete_table_sql = ""
    for table_name in db_table_map:
        if table_name not in table_map:
            delete_table_sql += "DROP TABLE %s;\n"%(table_name)
    
    # 对比已存在的表差异
    modify_table_sql = ""
    for table_name in table_map:
        if table_name in db_table_map:
            diff_sql_str = table_diff(table_map[table_name], db_table_map[table_name])
            modify_table_sql += (diff_sql_str + "\n")
    return add_table_sql + delete_table_sql + modify_table_sql
    


# str转TableObj
def str_to_table_obj(sql_str):
    table_obj = TableObj()
    table_obj.sql_str = sql_str
    # 获取表名
    sql_str = get_table_name(table_obj, sql_str)
    # 获取字段
    sql_str = get_table_val(table_obj, sql_str)
    # 获取键
    get_table_key(table_obj, sql_str)
    return table_obj

# 获取表名
def get_table_name(table_obj, sql_str):
    matchObj = re.match( r".*?`(.*?)`.*?\((.*)\) (.*);.*", sql_str, re.M|re.S)
    # 表名
    table_obj.table_name = matchObj.group(1)
    sql_str = matchObj.group(2)
    # 表参数
    table_obj.param = matchObj.group(3)
    return sql_str

# 获取字段
def get_table_val(table_obj, sql_str):
    while True :
        sql_str = sql_str.lstrip()
        # 是否还是字段行
        if sql_str.find("`") != 0:
            break
        
        # 字段str范围
        matchObj = re.match( r".*?`(.*?),(.*)", sql_str, re.M|re.S)
        key_str = "`" + matchObj.group(1)
        sql_str = matchObj.group(2)
        
        # 获取key
        key_obj = KeyObj()
        key_obj.sql_str = key_str
        matchObj = re.match( r"`(.*?)`(.*)", key_str, re.M|re.S)
        key_obj.key_name = matchObj.group(1)
        key_str = matchObj.group(2)
        
        # 获取注释
        matchObj = re.match( r"(.*)COMMENT '(.*?)'(.*)", key_str, re.M|re.S)
        if matchObj:
            key_obj.comment = matchObj.group(2)
            key_str = matchObj.group(1) + matchObj.group(3)
        
        # 获取默认值
        matchObj = re.match( r"(.*)DEFAULT '(.*?)'(.*)", key_str, re.M|re.S)
        if matchObj:
            key_obj.default = matchObj.group(2)
            key_str = matchObj.group(1) + matchObj.group(3)
            
        # 获取是否不为空
        matchObj = re.match( r"(.*)NOT NULL(.*)", key_str, re.M|re.S)
        if matchObj:
            key_obj.not_null = "NOT NULL"
            key_str = matchObj.group(1) + matchObj.group(2)
            
        # 获取类型和长度
        key_str = key_str.lstrip()
        matchObj = re.match( r"(.*?)\((.*?)\).*", key_str, re.M|re.S)
        if matchObj:
            key_obj.type = matchObj.group(1)
            key_obj.len = matchObj.group(2)
            
        # 添加到table_obj
        table_obj.key_map[key_obj.key_name] = key_obj
    return sql_str

# 获取键
def get_table_key(table_obj, sql_str):
    # 获取主键
    matchObj = re.match( r"(.*)PRIMARY KEY \((.*?)\)(.*)", sql_str, re.M|re.S)
    if matchObj:
        primary_key = matchObj.group(2)
        primary_key = primary_key.replace("`","")
        table_obj.primary_key = primary_key.split(",")
        sql_str = matchObj.group(1) + matchObj.group(3)
    # 获取联合键
    matchObj = re.match( r"(.*)UNIQUE KEY `(.*?)` \((.*?)\)(.*)", sql_str, re.M|re.S)
    if matchObj:
        unique_key = matchObj.group(3)
        unique_key = unique_key.replace("`","")
        unique_key = unique_key.split(",")
        table_obj.unique_key[matchObj.group(2)] = unique_key
        sql_str = matchObj.group(1) + matchObj.group(4)
    # 获取普通键
    while True :
        matchObj = re.match( r"(.*)KEY `(.*?)` \(`(.*?)`\)(.*)", sql_str, re.M|re.S)
        if matchObj:
            table_obj.key_list[matchObj.group(2)] = matchObj.group(3)
            sql_str = matchObj.group(1) + matchObj.group(4)
        break

# 生成两个表的差异sql， 第一个表为主
def table_diff(new_table, old_table):
    sql_str = ""
    table_name = new_table.table_name
    # 添加和修改的字段
    for key_name in new_table.key_map:
        new_key_obj = new_table.key_map[key_name]
        # 是否新字段
        if key_name not in old_table.key_map:
            sql_str += "ALTER TABLE %s ADD "%(table_name)
            sql_str += (key_obj_get_sql(new_key_obj) + "\n")
        else:
            # 字段存在
            # 检查差异
            old_key_obj = old_table.key_map[key_name]
            # 字段类型和长度
            if new_key_obj.type != old_key_obj.type \
                or new_key_obj.len != old_key_obj.len \
                or new_key_obj.not_null != old_key_obj.not_null \
                or new_key_obj.default != old_key_obj.default \
                or new_key_obj.comment != old_key_obj.comment:
                    sql_str += ("ALTER TABLE %s MODIFY "%(table_name) + key_obj_get_sql(new_key_obj) + "\n")
    # 删除的字段
    for key_name in old_table.key_map:
        if key_name not in new_table.key_map:
            sql_str += ("ALTER TABLE %s DROP %s;\n")%(table_name, key_name)
    
    # 索引
    
    
    # 表的属性
    # 暂时不考虑改这个
    return sql_str

# 获取字段类对应sql
def key_obj_get_sql(key_obj):
    sql_str = "{0} {1}({2}) {3}".format(
        key_obj.key_name
        , key_obj.type
        , key_obj.len
        , key_obj.not_null
    )
    # 是否有默认值
    if key_obj.default != "":
        sql_str += " DEFAULT '%s'"%(key_obj.default)
    # 是否有注释
    if key_obj.comment != "":
        sql_str += " COMMENT '%s'"%(key_obj.comment)
    sql_str += ";"
    return sql_str
