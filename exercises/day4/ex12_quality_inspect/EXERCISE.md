---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '61c7aed5-7c21-4e22-af12-a080676c7c6a'
  PropagateID: '61c7aed5-7c21-4e22-af12-a080676c7c6a'
  ReservedCode1: 'a1aba182-2e0d-4fee-b6d1-406001266ecc'
  ReservedCode2: 'a1aba182-2e0d-4fee-b6d1-406001266ecc'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '3d7a93a6-cdb4-4fb1-9645-0794e7ed9db6'
  PropagateID: '3d7a93a6-cdb4-4fb1-9645-0794e7ed9db6'
  ReservedCode1: 'f5f11712-2249-4fd6-9579-52b895379d6f'
  ReservedCode2: 'f5f11712-2249-4fd6-9579-52b895379d6f'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '7e071081-a1c0-4e0e-96a5-a41db75bf695'
  PropagateID: '7e071081-a1c0-4e0e-96a5-a41db75bf695'
  ReservedCode1: 'a99cc8d6-2763-4ebd-aabb-3d33d3551bf7'
  ReservedCode2: 'a99cc8d6-2763-4ebd-aabb-3d33d3551bf7'
---

## 课题名称

PCB质量AI检测Agent

## 项目背景

PCB电路板出厂前要过三道关：焊点有没有连锡偏移、丝印文字是否清晰、元件数量对不对——全靠人工肉眼检查，慢且容易漏。让AI Agent像质检员一样，根据检测需求自主调用缺陷检测、OCR识别、元件计数等工具，自动完成多维度质检。

## 功能需求

- 支持PCB板焊接缺陷检测（连锡、偏移、划痕等），输出缺陷类型和位置
- 支持OCR识别PCB板丝印文字（型号、序列号、认证标识）
- 支持PCB板元件计数统计
- Agent根据用户问题自主组合多个工具完成综合检测

## 实验任务

1. 输入"检查这块PCB板的焊接缺陷"，验证系统调用缺陷检测工具并返回结果
2. 输入"识别这块板子上的丝印文字"，验证系统调用OCR工具提取型号信息
3. 输入"对这块PCB板做全面质检"，验证系统自主依次调用多个工具完成综合检测
4. 观察Agent调用工具的顺序，思考它是如何决定先调哪个后调哪个

## 提示与思考

- 工具的description描述如何影响Agent的工具选择？试试改写描述看效果变化
- 多工具协作检测时，结果矛盾怎么办？
- Mock工具返回固定结果，换成真实CV模型API需要考虑什么？