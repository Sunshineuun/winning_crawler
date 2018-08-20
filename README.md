##### python连接oracle需要配置客户端
* 配置ORACLE客户端，代码如下
```
os.environ['path'] = 'H:\instantclient-basic-windows.x64-11.2.0.4.0\instantclient_11_2'
```
* 客户端安装包
64位的，见目录`resource\instantclient-basic-windows.x64-11.2.0.4.0.7z`

注意点：
    1. python连接oracle，需要客户端，服务端，python，cx_oracle位数一致要么32，要么多64.
    但是据说好像是64能兼容32的。