## 课题名称

制造业BI分析

## 学习目标

- 掌握LangGraph ReAct Agent构建
- 实现Agent自主决策何时调用工具
- 理解Agent与Chain的本质区别

## 任务要求

- 定义Python执行工具：pandas数据查询、统计计算、趋势分析
- 用langgraph.create_react_agent构建BI分析Agent
- 测试Agent能否自主决定查数据、算统计还是直接回答
- 对比Agent模式 vs 固定Chain模式的分析能力

## 技术栈

- LangChain 1.x
- LangGraph (create_react_agent, Tool)
- pandas

## 输入数据

data/production_data.json（270条生产线数据）

## 预期输出

- Agent自主决策的分析过程日志
- 多维度BI分析报告

## 提示与思考

- **Agent vs Chain的核心区别**：Chain是固定流程（输入→A→B→C→输出），Agent是自主决策（输入→思考→选工具→执行→再思考→...→输出）。Chain简单可控，Agent灵活智能。
- **ReAct循环**：Reasoning（推理当前该做什么）→ Acting（调用工具执行）→ Observing（观察结果）→ 再次Reasoning，直到得出最终答案。
- **工具设计要点**：每个工具的描述（description）要清晰准确，Agent依赖描述来决定是否调用。工具粒度要合理——太粗则灵活性差，太细则决策成本高。
- 思考：如果用户问"哪条生产线产量最高"，Agent需要调用哪些工具？如果问"帮我总结一下整体生产情况"呢？两种问题下Agent的决策路径有何不同？