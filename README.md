# mysql_diff

# 根据sql文件更新数据库

# 安装modul
pip install pymysql==1.0.2
<!-- pip install mysqlclient-2.1.0-cp38-cp38-win_amd64.whl -->

# 使用
修改main.py, 填入你的数据库参数  
目标db.sql放在db目录下，也要修改main.py对应地址  

# 测试
python3 api.py root "Ylunnvh)G4La" 3306 test_diff ./sql/db.sql ./sql/db_diff.sql
