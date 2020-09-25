# wky_rest_api
玩客云pc客户端基础管理接口实现，只实现了单设备管理，主要做下载机用。
局域网请求签名规则没有实现，所以局域网管理功能没有
希望有了解这块的小伙伴分享下

# 配置文件说明 conf/config.ini
```
[global]
#日志级别
log_level = DEBUG
#api端口
port = 9003
[one_thing_cloud]
#用户名
username = 玩客云账号用户名
#密码
password = 密码
```

# docker run
```
docker run --name wky_rest_api \
--restart always \
-v /path/config.ini:/app/conf/config.ini \
-d gaohongliang/wky_rest_api
```