# 数据Schema说明

本项目的数据由 `backend/data_loader.py` 程序化生成（随机种子42），首次访问时自动生成并缓存为JSON文件。

## 数据概览

| 数据集 | 文件 | 记录数 | 说明 |
|--------|------|--------|------|
| 销售记录 | sales.json | ~540条 | 18个月×5区域×8品类×3渠道 |
| 客户 | customers.json | 120个 | 含RFM分群和LTV |
| 商品 | products.json | 30个 | 8个品类 |
| 评论 | reviews.json | 60条 | 含情感标签和评分 |
| FAQ | faq.json | 30条 | 6个分类 |

## sales.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| date | string | 月份 (YYYY-MM) | "2024-01" |
| region | string | 区域 | "华东" |
| category | string | 品类 | "美妆个护" |
| channel | string | 渠道 | "线上直营" |
| product_id | string | 商品ID | "P001" |
| product_name | string | 商品名称 | "鲜萃拿铁咖啡24罐装" |
| amount | float | 销售额(元) | 12580.5 |
| orders | int | 订单数 | 142 |
| quantity | int | 销售件数 | 180 |

**区域**: 华东、华南、华北、西南、华中

**品类**: 食品饮料、美妆个护、家居日用、数码家电、服饰鞋包、母婴用品、运动户外、宠物用品

**渠道**: 线上直营、线上分销、线下门店

## customers.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| customer_id | string | 客户ID | "C001" |
| name | string | 姓名 | "张三" |
| gender | string | 性别 | "男" |
| age | int | 年龄 | 32 |
| phone | string | 电话 | "138****1234" |
| member_level | string | 会员等级 | "金卡" |
| segment | string | RFM分群 | "高价值活跃" |
| recency | int | 最近消费天数 | 5 |
| frequency | int | 消费频次 | 28 |
| monetary | float | 消费总额(元) | 15800.0 |
| ltv | float | 客户终身价值 | 25000.0 |
| preferred_channel | string | 偏好渠道 | "线上直营" |
| register_date | string | 注册日期 | "2023-06-15" |

**RFM分群**: 高价值活跃、高价值沉睡、中价值成长、中价值稳定、低价值潜力、低价值流失

**会员等级**: 普通、银卡、金卡、黑卡

## products.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | string | 商品ID | "P001" |
| name | string | 商品名称 | "鲜萃拿铁咖啡24罐装" |
| category | string | 品类 | "食品饮料" |
| price | float | 售价(元) | 89.9 |
| cost | float | 成本(元) | 42.0 |

## reviews.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| review_id | string | 评论ID | "R001" |
| product_id | string | 商品ID | "P001" |
| customer_id | string | 客户ID | "C005" |
| rating | int | 评分(1-5) | 5 |
| content | string | 评论内容 | "非常好用，推荐！" |
| sentiment | string | 情感标签 | "positive" |
| date | string | 评论日期 | "2025-06-10" |

## faq.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | string | FAQ ID | "F001" |
| question | string | 问题 | "如何退货退款？" |
| answer | string | 回答 | "收到商品7天内..." |
| category | string | 分类 | "售后政策" |

**FAQ分类**: 售后政策、物流配送、会员服务、支付问题、商品咨询、优惠活动