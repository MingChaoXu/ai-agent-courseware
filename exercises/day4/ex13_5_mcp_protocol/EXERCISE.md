## 课题名称

MCP协议实践

## 学习目标

- 理解MCP (Model Context Protocol) 核心概念
- 掌握三大工具类型（感知 / 执行 / 协作）
- 实现MCP工具与LangChain的映射

## 任务要求

- 理解MCP三大工具类型：感知类（获取信息）、执行类（执行操作）、协作类（跨Agent通信）
- 实现MCP工具到LangChain Tool的映射
- 用EventDrivenAgent实现事件驱动的Agent + MCP工具协同

## 技术栈

- LangChain 1.x
- LangGraph (create_react_agent, Tool)
- training_utils (MCPClient, EventDrivenAgent)

## 输入数据

模拟的事件触发场景

## 预期输出

- MCP工具映射示例
- 事件驱动Agent运行日志

## 提示与思考

- **MCP三大工具类型**：
  - 感知类：用于获取外部信息，如查询数据库、读取文件、调用API。本质是"只读"操作，无副作用。
  - 执行类：用于执行操作，如发送邮件、写数据库、调用设备控制接口。有副作用，需谨慎授权。
  - 协作类：用于跨Agent通信，如委派子任务、请求其他Agent协助。实现多Agent协同的关键。
- **MCP → LangChain Tool映射**：MCP工具的schema可自动转换为LangChain Tool的参数定义。核心是保持工具名称、描述、参数类型的一致性。
- **事件驱动**：传统Agent是"用户提问→Agent响应"的请求-响应模式；EventDrivenAgent是"事件触发→Agent自动处理"的主动模式。例如：监控系统检测到异常→触发Agent→Agent调用工具分析→自动生成报告。
- 思考：如果一个MCP协作类工具用于向另一个Agent委派任务，而那个Agent也需要调用MCP工具，如何避免无限递归？事件驱动模式下，如何防止事件风暴（一个事件触发连锁反应导致大量事件）？