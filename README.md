# FoodExpress Analytics

一个基于 Docker 的电商大数据分析项目，主要用于学习和实践 Kafka、Flink、Spark、Airflow、PostgreSQL 等大数据技术。

## 项目功能

项目主要包括：

* 模拟生成用户和订单数据
* Kafka 接收实时订单数据
* Flink 实时处理订单数据
* PostgreSQL 保存业务数据和分析结果
* Spark 进行批量数据处理
* Airflow 定时执行数据处理任务
* Seaweedfs 保存原始数据
* Grafana 显示数据监控
* Backend 提供 API
* Frontend 提供简单的数据展示页面

## 主要技术

* Python
* Apache Kafka
* Apache Flink
* Apache Spark
* Apache Airflow
* PostgreSQL
* Redis
* Seaweedfs
* Grafana
* FastAPI / Backend
* HTML / CSS / JavaScript / Frontend
* Docker & Docker Compose

## 数据流程

```text
数据生成器
    ↓
  Kafka
    ↓
  Flink
    ↓
PostgreSQL
    ↓
 Backend
    ↓
 Frontend
```

批处理部分：

```text
Seaweedfs
  ↓
Airflow
  ↓
Spark
  ↓
PostgreSQL
```

## 启动项目

需要安装 Docker 和 Docker Compose。

克隆项目：

```bash
git clone https://github.com/imash1999/restaurants_analytics
cd restaurants_analytics

```

启动所有服务：

```bash
docker compose up -d --build
```
```bash
docker cp ecommerce_backup_after_images.sql postgres:/tmp/backup.sql
```
```bash
docker exec -i postgres psql -U postgres -d postgres -f /tmp/backup.sql
```
查看容器：

```bash
docker compose ps
```

## 访问地址

| 服务       | 地址                    |
| -------- | --------------------- |
| Frontend | http://localhost:3080 |
| Backend  | http://localhost:8000 |
| Airflow  | http://localhost:8085 |
| Flink    | http://localhost:8081 |
| Grafana  | http://localhost:3000 |


## 数据库

项目使用 PostgreSQL 保存业务数据和实时分析结果。

项目数据库：

```text
postgres
```

Airflow 使用单独的数据库：

```text
ecommerce_analytics
```

PostgreSQL 数据使用 Docker volume 保存，重新启动容器不会自动删除数据库数据。

## 停止项目

```bash
docker compose down
```

再次启动：

```bash
docker compose up -d
```

## 说明

这个项目主要用于学习和实践大数据技术，目前还在不断完善中。
