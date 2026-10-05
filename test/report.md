# 高级数据结构与算法分析 —— Project 1 实验报告

## Roll Your Own Mini Search Engine

**完成日期：2026-10-04**

小组分工：

| 成员 | 负责模块 |
|---|---|
| 王辗悠 | 数据预处理（preprocess）+ 停用词处理（stopword-processer） |
| 陈思羽 | 倒排索引构建（build-index） |
| 胡宏伟 | 查询（search）与命令行（cli） |
| 刘恒弋 | benchmark 与实验报告 |

---

# Chapter 1  Problem Description

## 1.1 要做什么（What）

本项目要**为一个本地语料库建立倒排索引（inverted index），并据此回答用户的关键词查询**。
语料是《莎士比亚全集》（shakespeare.mit.edu 镜像），共 761 篇 HTML（每篇一个场次，
如 macbeth/macbeth.1.1），全库约 93.9 万 token。

具体包含四步：

1. **词数统计与停用词识别**：扫描全部文档，统计每个词干的出现次数和文档数，
   找出"噪声词"（stop words，也叫 noisy words）——几乎每篇都出现、没有区分度的词，
   并把它们从后续索引里剔除；
2. **倒排索引构建**：对每篇文档做分词 + 词干化（stemming），记录每个词干出现在哪些文档里
   （以及词频、位置），生成倒排索引；
3. **查询**：接受用户输入的一个或多个关键词，返回包含它们的文档 ID；
4. **测试**：验证倒排索引的正确性，并展示 threshold（命中词数门槛）如何影响查询结果。

## 1.2 为什么这样做（Why）

如果不用倒排索引，每次查询都要把 761 篇文档从头到尾扫一遍，比较每个文档"含不含这个词"。
这种**线性扫描**的代价和文档总数成正比，查询越多越浪费。

倒排索引把"词 → 出现在哪些文档"的对应关系**提前算好存下来**：查一个词时直接拿到它的
posting list（包含该词的文档 id 列表），不用再扫全库。文档规模越大，这种"一次预处理、
反复快速查询"的优势越明显。本项目通过实现它、再和线性扫描做交叉对比，来理解这一信息检索
核心数据结构的设计与收益。

## 1.3 关键设计点

- **停用词的界限怎么划**：用什么指标判断一个词是"有意思"还是"噪声"，这个指标会不会随数据变化；
- **词干化**：查询词和文档词都要先归到同一词干（loves/loved/loving → love），否则查不到；
- **threshold**：多个关键词时，命中几个才算匹配，应当是用户可配置的。

---

# Chapter 2  Algorithms and Data Structures

## 2.1 数据结构

处理链路上共有四份数据产物：

| 文件 | 格式 | 含义 |
|---|---|---|
| mapping.json | `{"0": "macbeth/macbeth.1.1", ...}` | 文档编号（字符串键）→ 文档路径，761 篇 |
| inner-docs.json | `{"0": [length, {词干: [频率, 位置0, ...]}]}` | 每篇文档的词频/位置表，约 25 MB |
| stopword.json | `["词干1", "词干2", ...]` | 停用词表（词干形态，135 词） |
| inverted-index.json | `{词干: {total-frequency, document-frequency, docId[]}}` | 倒排索引 |

其中倒排索引一个词条的字段含义：

- `total-frequency`：该词干在全库的出现次数之和；
- `document-frequency`（df）：该词干出现在多少篇文档里；
- `docId`：包含该词干的文档 id 升序列表（posting list）。

inner-docs 里 `length` = 该文档 token 总数 = 该文档所有频率之和，用来对账校验。

## 2.2 词数统计与停用词识别（Word Counter）

停用词规则（数据驱动 + 人工审查）：一个词干若满足下面任一条件，判为噪声词——

- df ≥ 50% 的文档（出现在 381 篇及以上）；
- 总词频占比 ≥ 0.1%（全库出现 939 次及以上）。

规则算完后，人工把 19 个有查询价值的实义词（king、lord、queen、duke 等人名/身份词）拉回索引，
最终停用词表 135 词，覆盖全库约 55.5% 的词次。

```
for each 文档 D in raw-data:
    text = 去掉 HTML 标签后的 D 文本
    tokens = 分词(text)          // 取连续字母段；连字符/撇号仅当后面紧跟字母时保留（如 i'll、twenty-one 不拆，proved--that 拆成两词）
    for t in tokens: t = lowercase(t)
    stems = stemmer.stemWords(tokens)   // Porter2 词干化，一次批量处理
    freq_map = {}
    for j, s in enumerate(stems):
        if s not in freq_map: freq_map[s] = [1, j]
        else: freq_map[s][0] += 1; freq_map[s].append(j)
    // 整篇文档扫描完后，再一次性写入 inner_docs
    inner_docs[D.id] = [len(stems), freq_map]

// 停用词：另扫一遍 inner_docs，统计每个词干的 df 和总频率，套用上面的规则
```

## 2.3 倒排索引生成（Index Generator）

单遍扫描 inner-docs，边扫边累加；停用词直接跳过（inner-docs 保持全量不动）。

```
index = {}
for each doc_id, (length, freq_map) in inner_docs:
    for each stem, info in freq_map:
        if stem in stopwords: continue
        freq = info[0]
        if stem not in index:
            index[stem] = {"total-frequency": freq, "document-frequency": 1, "docId": [doc_id]}
        else:
            index[stem]["total-frequency"] += freq
            index[stem]["document-frequency"] += 1
            index[stem]["docId"].append(doc_id)
```

按文档号升序扫描，因此每个词的 docId 列表天然升序，无需再排序。
构建同时做对账：每篇文档的 length 应等于该文档所有频率之和。

## 2.4 查询（Query Processor）

查询词先走和构建侧完全相同的预处理（分词 + 小写 + 词干化 + 去停用词），再取 posting list 计命中数；
输入是原始字符串，内部先做分词。

```
ipt = 用户输入的原始字符串
q = normalize(ipt)              // 与构建侧相同的分词：取连续字母段并小写（连字符/撇号按同规则保留）
q = stemmer.stemWords(q)        // 词干化
q = 去掉 q 中的停用词            // 结果为去重后的词干集合
n = len(q)
need = ceil(n * threshold)      // 至少命中几个词
hit = {}
for each w in q:
    if w not in index: continue
    for each doc_id in index[w]["docId"]:
        hit[doc_id] += 1
result = { doc_id : hit[doc_id] >= need }
把 result 里的 doc_id 经 mapping.json 转回 [doc_id, 文档路径] 列表返回
```

threshold 是可配置项：threshold=1.0 表示所有关键词都要命中；越小，允许漏掉的词越多，结果越宽松。

---

# Chapter 3  Testing

测试方法：以 inner-docs.json 为 ground truth，写一个**线性扫描参考实现**与**倒排索引查询**
做交叉验证——对同一查询，两者返回的文档 id 集合必须一致。测试环境为 Python 3.13、
PyStemmer 3.1.0（Porter2）、Windows 11。

## 3.1 倒排索引正确性测试

| 用例 | 查询词 | 测试目的 | 线性扫描(篇) | 倒排索引(篇) | 是否一致 |
|---|---|---|---|---|---|
| 单高频词 | kill | 高频词检索 | 161 | 161 | 一致 |
| 单高频词 | young | 高频词检索 | 251 | 251 | 一致 |
| 单高频词 | feed | 高频词检索 | 92 | 92 | 一致 |
| 单中频词 | fledg | 中频词检索 | 2 | 2 | 一致 |
| 单中频词 | tress | 中频词检索 | 2 | 2 | 一致 |
| 单低频词 | aim'st | 低频词检索 | 1 | 1 | 一致 |
| 单低频词 | antick'd | 低频词检索 | 1 | 1 | 一致 |
| 词形变化 | killed | 词干化后应与 kill 相同 | 161 | 161 | 一致 |
| 词形变化 | killing | 词干化后应与 kill 相同 | 161 | 161 | 一致 |
| 罕见词 | wrlengme | 不存在的词应返回 0 | 0 | 0 | 一致 |
| 停用词 | love | 停用词应被过滤 | 0 | 0 | 一致 |

此外还做了**文件级核对**：把 build-index 生成的 inverted-index.json 与现场从 inner-docs 构建的
标准索引逐条比对 total-frequency / document-frequency / docId，18,401 个词条全部一致；
构建过程的对账数字（761 篇 / 938,770 token / 18,536 词干 / 319,686 对）也全部吻合。
完整自动化测试共 34 组用例，全部通过。

## 3.2 threshold 对查询的影响

| 查询词 | 词数 n | threshold | 需命中 ceil(n×th) | 结果文档数 |
|---|---|---|---|---|
| kill, king | 2 | 0.5 | 1 | 467 |
| kill, king | 2 | 1.0 | 2 | 101 |
| feed, young, king | 3 | 0.34 | 2 | 192 |
| feed, young, king | 3 | 0.67 | 3 | 26 |
| feed, young, king | 3 | 1.0 | 3 | 26 |

可见 threshold 越高，要求命中的词越多，结果越少（更严格）；threshold 越低，允许漏掉部分词，
结果越多（更宽松）。这正是 threshold 作为"匹配门槛"的预期行为。

注：feed/young/king 在 0.67 与 1.0 两行结果相同（都是 26），是因为 need = ceil(3×threshold) 在这两处都
等于 3（ceil(2.01)=3、ceil(3.0)=3），两者都要求三个词全部命中，并非巧合。

## 3.3 性能测试数据

| 指标 | 值 |
|---|---|
| 词条数（去停用词） | 18,401 |
| 构建耗时 | 167.0 ms |
| 构建峰值内存 | 6.9 MB |

查询延迟（倒排索引，单位 ms）与加速比（= 线性扫描耗时 / 倒排索引耗时）：

| 频段 | 1 词延迟 | 10 词延迟 | 1 词加速比 | 10 词加速比 |
|---|---|---|---|---|
| high（df 前 10%） | 0.007 | 0.049 | 11.3× | 5.6× |
| mid（中位附近） | 0.001 | 0.003 | 103.9× | 93.2× |
| low（df 最小 2%） | 0.001 | 0.002 | 127.8× | 136.7× |

（频段按 df 划分：high = df 前 10%，mid = 中位附近，low = df 最小的 2%。每组查询跑 200 次取平均。）

---

# Chapter 4  Complexity Analysis

## 4.1 时间复杂度

**线性扫描**：对一次查询，要遍历全部 D=761 篇文档，每篇检查 n 个查询词是否在
"该文档词干字典"里（字典查找平均 O(1)），故为 O(D × n)。代价与文档总数成正比，
和查询词是高频还是低频无关。

**倒排索引**：查每个查询词时，只遍历它自己的 posting list，长度为 df(w)；
n 个查询词合计 O(Σ df(wᵢ))，即 O(n × df̄)（df̄ 为平均 df）。查词典本身 O(n)。

两者差异的本质：线性扫描的"每篇文档"是固定项 D；倒排索引的"posting 长度"是 df，
而 df ≤ D 且低频词 df 远小于 D。所以**词越低频，倒排索引省得越多**。

## 4.2 空间复杂度

**线性扫描**：不需要任何额外索引，空间 O(1)（不计读入的 inner-docs）。

**倒排索引**：索引由"词条 + posting"构成。词条数 = 去停用词后的词干数 18,401；
posting 总长 = (文档, 词干) 对数（去停用词后）。空间 O(词条数 + Σ df) ≈ O(18k + 32 万)，
实测构建峰值内存 6.9 MB。这是"用空间换查询时间"的典型取舍。

**用到的 Python 内置结构及其复杂度**：

| 结构 | 底层 | 关键操作复杂度 |
|---|---|---|
| dict（字典） | 哈希表 | 查找 / 插入平均 O(1)，最坏 O(n) |
| set（集合） | 哈希表 | `in` 判断平均 O(1) |
| list（列表） | 动态数组 | `append` 均摊 O(1)，遍历 O(n) |
| sort() | Timsort | O(n log n) |

这些复杂度已经包含在上面的推导里：构建索引时，对每个 (文档, 词干) 对做一次 dict 查找 +
累加，均摊 O(1)，所以单遍扫描整体是 O(总 (文档, 词) 对数)；查询时命中计数用 dict 实现，
每次累加 O(1)，主要代价仍是遍历 posting list 的 O(Σ df)。

## 4.3 测试结果讨论

1. **正确性**：34 组交叉验证全部一致，说明倒排索引构建与查询逻辑正确；词形变化
   （killed/killing → kill 同结果）验证了词干化在查询侧与构建侧口径一致；停用词
   （love → 0 结果）验证了停用词过滤生效。
2. **threshold**：结果文档数随 threshold 上升而单调下降，符合 ceil(n×th) 的预期语义，
   说明 threshold 机制工作正常。
3. **加速比随 df 下降而上升**：高频词（df 接近 D）倒排索引优势最小（约 5×），低频词
   （df 接近 1）优势最大（约 130×）——与 4.1 节"代价 ∝ df"的推导一致。
4. **加速比随词数略降**：词越多，需要合并的 posting list 越多，优势被摊薄。
5. **停用词的价值**：去停用词后索引词条从 18,536 → 18,401，被剔除的正是 df 最高的词，
   既缩小了索引，又避免了"几乎每篇都命中"的无区分度结果。
6. **绝对延迟**：查询都是微秒级，说明在 761 篇规模下两种方法都很快；加速比的意义更多
   体现在规模扩大后的扩展性上（见下节 bonus）。

## 4.4 Bonus：规模扩展性分析

题目：如果有 500,000 个文件、400,000,000 个不同单词，程序还能正常工作吗？

**直接结论：不能直接工作，主要瓶颈是内存与存储。**

定量估算（当前 761 篇 / 18,536 词为基准，目标规模约 ×657 文档、×21,580 词）：

- 假设每篇文档平均约 1,200 token，总 token ≈ 6 亿；
- 倒排索引词条数 = 4 亿，每个词条含词干字符串 + total-frequency + document-frequency +
  docId 列表。在 Python 里每个词条连同字典/list 的固定开销约 100~200 字节，
  4 亿 × 150 字节 ≈ **60 GB**（仅词典部分，还不算 posting 里的 docId）；
- posting 部分若平均每词出现在 10 篇文档，4 亿 × 10 × 8 字节 ≈ 32 GB（未计 Python 列表
  的指针开销，实际还要再乘 3~5 倍）。

**合计内存需求在 100 GB 量级甚至更高，远超普通单机（16~32 GB）。**

具体瓶颈：

1. **内存**：当前实现把整个 inverted-index 和 inner-docs 一次性加载进内存，`json.load`
   会直接内存不足（OOM）；
2. **存储格式**：JSON 每个词条重复 "total-frequency" / "document-frequency" / "docId"
   三个 key，4 亿词条下冗余膨胀数倍，且文本解析慢；
3. **构建时间**：单遍扫描 O(N) 本身是对的，但 N 涨到 6 亿后构建从 167 ms 涨到分钟级；
   一旦内存不足触发换页（swap），会退化到小时级甚至跑不完；
4. **查询**：高频词（如 the）在 500,000 文件里几乎每篇都出现，posting list 长达几十万，
   单次查询从微秒涨到毫秒级；
5. **Python 对象开销**：dict/list/str 每个对象都有固定开销，内存膨胀比编译型语言高 3~5 倍。

如何让它工作（改进方向）：

1. **词典与 posting 分离**：词典用紧凑结构放内存（front coding / trie），posting 放磁盘按需读取；
2. **posting 压缩**：docId 已升序，改存差值后用 var-byte / Simple-9 / PForDelta 编码，
   可压缩到原来的 1/5~1/10；
3. **二进制存储**：弃用 JSON，消除 key 冗余；
4. **分段构建 + 归并**（merge-based indexing）：分批构建小索引再归并，峰值内存可控；
5. **分片 / 分布式**：按词或文档把索引分片到多机（如 MapReduce 建索引）；
6. **成熟方案**：直接采用 Lucene / Elasticsearch 等工业级倒排索引系统。

**结论**：在 761 篇、1.8 万词的规模下，内存驻留的朴素实现完全够用（6.9 MB、167 ms）；
但在 500,000 文件、4 亿词的规模下，朴素实现会因内存与存储瓶颈而无法工作，必须引入 posting
压缩、外存索引、分段归并、分片等机制（或改用工业级搜索引擎）。**倒排索引的算法与数据结构
本身是成立的，需要改变的是存储与内存管理方式。**
