## 课题名称

精准营销策略

## 学习目标

- 掌握PydanticOutputParser实现客户画像结构化
- 理解RFM分群模型
- 实现差异化营销推荐

## 任务要求

- 定义客户画像Pydantic模型（RFM评分、客户层级、营销策略）
- 构建LCEL Chain实现RFM分群：根据最近购买时间、频率、金额自动分层
- 基于客户层级推荐差异化营销策略

## 技术栈

- LangChain 1.x (PydanticOutputParser, ChatPromptTemplate, LCEL)

## 输入数据

模拟的客户交易记录

## 预期输出

- 结构化客户画像（含RFM评分）
- 分层营销策略推荐

## 提示与思考

- **RFM模型**：R（Recency）最近购买时间、F（Frequency）购买频率、M（Monetary）消费金额。三维度各1-5分，组合出客户价值层级。例如R=5/F=5/M=5为"重要价值客户"，R=1/F=1/M=1为"流失预警客户"。
- **PydanticOutputParser用法**：定义Pydantic模型 → 创建parser → parser.get_format_instructions()生成格式指令 → 将指令嵌入prompt → LLM输出自动解析为结构化对象。
- **LCEL Chain**：prompt | llm | parser，用管道操作符串联，数据像流水线一样依次经过处理。
- 思考：RFM分层是硬规则还是LLM判断？如果客户的R=5/F=2/M=3，该归入哪个层级？LLM如何理解这种边界情况？