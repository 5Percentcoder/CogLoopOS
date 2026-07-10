---
id: 2026-07-09-sql-query-crash-causes
type: learning-loop
status: complete
created: 2026-07-09
updated: 2026-07-09
tags:
  - learning-loop
  - sql
  - database
  - debugging
---

# SQL 查询“崩溃”是怎么造成的

## 1. 触发问题

问题原文：“SQL 中的查询崩溃是怎么造成的？”

用户随后澄清：这是**企业级 RAG 系统中的假设故障场景**，不是正在发生的数据库事故。
因此主问题是：RAG 中的自然语言请求、LLM 生成 SQL、数据库资源与服务重试，
如何组合成级联故障。

“崩溃”不是足够精确的数据库故障类型。需要先区分：

1. **SQL 层报错**：语法、对象不存在、类型转换、约束或权限问题。
2. **查询被取消**：statement timeout、人工取消、连接池或网关超时。
3. **并发失败**：锁等待、死锁、序列化冲突。
4. **资源耗尽**：内存、临时磁盘、CPU、连接数或文件描述符不足。
5. **执行计划失控**：缺索引、统计信息失真、连接顺序或中间结果集爆炸。
6. **数据库进程退出**：OOM killer、存储故障、引擎或扩展缺陷。
7. **客户端应用退出**：一次性加载过多结果、反序列化开销、应用自身内存限制。
8. **网络表现为失败**：数据库仍在执行，但客户端连接已断开。

在企业 RAG 中，一条典型级联路径是：

```mermaid
flowchart LR
    U["用户自然语言问题"] --> L["LLM 生成 SQL"]
    L --> V["SQL 校验不充分"]
    V --> Q["全表扫描 / 错误 Join / 无界结果"]
    Q --> R["CPU、内存、临时磁盘或锁等待上升"]
    R --> T["查询超时或连接断开"]
    T --> X["客户端盲目重试"]
    X --> P["连接池耗尽"]
    P --> F["整个 RAG 服务看似崩溃"]
```

例如，模型生成的 SQL 缺少租户、时间范围或 Join 条件，可能让一次本应很小的查询
变成全表扫描、笛卡尔积或大规模排序；若超时后自动重试，故障会从单请求扩大到连接池
和整个 RAG API。

本地实验只验证这条链路中的一个机制：无界结果集进入客户端后，
结果物化方式如何放大内存占用。

## 2. 当前理解

- **Fact：** SQL 报错、查询取消、连接断开、数据库进程退出和应用进程退出是不同故障。
- **Fact：** `fetchall()` 会把剩余结果一次性物化为客户端对象；分批读取可以限制
  同时驻留在 Python 内存中的结果数量。
- **Fact：** PostgreSQL 的 `EXPLAIN` 可以在不执行查询的情况下查看计划；
  `EXPLAIN ANALYZE` 会实际执行查询，因此不能把它当作无风险的生产前置校验。
- **Fact：** `statement_timeout` 和 `lock_timeout` 分别限制语句总时长和锁等待时间，
  但超时只能止损，不能修复错误 SQL 或重试风暴。
- **Unknown：** 在同一 SQLite 查询和同一结果规模下，两种读取方式的 Python
  峰值内存差距有多大。

## 3. 可证伪假设

- **Hypothesis：** 对 75,000 行、每行约 256 字节载荷的相同查询，
  `fetchall()` 的 Python 峰值跟踪内存至少是 `fetchmany(500)` 的 10 倍。
- **如果假设错误，应观察到：** 峰值内存比小于 10，或两种模式没有消费相同行数。

## 4. 实验契约

- **主要指标：** `fetchall_peak_bytes / fetchmany_peak_bytes`。
- **通过阈值：** 峰值内存比 `>= 10`。
- **护栏指标：** 两种模式都必须读取恰好 75,000 行。
- **固定变量：** Python、SQLite、SQL、行数、载荷长度；只改变客户端读取方式。
- **最小数据集：** SQLite 递归 CTE 动态生成 75,000 行，不依赖外部数据库。
- **运行命令：**

```bash
python3 experiments/2026-07-09-sql-query-crash-causes/evaluate.py
```

## 5. 证据

- **Observation：** 两种模式均消费 75,000 行，护栏通过。
- **Observation：** `fetchall()` 的 Python 峰值跟踪内存为 29,498,837 bytes，
  `fetchmany(500)` 为 392,567 bytes，前者约为后者的 `75.14` 倍。
- **Observation：** 单次运行耗时保留在原始结果中，但它不是预设判定指标，
  也不作为持久工程结论。
- **原始结果：** `experiments/2026-07-09-sql-query-crash-causes/result.json`
- **可复现性：** Python 3.13.7、SQLite 3.50.4，仅使用标准库；结果文件保存了环境参数。

## 6. 工程判断

- **Decision：** 对结果规模没有严格上界的查询，客户端默认使用有界分批读取，
  同时在 SQL 层设置合理的过滤、`LIMIT` 或分页；只有结果规模已被证明足够小时才使用
  全量物化。若驱动支持服务端游标，还要确认它是否真的避免客户端或驱动内部预缓冲。
- **Decision：** 企业 RAG 的 Text-to-SQL 工具不能把模型输出直接交给数据库。执行前至少要：
  - 使用只读、最小权限账号，并只开放必要的视图或函数；
  - 解析 SQL AST，仅允许批准的语句、表、列和函数；
  - 在数据库或可信中间层强制注入租户范围，不能依赖模型自觉添加；
  - 强制结果行数上限、语句超时、锁超时和并发配额；
  - 用普通 `EXPLAIN` 做成本、估算行数和扫描范围门禁；
  - 对超时与资源错误使用限次重试、退避和熔断，禁止立即盲重试；
  - SQL 路径失败时降级到向量检索、预定义查询或明确的暂不可用响应。
- **适用范围：** 企业 RAG 的 Text-to-SQL、关系型元数据检索和 Python DB-API
  风格客户端的大结果集读取。
- **不适用范围：** 当前实验不能证明数据库服务端 OOM、锁、执行计划、网络与具体驱动
  的行为；这些分支需要对应数据库和生产流量验证。
- **风险与限制：** SQLite 和 `tracemalloc` 不能代表所有数据库、驱动及原生内存分配。
- **需要生产数据验证的部分：** 实际驱动的游标行为、服务端游标配置、容器内存上限、
  查询超时与数据库监控证据。

## 7. 关联

- **已有知识：** [[Database Execution Plan]]、[[Database Locking]]、[[OOM]]
  （按需创建，不为填目录提前生成）
- **代码或项目：** `experiments/2026-07-09-sql-query-crash-causes/evaluate.py`
- **来源：**
  - [PostgreSQL 18: Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html)，访问于 2026-07-09
  - [PostgreSQL 18: Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html)，访问于 2026-07-09
  - [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)，访问于 2026-07-09
  - 本地可复现实验

## 8. 未来复用触发器

遇到 RAG 的 SQL 工具生成无界查询、遗漏租户条件、产生复杂 Join、超时后反复重试，
或者代码使用 `fetchall()`、ORM `.all()`、DataFrame 全量加载时，重新调用这条记录。

## 9. 下一步

用一个隔离的 PostgreSQL 测试库做故障注入：分别验证缺少 Join 条件、缺少租户条件、
语句超时与盲重试，并记录数据库、连接池和 RAG API 三层指标。
