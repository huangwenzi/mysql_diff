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
    unsigned = ""   # 是否无符号

# 索引对象
class IndexObj():
    sql_str = ""    # 原sql
    name = ""       # 索引名
    field = []      # 索引字段

# 表对象
class TableObj():
    sql_str = ""    # 原sql
    table_name = "" # 表名
    key_map = {}    # key:字段
    ordinary_key = {}   # 普通键
    primary_key = None# 主键
    unique_key = {} # 联合键
    param = ""      # 表参数
    
    def __init__(self):
        self.key_map = {}
        self.ordinary_key = {}
        self.primary_key = None
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
    # sql = "select table_name from information_schema.tables where table_schema='%s' and table_type='base table';\n"%(db_name)
    sql = "show tables;"
    cursor.execute(sql)
    # 读取表名
    table_name_list = []
    results = cursor.fetchall()
    for row in results:
        table_name_list.append(row[0])
    
    # 获取创表sql
    sql_str = ""
    # print("analysis_db_table db_name:%s table_name_list:%s"%(db_name, table_name_list))
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
            print("table_map %s"%(table_map.keys()))
            print("db_table_map %s"%(db_table_map.keys()))
            add_table_sql += table_map[table_name].sql_str
        
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
            modify_table_sql += diff_sql_str
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
def get_table_name(table_obj:TableObj, sql_str:str):
    # print("sql_str:%s\n"%(sql_str))
    # 表名
    table_obj.table_name,sql_str = get_str_by_begin_end(sql_str, "`", "`")
    # 表字段
    field_str,sql_str = get_str_by_begin_end(sql_str, "(", "\n)")
    # 表参数
    param_end = sql_str.find(";)")
    table_obj.param = sql_str[: param_end]
    # print("table_obj.table_name:%s\n"%(table_obj.table_name))
    # print("table_obj.param:%s\n"%(table_obj.param))
    # print("field_str:%s\n"%(field_str))
    return field_str
    
    # re实现
    # matchObj = re.match( r".*?`(.*?)`.*?\((.*)\) (.*);.*", sql_str, re.M|re.S)
    # # 表名
    # table_obj.table_name = matchObj.group(1)
    # sql_str = matchObj.group(2)
    # # 表参数
    # table_obj.param = matchObj.group(3)
    # return sql_str

# 获取字段
def get_table_val(table_obj:TableObj, sql_str:str):
    while True :
        sql_str = sql_str.lstrip()
        # 是否还是字段行
        if sql_str.find("`") != 0:
            break
        
        # find实现
        # 字段str范围
        key_str_end = sql_str.find("\n")
        key_str = sql_str[:key_str_end]
        sql_str = sql_str[key_str_end:]
        # 获取key
        key_obj = KeyObj()
        key_obj.sql_str = key_str
        key_obj.key_name,key_str = get_str_by_begin_end(key_str, "`", "`")
        # 获取注释
        key_obj.comment,_tmp = get_str_by_begin_end(key_str, "COMMENT '", "'")
        # 获取默认值
        key_obj.default,_tmp = get_str_by_begin_end(key_str, "DEFAULT '", "'")
        # 是否无符号
        if key_str.find("unsigned") != -1:
            key_obj.unsigned = "unsigned"
        # 获取是否不为空
        if key_str.find("NOT NULL") != -1:
            key_obj.not_null = "NOT NULL"
        # 获取类型和长度
        key_str = key_str.lstrip()
        matchObj = re.match( r".*? (.*?)\((.*?)\).*", key_str, re.M|re.S)
        if matchObj:
            key_obj.type = matchObj.group(1)
            key_obj.len = matchObj.group(2)
        else:
            # 不是type(len)格式
            matchObj = re.match( r"(.*?) .*", key_str, re.M|re.S)
            key_obj.type = matchObj.group(1)
            key_obj.type = key_obj.type.strip()
            key_obj.len = 0
        
        # # re实现
        # # 字段str范围
        # matchObj = re.match( r".*?`(.*?),\n(.*)", sql_str, re.M|re.S)
        # key_str = "`" + matchObj.group(1)
        # sql_str = matchObj.group(2)
        
        # # 获取key
        # key_obj = KeyObj()
        # key_obj.sql_str = key_str
        # matchObj = re.match( r"`(.*?)`(.*)", key_str, re.M|re.S)
        # key_obj.key_name = matchObj.group(1)
        # key_str = matchObj.group(2)
        
        # # 获取注释
        # matchObj = re.match( r"(.*)COMMENT '(.*?)'(.*)", key_str, re.M|re.S)
        # if matchObj:
        #     key_obj.comment = matchObj.group(2)
        #     key_str = matchObj.group(1) + matchObj.group(3)
        
        # # 获取默认值
        # matchObj = re.match( r"(.*)DEFAULT '(.*?)'(.*)", key_str, re.M|re.S)
        # if matchObj:
        #     key_obj.default = matchObj.group(2)
        #     key_str = matchObj.group(1) + matchObj.group(3)
            
        # # 获取是否不为空
        # matchObj = re.match( r"(.*)NOT NULL(.*)", key_str, re.M|re.S)
        # if matchObj:
        #     key_obj.not_null = "NOT NULL"
        #     key_str = matchObj.group(1) + matchObj.group(2)
            
        # # 获取类型和长度
        # key_str = key_str.lstrip()
        # matchObj = re.match( r"(.*?)\((.*?)\).*", key_str, re.M|re.S)
        # if matchObj:
        #     key_obj.type = matchObj.group(1)
        #     key_obj.len = matchObj.group(2)
        # else:
        #     # 不是type(len)格式
        #     matchObj = re.match( r"(.*?) .*", key_str, re.M|re.S)
        #     key_obj.type = matchObj.group(1)
        #     key_obj.type = key_obj.type.strip()
        #     key_obj.len = 0
            
        # 添加到table_obj
        table_obj.key_map[key_obj.key_name] = key_obj
    print("key_map:%s"%(table_obj.key_map.keys()))
    return sql_str

# 获取键
def get_table_key(table_obj, sql_str):
    # 获取主键
    matchObj = re.match( r"(.*)PRIMARY KEY \((.*?)\)(.*)", sql_str, re.M|re.S)
    if matchObj:
        index_obj = IndexObj()
        primary_key = matchObj.group(2)
        primary_key = primary_key.replace("`","")
        index_obj.field = primary_key.split(",")
        index_obj.field = list_del_blank(index_obj.field)
        table_obj.primary_key = index_obj
        sql_str = matchObj.group(1) + matchObj.group(3)
    # 获取联合键
    while True:
        matchObj = re.match( r"(.*)UNIQUE KEY `(.*?)` \((.*?)\)(.*)", sql_str, re.M|re.S)
        if matchObj:
            index_obj = IndexObj()
            index_obj.name = matchObj.group(2)
            unique_key = matchObj.group(3)
            unique_key = unique_key.replace("`","")
            index_obj.field = unique_key.split(",")
            index_obj.field = list_del_blank(index_obj.field)
            table_obj.unique_key[index_obj.name] = index_obj
            sql_str = matchObj.group(1) + matchObj.group(4)
        else:
            break
    # 获取普通键
    while True :
        matchObj = re.match( r"(.*)KEY `(.*?)` \(`(.*?)`\)(.*)", sql_str, re.M|re.S)
        if matchObj:
            index_obj = IndexObj()
            index_obj.name = matchObj.group(2)
            key_list = matchObj.group(3)
            key_list = key_list.replace("`","")
            index_obj.field = key_list.split(",")
            index_obj.field = list_del_blank(index_obj.field)
            table_obj.ordinary_key[index_obj.name] = index_obj
            sql_str = matchObj.group(1) + matchObj.group(4)
        else:
            break

# 生成两个表的差异sql， 第一个表为主
def table_diff(new_table, old_table):
    sql_str = ""
    table_name = new_table.table_name
    # 添加和修改的字段
    for key_name in new_table.key_map:
        new_key_obj:KeyObj = new_table.key_map[key_name]
        # 是否新字段
        if key_name not in old_table.key_map:
            sql_str += "ALTER TABLE %s ADD "%(table_name)
            sql_str += (key_obj_get_sql(new_key_obj))
        else:
            # 字段存在
            # 检查差异
            old_key_obj = old_table.key_map[key_name]
            # 字段类型和长度
            # or new_key_obj.not_null != old_key_obj.not_null \
            if new_key_obj.type.lower() != old_key_obj.type.lower() \
                or new_key_obj.len != old_key_obj.len \
                or new_key_obj.default.lower() != old_key_obj.default.lower() \
                or new_key_obj.unsigned != old_key_obj.unsigned \
                or new_key_obj.comment != old_key_obj.comment:
                    sql_str += ("ALTER TABLE %s MODIFY "%(table_name) + key_obj_get_sql(new_key_obj))
    # 删除的字段
    for key_name in old_table.key_map:
        if key_name not in new_table.key_map:
            sql_str += ("ALTER TABLE %s DROP %s;\n")%(table_name, key_name)
    
    # 索引
    # 主键
    primary_key_sql = ""
    new_primary_key = new_table.primary_key
    old_primary_key = old_table.primary_key
    if not new_primary_key and not old_primary_key:
        # 新表,旧表主键都不存在
        pass
    elif new_primary_key and not old_primary_key:
        # 新表主键存在 旧表主键不存在
        # 添加主键
        primary_key_str = ",".join(new_primary_key.field)
        primary_key_sql = "ALTER TABLE {0} ADD PRIMARY KEY ({1});\n".format(
            table_name
            , primary_key_str
        )
    elif new_primary_key and old_primary_key:
        # 新表主键存在 旧表主键也存在
        if not list_is_same(new_primary_key.field, old_primary_key.field):
            # 主键不一致
            primary_key_sql = "ALTER TABLE {0} DROP PRIMARY KEY;\n".format(table_name)
            primary_key_str = ",".join(new_primary_key.field)
            primary_key_sql += "ALTER TABLE {0} ADD PRIMARY KEY ({1});\n".format(
                table_name
                , primary_key_str
            )
    elif not new_primary_key and old_primary_key:
        # 新表主键不存在 旧表主键存在
        primary_key_sql = "ALTER TABLE {0} DROP PRIMARY KEY;\n".format(table_name)
    sql_str += primary_key_sql
    
    # 联合键
    # 添加和修改的键
    new_unique_key = new_table.unique_key
    old_unique_key = old_table.unique_key
    for tmp_key in new_unique_key:
        unique_key_str = ",".join(new_unique_key[tmp_key].field)
        if tmp_key not in old_unique_key:
            # 旧表不存在
            sql_str += "ALTER TABLE {0} ADD UNIQUE {1}({2});\n".format(table_name, tmp_key, unique_key_str)
        elif not list_is_same(old_unique_key[tmp_key].field, new_unique_key[tmp_key].field):
            # 键存在，但值不一致
            sql_str += "ALTER TABLE {0} DROP INDEX {1};\n".format(table_name, tmp_key)
            sql_str += "ALTER TABLE {0} ADD UNIQUE {1}({2});\n".format(table_name, tmp_key, unique_key_str)
    # 删除的键
    for tmp_key in old_unique_key:
        if tmp_key not in new_unique_key:
            sql_str += "ALTER TABLE {0} DROP INDEX {1};\n".format(table_name, tmp_key)
            
    # 普通键
    new_ordinary_key = new_table.ordinary_key
    old_ordinary_key = old_table.ordinary_key
    for tmp_key in new_ordinary_key:
        ordinary_key_str = ",".join(new_ordinary_key[tmp_key].field)
        if tmp_key not in old_ordinary_key:
            # 旧表不存在
            sql_str += "ALTER TABLE {0} ADD INDEX {1}({2});\n".format(table_name, tmp_key, ordinary_key_str)
        elif not list_is_same(old_ordinary_key[tmp_key].field, new_ordinary_key[tmp_key].field):
            # 键存在，但值不一致
            sql_str += "ALTER TABLE {0} DROP INDEX {1};\n".format(table_name, tmp_key)
            sql_str += "ALTER TABLE {0} ADD INDEX {1}({2});\n".format(table_name, tmp_key, ordinary_key_str)
    # 删除的键
    for tmp_key in old_ordinary_key:
        if tmp_key not in new_ordinary_key:
            sql_str += "ALTER TABLE {0} DROP INDEX {1};\n".format(table_name, tmp_key)
    
    # 表的属性
    # 暂时不考虑改这个
    return sql_str

# 获取字段类对应sql
def key_obj_get_sql(key_obj):
    # 类型可能没有长度
    type_str = ""
    if key_obj.len == 0:
        type_str = key_obj.type
    else:
        type_str = "{0}({1}) {2}".format(key_obj.type, key_obj.len, key_obj.unsigned)
        
    sql_str = "{0} {1} {2}".format(
        key_obj.key_name
        , type_str
        , key_obj.not_null
    )
    # 是否有默认值
    if key_obj.default != "":
        sql_str += " DEFAULT '%s'"%(key_obj.default)
    # 是否有注释
    if key_obj.comment != "":
        sql_str += " COMMENT '%s'"%(key_obj.comment)
    sql_str += ";\n"
    return sql_str

# 两个表内容是否一致，顺序不需要一致
def list_is_same(a_list, b_list):
    if len(a_list) != len(b_list):
        return False
    
    # 遍历元素
    for item in a_list:
        if item not in b_list:
            return False
    return True

# 字符串列表删除字符串空白
def list_del_blank(list):
    new_list = []
    for tmp in list:
        tmp = tmp.strip()
        new_list.append(tmp)
    return new_list

# 获取两个字符串间的字符串
def get_str_by_begin_end(sql_str:str, begin_str:str, end_str:str):
    begin_idx = sql_str.find(begin_str)
    if begin_idx == -1:
        return "",sql_str
    begin_idx = begin_idx + len(begin_str)
    end_idx = sql_str.find(end_str, begin_idx)
    if end_idx == -1:
        return "",sql_str
    else:
        return sql_str[begin_idx : end_idx], sql_str[end_idx:]