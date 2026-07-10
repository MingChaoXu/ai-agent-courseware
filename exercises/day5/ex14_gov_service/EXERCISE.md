## 课题名称

政务服务全链路智能服务

## 学习目标

- 掌握多Agent协同架构
- 理解System Hint机制实现流程控制
- 实现事件触发的自动服务流转

## 任务要求

1. 实现5个Agent协同：接待Agent→分类Agent→办理Agent→审核Agent→反馈Agent
2. 用System Hint机制控制Agent流转方向（不硬编码if-else）
3. 实现事件触发：新咨询自动启动流程，异常情况自动升级
4. 端到端测试一个完整的政务咨询→办理→反馈流程

## 技术栈

- LangChain 1.x
- LangGraph (create_react_agent, Tool)
- TeleAgentClient

## 输入数据

- 模拟的群众咨询
- 材料提交记录
- 审批流程数据

## 预期输出

- 5个Agent的协同运行日志
- 端到端服务流程完整记录

## 提示与思考

- System Hint的本质是什么？它和硬编码分支相比有哪些优势？思考在什么场景下System Hint会失效。
- 5个Agent之间的数据如何传递？是共享状态还是消息传递？两种方式各有什么优劣？
- 事件触发模式下，如何保证同一咨询不会被重复处理？考虑幂等性设计。
- 如果审核Agent发现材料不全，流程应该如何回退？思考异常恢复机制。
- 尝试将5个Agent的流转绘制成流程图，标注每个System Hint的作用点。