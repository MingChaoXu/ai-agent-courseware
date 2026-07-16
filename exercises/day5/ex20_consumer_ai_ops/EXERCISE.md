---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '569027cf-5fa6-4871-9d09-a26d1d1943dd'
  PropagateID: '569027cf-5fa6-4871-9d09-a26d1d1943dd'
  ReservedCode1: 'e69169d6-885a-4750-b7d9-5a3303052726'
  ReservedCode2: 'e69169d6-885a-4750-b7d9-5a3303052726'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '97fe66eb-0da2-40c7-9a05-290480e91e75'
  PropagateID: '97fe66eb-0da2-40c7-9a05-290480e91e75'
  ReservedCode1: '34375336-76bc-480f-9436-d9b0925cd12a'
  ReservedCode2: '34375336-76bc-480f-9436-d9b0925cd12a'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '95bdb1b9-1779-4586-b39d-a705c70252f7'
  PropagateID: '95bdb1b9-1779-4586-b39d-a705c70252f7'
  ReservedCode1: '22a48780-dfff-4c81-8d7f-0bf2167f7f5e'
  ReservedCode2: '22a48780-dfff-4c81-8d7f-0bf2167f7f5e'
---

## 课题名称

消费领域AI智能运营平台

## 项目背景

零售企业每天都在面对三个核心问题：销售数据怎么看、客户咨询怎么回、营销活动怎么做准。靠人工分析慢且主观，把这三件事交给AI——用自然语言问数据就能出图表，客户来咨询能自动检索知识库作答，做营销前能模拟ROI再决策。

## 功能需求

- 智能BI：用自然语言提问就能查询销售数据、计算统计指标、自动生成图表，LLM自主决定调用哪些数据工具
- 智能客服：自动识别客户意图，检索FAQ知识库生成回答，分析客户情感并按需创建工单，支持多轮对话
- 精准营销：对客户进行RFM分群，生成客户画像和情感分析报告，输出营销策略并用蒙特卡洛模拟ROI

## 实验任务

1. 输入"上个月华东区销售额多少？按品类分布呢？"，验证BI模块自动查询数据并生成图表
2. 输入"我买的商品一直没发货，已经三天了！"，验证客服模块识别意图（投诉）、检索FAQ、分析情感（愤怒）、创建工单
3. 选择"高价值沉睡"客户分群，生成画像和营销策略，运行ROI模拟器查看P10/P50/P90收益
4. 观察BI模块中LLM是如何自主推理选择工具的（ReAct模式）

## 提示与思考

- ReAct Agent和传统Chain的区别是什么？它怎么决定先调哪个工具、再调哪个？
- 客服模块为什么要先分类意图再检索？直接拿用户原话去检索FAQ会怎样？
- 蒙特卡洛模拟的P10/P50/P90分别代表什么？为什么用百分位数而不是直接报平均值？