# 《高级数据结构与算法分析》Project 1 实验报告

## 0. 基本信息

| 项目 | 内容 |
|---|---|
| 课题 | Roll Your Own Mini Search Engine（本地迷你搜索引擎） |
| 语料 | 莎士比亚全集，761 篇 HTML，938,770 token |
| 本人分工 | benchmark（基准测试）与实验报告撰写 |
| 日期 | 2026-10-04 |

---

## 1. 任务与目标

整个项目要做的是一个**给本地文件建倒排索引、按关键词查文件**的搜索引擎。
我负责的部分是：

1. **正确性验证**：确认队友写的倒排索引构建、查询结果是对的；
2. **性能测试（benchmark）**：测构建要花多少时间、查一次要多久、占多少内存；
3. **对比分析**：倒排索引 vs 线性扫描，看快多少倍，快在哪。

---

## 2. 系统架构与数据流

```
data/raw-data（761 篇 html）
  → src/build/preprocess        → mapping.json + inner-docs.json
  → src/build/stopword-processer → stopword.json
  → src/build/build-index        → inverted-index.json
  → src/search + src/cli         → 查询结果
```

几个中间文件的格式：

- `mapping.json`：`{"0": "macbeth/macbeth.1.1", ...}`，761 个 docname，键是字符串；
- `inner-docs.json`：`{"0": [length, {词干: [频率, 位置0, ...]}]}`，约 25 MB；
- `stopword.json`：停用词表（词干形态，135 词）；
- `inverted-index.json`：`{词干: {total-frequency, document-frequency, docId[]}}`。

---

## 3. 数据结构与算法设计

### 3.1 inner-docs（词频表）

每篇文档一个「词干 → [频率, 位置…]」字典。它是建索引的中间产物，也是我做正确性验证的
**ground truth（标准答案）来源**——它完整记了每篇文档里有哪几个词干。

### 3.2 inverted-index（倒排索引）

`词干 → {total-frequency, document-frequency, docId[]}`：

- `total-frequency`：这个词干在全库一共出现了多少次；
- `document-frequency`（df）：这个词干出现在多少篇文档里；
- `docId`：包含这个词干的文档 id 列表（升序，也就是 posting list）。

构建方法：**单遍扫描** inner-docs，对每个 (文档, 词干) 对累加；停用词在构建时直接过滤掉。
实测：去掉停用词后 18,401 个词条，构建 167.0 ms，峰值内存 6.9 MB。

### 3.3 查询流程

查询词 → 小写 + Porter2 词干化 → 去停用词 → 去重 → 对每个词干取它的 posting list，
统计每篇文档命中了几个词，**命中数 >= ceil(n × threshold)** 的文档入选（n 是查询词数）。

### 3.4 复杂度分析（核心）

| 方法 | 查询时间复杂度 | 空间 |
|---|---|---|
| 线性扫描 | O(D × n)，D=761，n=查询词数 | 不用额外索引 |
| 倒排索引 | O(Σ df(wᵢ)) ≈ O(n × df̄)，只访问命中词的 posting list | O(词条数 + (文档,词) 对数) ≈ 18k 词条 + 319,686 个 docId |

关键差别：线性扫描每次查询都要**把 761 篇文档全部过一遍**（代价固定不变）；
倒排索引只访问命中词的 posting list（代价和 df 成正比）。
所以**词越低频（df 越小），倒排索引优势越大**——这是下面实验要验证的核心结论。

---

## 4. 实验设计

### 4.1 正确性验证方法

以 `inner-docs.json` 为 ground truth，写一个**线性扫描参考实现**（`reference.py`），
和**倒排索引查询**（`candidate.py`）做交叉验证：同一个查询，两边返回的文档 id 集合必须一样。

用例覆盖：
- 单关键词（高频 / 中频 / 低频词）；
- 多关键词 × 不同 threshold（2 词 0.5/1.0，3 词 0.34/0.67/1.0）；
- 罕见词（0 结果）、词形变化（kill/killed/killing → kill）、停用词过滤、threshold 边界。

另外还做了**两层对队友产物的核对**（见第 5.1 节）：
一是用 `check_index_file` 比对我现场构建的索引和队友的 `inverted-index.json`；
二是用 `verify_teammate_search.py` 把队友 `search` 的结果反查回 docId，和 ground truth 逐条对照。

### 4.2 性能测试方法

- 构建耗时：`time.perf_counter` 包住 `make_index`；
- 内存：`tracemalloc` 测构建峰值内存；
- 查询延迟：按 (频段, 词数) 生成 20 组查询，每组跑 200 次取平均；
- 加速比：同一查询跑线性扫描（50 次）与倒排索引（200 次），算平均耗时比。

词频分档：high = df 前 10%，mid = 中位附近，low = df 最小的 2%。

### 4.3 实验环境

- Python 3.13，PyStemmer 3.1.0（Porter2 词干化）；
- Windows 11，单机单进程。

---

## 5. 实验结果

### 5.1 正确性

**（1）我的参考实现 vs 倒排索引：34 组用例全部通过**（`test_correctness.py`），
倒排索引查询结果和线性扫描 ground truth 完全一致。

**（2）队友 `inverted-index.json` 文件核对：PASS。**
用 `check_index_file` 把队友跑 build-index 生成的 `inverted-index.json`
和我现场从 inner-docs 构建的标准索引逐条比对，18,401 个词条的
total-frequency / document-frequency / docId 全部一致。

队友 build-index 的对账数字也全对上了：

| 指标 | 期望 | 实际 |
|---|---|---|
| 文档数 | 761 | 761 |
| token 总数 | 938,770 | 938,770 |
| 去停用词前词干数 | 18,536 | 18,536 |
| (文档,词) 对数 | 319,686 | 319,686 |
| 去停用词后词条数 | — | 18,401 |

**（3）队友 `search` 交叉验证：16 个用例全部通过。**
用 `verify_teammate_search.py` 把队友 search 返回的 docname 反查回 docId，
和 ground truth 逐条对照（单高频/中频/低频词、多词 × 多 threshold、
词形变化、罕见词、停用词），结果全部一致。

### 5.2 构建性能

| 指标 | 值 |
|---|---|
| 词条数（去停用词） | 18,401 |
| 构建耗时 | 167.0 ms |
| 峰值内存 | 6.9 MB |

### 5.3 查询延迟（倒排索引，单位 ms）

| 频段 | 1 词 | 2 词 | 5 词 | 10 词 |
|---|---|---|---|---|
| high（高频） | 0.007 | 0.011 | 0.030 | 0.049 |
| mid（中频） | 0.001 | 0.001 | 0.001 | 0.003 |
| low（低频） | 0.001 | 0.001 | 0.001 | 0.002 |

查询延迟都在**微秒级**，随词数近似线性增长；高频词因为 posting list 长所以略慢。

### 5.4 倒排索引 vs 线性扫描（加速比 = 线性耗时 / 倒排耗时）

| 频段 | 1 词 | 2 词 | 5 词 | 10 词 |
|---|---|---|---|---|
| high（高频） | 11.3× | 8.5× | 5.3× | 5.6× |
| mid（中频） | 103.9× | 107.4× | 101.4× | 93.2× |
| low（低频） | 127.8× | 125.8× | 136.3× | 136.7× |

> 建议配一张分组条形图（x=词数，系列=频段），能很直观地看出加速比随频段的变化。

---

## 6. 团队协作中发现并修复的问题

做交叉验证时，我发现队友的 search 模块**在 import 阶段就会崩**，有两个问题，都是小笔误/API 用错，
但导致整个搜索功能跑不起来。我做的是最小修改（只动有问题的行，不重写），改完 16 个用例全部通过：

1. **停用词文件名写错**：`src/search/preprocess.py` 里读的是 `stopwords.json`，
   但项目里实际文件名是 `stopword.json`（少一个 s），import 时直接 `FileNotFoundError`。
   改成 `stopword.json`。
2. **PyStemmer 用法写错**：`preprocess.py` 里写了 `stemmer(ipt)`，
   但 `Stemmer.Stemmer("english")` 返回的对象不能直接当函数调用，报
   `TypeError: 'Stemmer.Stemmer' object is not callable`。
   正确写法是 `stemmer.stemWords(ipt)`（对列表逐个取词干）。

另外，`data/processed-data/inverted-index.json` 之前是占位假数据（只有 227 字节、两条词条），
我用队友的 build-index 跑出了真实索引（4.7 MB，18,401 词条），并已通过 `check_index_file` 核对。

---

## 7. 分析与讨论

1. **加速比随 df 下降而上升**（和第 3.4 节理论一致）：线性扫描代价固定 ≈ O(D)，
   倒排索引代价 ∝ df。低频词 df 接近 1，倒排几乎 O(1)，加速比到 ~130×；
   高频词 df 接近 D，优势缩到 ~5×。
2. **加速比随词数增加略降**：词越多，要合并的 posting list 越多，而且线性扫描里
   hit 计数的常数因子相对更小。
3. **停用词的价值**：去停用词后索引词条从 18,536 → 18,401，被过滤掉的正好是 df 最高的那些词，
   既缩小了索引，又避免了"几乎每篇都命中"、没有区分度的结果。
4. **threshold 的语义**：threshold 约定为 (0, 1]；threshold=0 是退化输入——
   倒排索引没法返回"一个查询词都不含"的文档，这时它和线性扫描语义不同。
5. **绝对延迟**：微秒级延迟说明在 761 篇这个规模下两种方法都很快，加速比的意义更多体现在
   **理论复杂度和扩展性**上——数据规模涨到 10⁴~10⁶ 篇时，O(D×n) 和 O(n×df̄) 的差距会真正拉开。

---

## 8. 结论

- 倒排索引的构建和查询逻辑正确（我的 34 组用例 + 队友 search 16 组交叉验证全部通过）；
- 队友的 `inverted-index.json` 与现场构建完全一致（`check_index_file` PASS）；
- 查询延迟微秒级，索引构建 167.0 ms / 6.9 MB，规模可控；
- 实测加速比验证了理论：**词越低频，倒排索引相对线性扫描的加速比越大**（约 5×~130×）。

---

## 附录：复现方法

```bash
# 0. 数据就位（inner-docs.json 约 25 MB 不入 git，可重建）
#    mapping.json + shakespeare/ -> data/raw-data/ -> inner-docs.json
pip install pystemmer

# 1. 正确性测试（我的参考实现 vs 倒排索引）
cd test
python test_correctness.py

# 2. 核对队友的 inverted-index.json
python -c "from common import get_inner_docs,get_stopwords; from candidate import check_index_file; print(check_index_file(get_inner_docs(), get_stopwords()))"

# 3. 交叉验证队友的 search 模块
python verify_teammate_search.py

# 4. 性能测试
python benchmark.py
```

本目录文件：

- `common.py` —— 数据加载 + 查询预处理（词干化/去停用词）
- `reference.py` —— 线性扫描参考实现（ground truth）
- `candidate.py` —— 倒排索引构建与查询（含 `check_index_file`）
- `queries.py` —— 按 df 分档生成查询用例
- `test_correctness.py` —— 正确性测试入口
- `benchmark.py` —— 性能测试入口
- `verify_teammate_search.py` —— 交叉验证队友 search 模块
- `toy_example.py` —— 手工小例子：3 篇假文档，手算答案 vs 程序对照
- `demo.py` —— 演示脚本：逐步打印倒排索引构建/查询过程
