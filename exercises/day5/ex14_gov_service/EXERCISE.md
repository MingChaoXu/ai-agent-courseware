## 课题名称

政务服务全链路Agent

## 学习目标

- 掌握多Agent协作架构，实现政务服务全链路（问答/推荐/填表/审核/复核）

## 项目概述

5个Agent协作：qa_agent(需求理解) + recommendation_agent(业务推荐) + form_filling_agent(表单填写) + verification_agent(材料审核) + review_agent(业务复核)。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义各Agent的LCEL Chain

  - `qa_agent`: 理解用户需求，提取关键信息，判断业务类型
  - `recommendation_agent`: 根据用户需求推荐合适的办理渠道和方案
  - `form_filling_agent`: 辅助填写政务表单，预填已知信息
  - `verification_agent`: 审核用户提交的材料是否齐全和合规
  - `review_agent`: 最终复核并给出办理建议

### 步骤2：create_agent()返回包含5条Chain的字典

### 步骤3：chat()函数依次调用5条Chain

- chat()函数依次调用5条Chain，将结果拼接为结构化输出

### 步骤4：构建FastAPI后端 + Vue前端

- 构建FastAPI后端 + Vue前端，展示多Agent协作全链路

## 技术栈

- 多条独立LCEL Chain（每条Agent一条）
- `ChatPromptTemplate` + `StrOutputParser`
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- 多Agent协作结果，按模块分区展示

## 提示与思考

- 5个Agent是并行执行还是串行执行？如何设计Agent间的数据传递？
- System Hint机制如何实现？如何在运行时动态切换Agent的行为？
- 如何处理某个Agent执行失败的情况？容错机制如何设计？