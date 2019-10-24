#### 项目目录

/home/spider/spider/association_spider/WSSpiderV2

#### 发布任务

scrapyd-deploy scrapyd2 -p WSSpiderV2

##### 添加爬虫任务

curl http://localhost:8889/schedule.json -d project=WSSpiderV2 -d spider=wanshang

删除爬虫任务

curl http://localhost:8889/cancel.json -d project=WSSpiderV2 -d job=ade462ecf61411e984f86c2b59956b44

查看项目列表

curl http://localhost:8889/listprojects.json

删除项目

curl http://localhost:8889/delproject.json -d project=WSSpiderV2