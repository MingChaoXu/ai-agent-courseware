# 数据Schema说明

本项目的数据由 `backend/data_loader.py` 程序化生成（随机种子42），首次访问时自动生成并缓存为JSON文件。

## 数据概览

| 数据集 | 文件 | 记录数 | 说明 |
|--------|------|--------|------|
| 销售记录 | sales.json | ~540条 | 18个月×5区域×8品类×3渠道 |
| 客户 | customers.json | 120个 | 含RFM分群、LTV和流失风险 |
| 商品 | products.json | 30个 | 8个品类 |
| 评论 | reviews.json | 60条 | 含情感标签和评分 |
| FAQ | faq.json | 30条 | 6个分类 |

## sales.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| date | string | 月份 (YYYY-MM) | "2024-07" |
| region | string | 区域 | "华东" |
| category | string | 品类 | "美妆个护" |
| channel | string | 渠道 | "线上直营" |
| sales_amount | float | 销售额(元) | 12580.5 |
| order_count | int | 订单数 | 142 |
| customer_count | int | 下单客户数 | 98 |
| avg_order_value | float | 客单价(元) | 88.5 |
| return_rate | float | 退货率 | 0.0523 |

**区域**: 华东、华南、华北、西南、华中

**品类**: 食品饮料、美妆个护、家居日用、数码家电、服饰鞋包、母婴用品、运动户外、宠物用品

**渠道**: 线上直营、线上分销、线下门店

## customers.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | string | 客户ID | "C001" |
| name | string | 姓名 | "张伟" |
| gender | string | 性别 | "男" |
| age | int | 年龄 | 32 |
| region | string | 所在区域 | "华东" |
| city | string | 所在城市 | "上海" |
| member_level | string | 会员等级 | "金卡" |
| recency_days | int | 最近消费天数 | 5 |
| frequency | int | 消费频次 | 28 |
| monetary | float | 消费总额(元) | 15800.0 |
| r_score | int | R评分(1-5) | 5 |
| f_score | int | F评分(1-5) | 4 |
| m_score | int | M评分(1-5) | 4 |
| segment | string | RFM分群 | "高价值活跃" |
| churn_risk | string | 流失风险 | "高" |
| preferred_category | string | 偏好品类 | "美妆个护" |
| preferred_channel | string | 偏好渠道 | "线上直营" |
| ltv | float | 客户终身价值 | 45000.0 |
| is_active | bool | 是否活跃(60天内) | true |

**RFM分群**: 高价值活跃、高价值沉睡、中价值成长、中价值稳定、低价值潜力、低价值流失

**会员等级**: 普通、银卡、金卡、黑卡

**流失风险**: 高、中、低

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
| id | string | 评论ID | "R001" |
| product_id | string | 商品ID | "P001" |
| product_name | string | 商品名称 | "鲜萃拿铁咖啡24罐装" |
| category | string | 品类 | "食品饮料" |
| rating | int | 评分(1-5) | 5 |
| content | string | 评论内容 | "质量很好，鲜萃拿铁咖啡24罐装用着很舒服，回购了" |
| sentiment | string | 情感标签 | "正面" |
| date | string | 评论日期 | "2025-06-10" |

**情感标签**: 正面、中性、负面

## faq.json 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | string | FAQ ID | "FAQ001" |
| category | string | 分类 | "退换货" |
| question | string | 问题 | "如何退货退款？" |
| answer | string | 回答 | "收到商品7天内..." |

**FAQ分类**: 订单相关、退换货、会员权益、配送物流、促销活动