---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'be2be9a8-1b7a-4e80-abf8-9ee5c121d4df'
  PropagateID: 'be2be9a8-1b7a-4e80-abf8-9ee5c121d4df'
  ReservedCode1: '6b7c2698-8203-43d8-a965-19f2c93204d5'
  ReservedCode2: '6b7c2698-8203-43d8-a965-19f2c93204d5'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'cd0c5e4a-ac40-48b5-adb2-7a447c922f54'
  PropagateID: 'cd0c5e4a-ac40-48b5-adb2-7a447c922f54'
  ReservedCode1: '7157b171-00ec-4174-adc1-128450cc370d'
  ReservedCode2: '7157b171-00ec-4174-adc1-128450cc370d'
---

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'a2c9f68d-d4d3-4c50-945a-5575ed38b10b'
  PropagateID: 'a2c9f68d-d4d3-4c50-945a-5575ed38b10b'
  ReservedCode1: '89772c8b-d176-4071-917d-506a3bacf319'
  ReservedCode2: '89772c8b-d176-4071-917d-506a3bacf319'
---

## 课题名称

事件驱动Agent实战

## 项目背景

企业里很多业务不是等人来问才做的，而是"到点了就提醒""数据异常了就告警""外部系统发消息了就响应"。这三种触发方式对应定时、数据、外部事件三种驱动模式，把它们做成Agent，业务就能自动跑起来。

## 功能需求

- 定时触发：按计划时间自动执行业务流程，如每日商机跟进提醒
- 数据触发：监测关键业务指标，超过阈值时自动告警
- 外部事件触发：响应外部系统的消息或回调，启动对应业务流程
- 每种触发模式的行为可独立配置和观察

## 实验任务

1. 输入"每天早上9点提醒跟进商机"，验证定时Agent按计划触发
2. 输入一条超阈值的数据（如"本月客诉量120，阈值100"），验证数据告警Agent自动响应
3. 模拟一条外部事件消息，验证外部事件Agent启动对应流程
4. 观察三种触发模式的输出是否区分展示

## 提示与思考

- 定时触发用cron表达式还是循环sleep？各自有什么优缺点？
- 数据触发的阈值怎么配置才能避免频繁告警打扰用户？
- 外部事件通过Webhook还是消息队列接入？两种方式适合什么场景？