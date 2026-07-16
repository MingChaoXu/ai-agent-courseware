---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '73d42040-f73a-4fbb-a438-d19fa66cca11'
  PropagateID: '73d42040-f73a-4fbb-a438-d19fa66cca11'
  ReservedCode1: 'f24f9f95-864a-472a-8139-254ae9b03bea'
  ReservedCode2: 'f24f9f95-864a-472a-8139-254ae9b03bea'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'd0e3e792-c0ab-4f99-b7fc-a21c748f371b'
  PropagateID: 'd0e3e792-c0ab-4f99-b7fc-a21c748f371b'
  ReservedCode1: 'fd6b0577-b5fc-45f1-a3f1-77ec0af05ace'
  ReservedCode2: 'fd6b0577-b5fc-45f1-a3f1-77ec0af05ace'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '99cf8fa9-b60f-4528-aeb5-0ef83971d953'
  PropagateID: '99cf8fa9-b60f-4528-aeb5-0ef83971d953'
  ReservedCode1: 'ee08eb06-70fe-421b-8ae9-87633e9ec6b1'
  ReservedCode2: 'ee08eb06-70fe-421b-8ae9-87633e9ec6b1'
---

## 课题名称

政务服务全链路Agent

## 项目背景

市民办事经常需要跑多个环节：先问清楚要什么材料，再选办理渠道，然后填表、交材料、等审核。把这些环节拆成多个Agent协作，让市民一次输入就能走完全流程——不用自己跑腿对接每个窗口。

## 功能需求

- 理解市民的自然语言需求，判断属于哪类政务业务
- 根据业务类型推荐合适的办理渠道和所需材料清单
- 辅助预填政务表单，减少市民重复录入
- 自动审核市民提交的材料是否齐全、是否合规
- 最终复核全部信息，给出办理建议和注意事项

## 实验任务

1. 输入"我想办理新生儿落户，需要准备什么？"，验证系统从需求理解到办理建议的完整链路
2. 输入"我要办社保转移，人在苏州，社保在南京"，验证系统正确提取关键信息并推荐渠道
3. 输入一份不完整的材料清单，验证审核Agent能指出缺什么
4. 观察多个Agent的输出是否按环节分区展示，数据是否顺畅传递

## 提示与思考

- 5个Agent串行执行还是并行执行？各环节之间的数据怎么传递？
- 如果某个Agent执行失败（比如材料审核报错），整个流程该怎么处理？
- 如何让每个Agent既独立又协作——各自专注自己的职责，但结果能拼成完整建议？