CREATE TABLE IF NOT EXISTS `player_base` (
  `player_id` bigint(5) NOT NULL COMMENT '角色ID',
  `account` varchar(64) NOT NULL COMMENT '角色账号',
  `id` bigint(64) NOT NULL COMMENT 'id',
  `name` varchar(30) NOT NULL COMMENT 'name',
  `svr_id` bigint(30) NOT NULL COMMENT 'svr_id',
  PRIMARY KEY (`player_id`),
  KEY `name` (`name`),
  UNIQUE KEY `account` (`account`, `name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='角色基本数据';