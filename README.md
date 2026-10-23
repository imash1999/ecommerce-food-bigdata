# FoodExpress Analytics

[![CI Pipeline](https://github.com/imash1999/ecommerce-food-bigdata/actions/workflows/ci.yml/badge.svg)](https://github.com/imash1999/ecommerce-food-bigdata/actions/workflows/ci.yml)

## 项目功能

项目主要包括：

* 模拟生成用户、餐厅、菜品和订单数据
* Kafka 接收实时订单事件
* Flink 实时处理订单数据
* PostgreSQL 保存业务数据和分析结果
* Spark 进行批量数据处理和客户分析
* 基于用户行为生成菜品推荐结果
* 使用 RFM 模型进行客户分群
* 对推荐结果和分析数据进行质量检查
* Airflow 定时执行数据处理任务
* SeaweedFS 保存原始数据
* Grafana 显示数据监控
* Backend 提供 API
* Frontend 提供数据展示页面

## 主要技术

* Python
* Apache Kafka
* Apache Flink
* Apache Spark
* Apache Airflow
* PostgreSQL
* SeaweedFS
* Grafana
* FastAPI / Backend
* HTML / CSS / JavaScript / Frontend
* Docker & Docker Compose

## 数据流程

实时处理部分：

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

批处理和分析部分：

```text
SeaweedFS
    ↓
  Airflow
    ↓
   Spark
    ↓
PostgreSQL
```

Spark 负责批量数据处理、RFM 客户分群和菜品推荐计算，分析结果保存到 PostgreSQL，供后续查询和展示。

## 启动项目

需要安装 Docker 和 Docker Compose。

克隆项目：

```bash
git clone https://github.com/imash1999/ecommerce-food-bigdata.git
cd ecommerce-food-bigdata
```

启动所有服务：

```bash
docker compose up -d --build
docker cp ecommerce_backup_after_images.sql postgres:/tmp/ecommerce_backup_current.sql
docker exec -i postgres psql -U postgres -d postgres -f /tmp/ecommerce_backup_current.sql
```

查看容器状态：

```bash
docker compose ps
```

如果需要恢复数据库备份，请先准备好对应的 SQL 备份文件，再根据实际的数据库配置执行恢复操作。

## 访问地址

Frontend: http://localhost:3080

Backend: http://localhost:8000/docs

Airflow: http://localhost:8085

Flink: http://localhost:8081

Grafana: http://localhost:3000

Kafka: http://localhost:8086

## 数据库

项目使用 PostgreSQL 保存业务数据、实时处理结果和批量分析结果。

业务数据库：

```text
postgres
```

Airflow 使用单独的数据库：

```text
ecommerce_analytics
```

PostgreSQL 数据使用 Docker volume 保存。执行 `docker compose down` 不会主动删除数据库 volume 中的数据。

## 停止项目

```bash
docker compose down
```
