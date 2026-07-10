## 课题名称

医疗病历摘要

## 学习目标

- 掌握PydanticOutputParser实现结构化输出
- 理解LLM输出格式控制原理

## 任务要求

### 步骤1：定义Pydantic模型

- 定义病历结构模型，包含以下字段：
  - 患者信息（姓名、年龄、性别）
  - 主诉
  - 现病史
  - 诊断建议
- 使用 `PydanticOutputParser` 将模型转为输出解析器
- 让LLM输出严格符合模型的JSON

### 步骤2：构建LCEL Chain

- 组装 Chain：`Prompt + Parser + LLM`
- 在Prompt中注入Parser的格式指令（`parser.get_format_instructions()`）
- 运行Chain，验证输出为合法JSON

### 步骤3：多份病历生成测试

- 输入多份不同的病历描述文本
- 验证每份输出的结构化字段完整性
- 检查必填字段是否齐全、字段类型是否正确

## 技术栈

- LangChain 1.x
- `PydanticOutputParser`（结构化输出解析）
- `ChatPromptTemplate`（提示模板）
- LCEL（管道式Chain组装）

## 输入数据

- 手动输入的病历描述文本，例如：
  - "患者张某，男，55岁，反复咳嗽1月余，伴胸闷气短，既往有慢性支气管炎病史……"
  - "患者李某，女，32岁，右下腹疼痛2天，伴恶心呕吐……"

## 预期输出

- 结构化JSON病历，包含以下字段：
  - `patient_info`：患者姓名、年龄、性别
  - `chief_complaint`：主诉
  - `present_illness`：现病史
  - `diagnosis`：诊断建议

## 提示与思考

- `PydanticOutputParser` 是如何让LLM输出指定格式的？提示词中做了什么？
- 如果LLM输出的JSON不合法，Parser会怎样？有哪些容错机制？
- 除了PydanticOutputParser，还有哪些方式控制LLM输出格式（如Function Calling、JSON Mode）？各有什么优缺点？