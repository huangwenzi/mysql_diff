# 数据库配置

# db 配置
db_map = {
    "web_svr" : {
        "host" : "localhost"                # 地址
        , "port" : 3306                     # 端口
        , "user_name" : "root"              # 用户名
        , "user_pass" : "123456"            # 密码
        , "db_name" : "bw_game_2"             # 数据库名
        , "sql_path" : "sql\\db.sql"        # 数据库sql地址
        , "out_path" : "sql\\db_diff.sql"   # diff_sql地址
    },
    "game_2" : {
        "host" : "localhost"                # 地址
        , "port" : 3306                     # 端口
        , "user_name" : "root"              # 用户名
        , "user_pass" : "123456"            # 密码
        , "db_name" : "bw_game_2"             # 数据库名
        , "sql_path" : "sql\\game_server.sql"        # 数据库sql地址
        , "out_path" : "sql\\game_server_diff.sql"   # diff_sql地址
    }
}



















