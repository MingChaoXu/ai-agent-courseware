---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '51703c0b-f6b6-4c4d-a46c-6c5a57bfe376'
  PropagateID: '51703c0b-f6b6-4c4d-a46c-6c5a57bfe376'
  ReservedCode1: 'e35171ed-5141-4c1c-a5e1-0819904c4d45'
  ReservedCode2: 'e35171ed-5141-4c1c-a5e1-0819904c4d45'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'ca68bfd1-de4e-4f3c-b4a8-88f04d2284d1'
  PropagateID: 'ca68bfd1-de4e-4f3c-b4a8-88f04d2284d1'
  ReservedCode1: '14aeb7af-f9db-40c7-bb9d-2f7e088212fb'
  ReservedCode2: '14aeb7af-f9db-40c7-bb9d-2f7e088212fb'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '3b5800fa-c43e-4329-85de-f637800a0e16'
  PropagateID: '3b5800fa-c43e-4329-85de-f637800a0e16'
  ReservedCode1: '8992b777-fb0f-4f4d-86c9-58558174b12d'
  ReservedCode2: '8992b777-fb0f-4f4d-86c9-58558174b12d'
---

## 课题名称

政务通报智能生成

## 项目背景

政务通报要求格式规范、用词严谨、逻辑清晰，但起草人员反复"改措辞、调格式"耗时不少。让AI根据事件信息自动生成符合公文规范的通报文稿，包含事由、经过、结果、后续措施等要素，起草人只需审核微调。

## 功能需求

- 根据事件信息生成包含事由、经过、结果、后续措施、政策依据的规范通报
- 根据通报类型（突发事件/日常工作/政策通知）自动调整语言风格和紧急程度
- 生成的通报用语严谨，不编造不存在的法规条文作为政策依据
- 结构化输出，便于前端渲染为标准公文格式

## 实验任务

1. 输入一起突发事件信息（如"某路段自来水主管破裂导致大面积停水"），选择"突发事件"类型，验证通报包含事由、处置经过和后续措施
2. 切换为"政策通知"类型，输入同一信息，对比语言风格和紧急程度的变化
3. 检查政策依据字段是否引用了真实法规，而非AI编造的条文

## 提示与思考

- 政策依据字段如何保证准确性？LLM是否会编造法规条文？如何防范？
- 如何根据事件类型调整生成风格？Prompt中哪些因素影响公文语气？
- 政务通报的语言严谨性如何通过Prompt控制？需要哪些约束？