# 《高级数据结构与算法分析》Project 1 实验报告

## 0. 基本信息

| 项目 | 内容 |
|---|---|
| 课题 | Roll Your Own Mini Search Engine（本地迷你搜索引擎） |
| 语料 | 莎士比亚全集（shakespeare.mit.edu 镜像），761 篇 HTML |
| 日期 | 2026-10-04 |

小组分工：

| 成员 | 负责模块 | 产物 |
|---|---|---|
| 孙俊杰 | 数据预处理（preprocess）+ 停用词处理（stopword-processer） | mapping.json、inner-docs.json、stopword.json |
| 陈思羽 | 倒排索引构建（build-index） | inverted-index.json |
| 胡宏伟 | 查询（search）与命令行（cli） | 查询预处理、检索、结果返回 |
| 刘恒弋 | benchmark 与实验报告 | 验证脚本、性能测试、报告 |

---

## 1. 项目概述

项目目标是实现一个为本地文件建立**倒排索引**、并根据用户输入的关键词返回命中文件的搜索引擎。

整体流程：

```
原始 HTML（761 篇）
  → 分词 / 词干化 / 词频统计 → mapping.json + inner-docs.json
  → 停用词识别                 → stopword.json
  → 倒排索引构建               → inverted-index.json
  → 关键词查询                 → 命中文件列表
```

---

## 2. 数据初始化

语料是《莎士比亚全集》，来自 shakespeare.mit.edu 镜像，共 761 篇 HTML，每篇对应一个场次
（如 macbeth/macbeth.1.1）。

语料镜像（shakespeare/ 目录）里 Comedy / History / Tragedy 三个子目录是根目录同名剧目的
重复副本，整包处理会重复计数；因此先整理出干净的 raw-data（761 篇，去掉重复副本和
index / full 等页面），作为后续所有处理的输入。raw-data 体积较大，不纳入版本库，可由镜像按需重建。

---

## 3. 数据预处理（preprocess）

### 3.1 文档编号（mapping.json）

`mapping_build.py` 遍历 raw-data 下的全部 .html 文件，按文档路径排序后编号，生成 mapping.json：

```
{"0": "macbeth/macbeth.1.1", "1": "macbeth/macbeth.1.2", ...}
```

共 761 篇，键为字符串 "0".."760"，连续无缺号。先排序再编号，保证每次生成结果一致。

### 3.2 分词与词干化（inner-docs.json）

`text_process.py` 对每篇文档做：

1. 去 HTML 标签；
2. 分词：跳过非字母，取连续字母段；连字符 `-` 和撇号 `'` 仅当后面紧跟字母时保留
   （这样 i'll、twenty-one 不会被拆开，proved--that 也不会粘成一个词）；
3. 转小写（PyStemmer 对含大写的词几乎不处理，必须先小写）；
4. 批量词干化：用 PyStemmer 的 Porter2（"english"）算法，`stemmer.stemWords(...)`。

词干化示例：loves / loved / loving 都归到 love；thy 归到 thi。

### 3.3 词频与位置统计

对每篇文档统计「词干 → [频率, 位置0, 位置1, ...]」，输出 inner-docs.json：

```
{"文档号": [length, {词干: [频率, 位置...]}]}
```

其中 length = 该文档 token 总数 = 该文档所有频率之和（对账校验用）。位置从 0 起编号，
完整记录了每个词在文档中的出现位置，为后续短语查询等扩展保留了数据基础。

---

## 4. 停用词处理（stopword-processer）

`stop_word_build.py` 从 inner-docs.json 统计每个词干的 df（出现文档数）和总频率，
按数据驱动规则筛选停用词：

- df >= 50% 的文档（门槛 381 篇），抓"几乎每篇都出现"的词；
- 总词频占比 >= 0.1%（门槛 939 次），抓"体量大"的词。

两条规则互补（如 exit 只有 df 这条抓得到，doth 只有份额这条抓得到）。规则算完后，
人工把 19 个有查询价值的实义词（人名、身份词等，如 king、lord、queen、duke）拉回索引，
最终得到 135 个停用词，覆盖 55.5% 的词次。

停用词以词干形态存储，在 build-index 端过滤，inner-docs.json 保持全量不动。

---

## 5. 倒排索引构建（build-index）

`build-index.py` 单遍扫描 inner-docs.json，过滤停用词，构建 inverted-index.json：

```
{词干: {total-frequency, document-frequency, docId[]}}
```

- `total-frequency`：该词干在全库的出现次数之和；
- `document-frequency`（df）：出现在多少篇文档中；
- `docId`：包含该词干的文档 id 升序列表（posting list）。

按文档号升序扫描，保证每个词的 docId 列表天然升序。构建过程带对账校验：每篇文档的
length 应等于该文档所有频率之和。

对账数字：

| 指标 | 值 |
|---|---|
| 文档数 | 761 |
| 总 token | 938,770 |
| 不同词干（去停用词前） | 18,536 |
| (文档, 词干) 对 | 319,686 |
| 词条数（去停用词后） | 18,401 |

---

## 6. 查询（search + cli）

查询侧流程：

1. 用户输入关键词（cli 按空格分隔）；
2. 预处理：词干化 + 去停用词（与构建侧同一套规则，保证能查到）；
3. 检索：对每个词干取 posting list，统计每篇文档命中词数；
4. threshold 判断：`命中数 >= ceil(n × threshold)` 的文档入选（n 为查询词数）；
5. 结果返回：通过 mapping.json 把 docId 转回 docname。

threshold 是用户可配置项，表示"多个关键词中至少要命中多少个才算匹配"（如 threshold=1.0
表示全部关键词都要命中）。

---

## 7. benchmark 与实验

### 7.1 正确性验证

以 inner-docs.json 为 ground truth，写一个**线性扫描参考实现**，与**倒排索引查询**做交叉验证：
对同一查询，两者返回的文档 id 集合必须一致。

用例覆盖：单关键词（高频 / 中频 / 低频）、多关键词 × 不同 threshold（2 词 0.5/1.0，
3 词 0.34/0.67/1.0）、词形变化（kill/killed/killing）、罕见词、停用词、threshold 边界。

结果：**34 组用例全部通过**。此外对 inverted-index.json 做文件级核对（与现场构建的标准索引
逐条比对 total-frequency / document-frequency / docId），18,401 个词条全部一致。

### 7.2 性能测试方法

- 构建耗时：`time.perf_counter` 包住索引构建；
- 内存：`tracemalloc` 测构建峰值内存；
- 查询延迟：按 (频段, 词数) 生成 20 组查询，每组跑 200 次取平均；
- 加速比：同一查询跑线性扫描（50 次）与倒排索引（200 次），算平均耗时比。

词频分档：high = df 前 10%，mid = 中位附近，low = df 最小的 2%。

实验环境：Python 3.13，PyStemmer 3.1.0（Porter2），Windows 11，单机单进程。

### 7.3 构建性能

| 指标 | 值 |
|---|---|
| 词条数（去停用词） | 18,401 |
| 构建耗时 | 167.0 ms |
| 峰值内存 | 6.9 MB |

### 7.4 查询延迟（倒排索引，单位 ms）

| 频段 | 1 词 | 2 词 | 5 词 | 10 词 |
|---|---|---|---|---|
| high（高频） | 0.007 | 0.011 | 0.030 | 0.049 |
| mid（中频） | 0.001 | 0.001 | 0.001 | 0.003 |
| low（低频） | 0.001 | 0.001 | 0.001 | 0.002 |

查询延迟均在**微秒级**，随词数近似线性增长；高频词因 posting list 长而略慢。

### 7.5 倒排索引 vs 线性扫描（加速比 = 线性耗时 / 倒排耗时）

| 频段 | 1 词 | 2 词 | 5 词 | 10 词 |
|---|---|---|---|---|
| high（高频） | 11.3× | 8.5× | 5.3× | 5.6× |
| mid（中频） | 103.9× | 107.4× | 101.4× | 93.2× |
| low（低频） | 127.8× | 125.8× | 136.3× | 136.7× |

---

## 8. 复杂度分析

| 方法 | 查询时间复杂度 | 空间 |
|---|---|---|
| 线性扫描 | O(D × n)，D=761，n=查询词数 | 无需额外索引 |
| 倒排索引 | O(Σ df(wᵢ)) ≈ O(n × df̄) | O(词条数 + (文档,词) 对数) |

线性扫描每次查询都要遍历全部 761 篇文档（代价固定）；倒排索引只访问命中词的 posting list
（代价 ∝ df）。因此 **df 越小的词，加速比越大**——这与 7.5 节的实测一致。

---

## 9. 分析与讨论

1. **加速比随 df 下降而上升**：低频词 df 接近 1，倒排几乎 O(1)，加速比达 ~130×；
   高频词 df 接近 D，优势收窄到 ~5×。
2. **加速比随词数增加略降**：词越多，需要合并的 posting list 越多。
3. **停用词的价值**：去停用词后索引词条从 18,536 → 18,401，被过滤掉的正是 df 最高的词，
   既缩小了索引，又避免了"几乎每篇都命中"的无区分度结果。
4. **threshold 的语义**：约定为 (0, 1]；threshold=0 是退化输入，倒排索引无法返回
   "不含任何查询词"的文档。
5. **绝对延迟**：微秒级延迟说明在 761 篇规模下两种方法都很快，加速比的意义更多体现在
   **扩展性**上——规模增大到 10⁴~10⁶ 篇时，O(D×n) 与 O(n×df̄) 的差距会真正拉开。

---

## 10. Bonus：规模扩展性分析

题目：如果有 500,000 个文件、400,000,000 个不同单词，程序还能正常工作吗？

**直接结论：不能直接工作，主要瓶颈是内存与存储。**

### 10.1 定量估算

当前规模（实测）：

| 指标 | 值 |
|---|---|
| 文档数 | 761 |
| 不同词干 | 18,536 |
| (文档, 词干) 对 | 319,686 |
| inner-docs.json | 25 MB |
| inverted-index.json | 4.7 MB |
| 构建内存峰值 | 6.9 MB |

目标规模：500,000 文档（约 ×657）、4 亿不同词（约 ×21,580）。假设每篇文档平均词数
与当前接近（约 1,200 token），则：

- 总 token ≈ 500,000 × 1,200 ≈ 6 亿；
- 倒排索引词条数 = 4 亿。

内存估算（关键）：

- 每个词条至少含：词干字符串（平均约 10 字符）+ total-frequency（int）+
  document-frequency（int）+ docId 列表。在 Python 里，外层字典条目、内层 dict 的
  3 个 key、字符串、列表的固定开销合计约 100~200 字节/词条；
- 4 亿 × 150 字节 ≈ **60 GB**（仅词典部分，还不算 posting 里的 docId）。

posting（docId 列表）估算：

- 假设平均每个词出现在 10 篇文档，4 亿词 × 10 × 8 字节 ≈ 32 GB（这还没算 Python list
  的指针开销，实际还要再乘 3~5 倍）。

**结论：内存需求在 100 GB 量级甚至更高，远超普通单机（16~32 GB）。**

### 10.2 具体瓶颈

1. **内存**：当前实现把整个 inverted-index 和 inner-docs 都一次性加载进内存。词条数
   涨 2 万倍后，词典 + posting 轻松破百 GB，`json.load` 会直接内存不足（OOM）。
2. **存储格式**：JSON 每个词条都重复 "total-frequency"、"document-frequency"、"docId"
   三个 key，4 亿词条下这个冗余会额外膨胀几倍；JSON 文本解析也比二进制慢得多。
3. **构建时间**：单遍扫描 O(N) 的算法是对的，但 N 从 93 万 token 涨到 6 亿，构建从
   167 ms 涨到分钟级；一旦内存不足触发频繁换页（swap），会退化到小时级甚至跑不完。
4. **查询**：df 高的词（如 the）在 500,000 文件里几乎每篇都出现，posting list 长达
   几十万，单次查询遍历从微秒涨到毫秒级，多词合并更慢。
5. **Python 对象开销**：dict/list/str 每个对象都有固定开销，内存膨胀比 C 等编译型语言
   高 3~5 倍，进一步恶化内存问题。

### 10.3 如何让它工作（改进方向）

1. **词典与 posting 分离**：词典（4 亿词）用紧凑结构放内存（如 front coding / trie），
   posting list 放磁盘按需读取，查询只加载命中的 posting；
2. **posting list 压缩**：docId 已升序，改成存差值（delta）后用 var-byte / Simple-9 /
   PForDelta 编码，可压缩到原来的 1/5~1/10；
3. **二进制存储**：弃用 JSON，改用二进制格式，消除 key 冗余与序列化开销；
4. **分段构建 + 归并（merge-based indexing）**：按文档分批构建小索引，再归并成最终索引，
   峰值内存可控；
5. **分片 / 分布式**：按词或按文档把索引分片到多机（如 MapReduce 建索引），单机装不下就
   横向扩展；
6. **成熟方案**：该规模下可直接采用 Lucene / Elasticsearch 等工业级倒排索引系统，它们
   内置了上述压缩、外存、分片机制。

### 10.4 结论

在 761 篇、1.8 万词的规模下，内存驻留的朴素实现完全够用（6.9 MB、167 ms）。但在
500,000 文件、4 亿词的规模下，朴素实现会因内存与存储瓶颈而无法工作；必须引入 posting
压缩、外存索引、分段归并、分片等机制（或改用工业级搜索引擎）才能正常运行。核心结论是：
**倒排索引的算法与数据结构本身是成立的，需要改变的是存储与内存管理方式**。

---

## 11. 结论

- 项目完整实现了「原始 HTML → 词频表 → 倒排索引 → 关键词查询」的全流程；
- 倒排索引构建与查询逻辑正确（34 组交叉验证 + 文件级核对全部通过）；
- 查询延迟微秒级，索引构建 167.0 ms / 6.9 MB，规模可控；
- 实测加速比验证了理论：**词越低频，倒排索引相对线性扫描的加速比越大**（约 5×~130×）。

---

## 附录：复现方法

```bash
# 0. 数据就位（raw-data 761 篇；mapping/inner-docs/stopword 均可由脚本重建）
python -m venv .venv
.venv\Scripts\activate    # 建议在 CMD 下执行，PowerShell 有权限报错
pip install PyStemmer

# 1. 生成数据（脚本用相对路径，需 cd 到脚本所在目录）
cd src/build/preprocess
python mapping_build.py
python text_process.py
cd ../stopword-processer
python stop_word_build.py
cd ../build-index
python build-index.py

# 2. 正确性测试
cd ../../test
python test_correctness.py

# 3. 性能测试
python benchmark.py
```

test 目录文件：

- `common.py` —— 数据加载 + 查询预处理（词干化 / 去停用词）
- `reference.py` —— 线性扫描参考实现（ground truth）
- `candidate.py` —— 倒排索引构建与查询（含 `check_index_file`）
- `queries.py` —— 按 df 分档生成查询用例
- `test_correctness.py` —— 正确性测试入口
- `benchmark.py` —— 性能测试入口
- `verify_teammate_search.py` —— 交叉验证查询模块的 search
- `toy_example.py` —— 手工小例子：3 篇假文档，手算答案 vs 程序对照
- `demo.py` —— 演示脚本：逐步打印倒排索引构建 / 查询过程
