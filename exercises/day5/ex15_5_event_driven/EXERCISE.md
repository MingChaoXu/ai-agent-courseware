## 课题名称

事件驱动Agent实战

## 学习目标

- 掌握事件驱动架构，实现三种触发模式（定时/数据/外部事件）

## 项目概述

3个Agent对应三种触发模式：timer_agent(定时触发) + data_alert_agent(数据触发) + external_event_agent(外部触发)。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义各Agent的LCEL Chain

  - `timer_agent`: 按计划时间触发业务流程，如每日商机跟进提醒
  - `data_alert_agent`: 监测数据指标，超阈值时自动告警
  - `external_event_agent`: 响应外部系统事件，启动业务流程

### 步骤2：create_agent()返回包含3条Chain的字典

### 步骤3：chat()函数调用各Chain

- chat()函数调用各Chain，展示不同触发模式的行为

### 步骤4：构建FastAPI后端 + Vue前端

## 技术栈

- 多条独立LCEL Chain（每条Agent一条）
- `ChatPromptTemplate` + `StrOutputParser`
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- 多Agent协作结果，按模块分区展示

## 提示与思考

- 定时触发如何实现？cron表达式还是while循环sleep？各有什么优劣？
- 数据触发的阈值如何配置？如何避免频繁告警？
- 外部事件如何接入？Webhook还是消息队列？