---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '5bcdf597-ab35-4556-834d-ca995fdd0ac9'
  PropagateID: '5bcdf597-ab35-4556-834d-ca995fdd0ac9'
  ReservedCode1: 'c82fc629-00d9-446a-9fee-93e422be69cc'
  ReservedCode2: 'c82fc629-00d9-446a-9fee-93e422be69cc'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '3a9513b1-7e7b-436b-b9fe-83ab40929e8e'
  PropagateID: '3a9513b1-7e7b-436b-b9fe-83ab40929e8e'
  ReservedCode1: 'e72927ed-7e37-4c95-bfb3-4679a2a28b5d'
  ReservedCode2: 'e72927ed-7e37-4c95-bfb3-4679a2a28b5d'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'bcc345b8-48dc-40a6-bd69-20593f51ff9b'
  PropagateID: 'bcc345b8-48dc-40a6-bd69-20593f51ff9b'
  ReservedCode1: '001fc107-d282-453b-b0c2-457deaa1ca35'
  ReservedCode2: '001fc107-d282-453b-b0c2-457deaa1ca35'
---

## 课题名称

制造业BI分析Agent

## 项目背景

工厂每天产生大量生产数据，但管理人员看报表时常常"有数据没结论"——哪条产线良品率下滑、要不要停机检修，全靠经验拍脑袋。让AI Agent自主查询数据、执行分析代码、给出决策建议，把"看报表"变成"问报表"。

## 功能需求

- 支持自然语言查询生产数据（产量、良品率、设备状态等）
- 能够执行数据分析代码，自动计算趋势、对比、异常检测等
- Agent根据问题自主决定调用哪些工具，无需人工指定分析步骤
- 工具调用过程可视化，展示推理链路

## 实验任务

1. 输入"上个月各产线良品率排名"，验证系统自动查询数据并给出分析
2. 输入"3号产线产量异常的原因分析"，验证系统执行代码进行深入分析
3. 输入简单问候语（如"你好"），验证系统不误调用工具
4. 对比同一问题下Agent模式与直接Chain模式的回答差异

## 提示与思考

- 让AI执行代码有什么安全风险？如何防止恶意代码？
- Agent自己决定调用工具的依据是什么？工具描述怎么写才能帮它选对？
- 如果数据查询结果为空，Agent应该怎么处理？