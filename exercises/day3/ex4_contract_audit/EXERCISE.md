## 课题名称

合同风险审核

## 学习目标

- 掌握 PydanticOutputParser 在复杂结构化输出中的应用
- 理解 Human-in-the-Loop（HITL）审批流程
- 实现审核结果的结构化表达

## 任务要求

1. **定义审核数据模型**：
   - 使用 Pydantic BaseModel 定义合同风险审核的输出结构
   - 字段应包含：风险条款原文、风险等级（高/中/低）、修改建议、审批状态（待审批/已通过/已驳回）

2. **构建自动审核 Chain**：
   - 使用 LCEL 构建 chain：ChatPromptTemplate | LLM | PydanticOutputParser
   - 对每个合同条款进行风险识别和等级评定
   - 输出结构化审核报告

3. **实现 HITL 审批节点**：
   - 风险等级为"高"的条款，自动标记为"待审批"
   - 在终端交互中提示审核人员确认或驳回
   - 审批结果回写到审核报告中

## 技术栈

- LangChain 1.x（PydanticOutputParser, ChatPromptTemplate, LCEL）
- langchain-classic

## 输入数据

- `data/contract_samples.json`（4份合同样本，每份含多个条款）

## 预期输出

- 结构化审核报告（含风险等级和修改建议）
- 高风险条款的 HITL 审批流程交互记录

## 提示与思考

- PydanticOutputParser 如何保证 LLM 输出严格符合预期结构？如果 LLM 输出不符合格式会怎样？
- HITL 的粒度如何选择？是逐条审批还是整份合同审批？各有什么利弊？
- 风险等级的判定标准应该如何传达给 LLM？试着用 few-shot 示例提升判定的稳定性。
- 在实际电信业务中，哪些合同条款最需要 HITL 机制？