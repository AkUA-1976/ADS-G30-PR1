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

## 10. Bonus 思考

在基础功能之上，以下方向可作为加分扩展：

### 10.1 短语查询（phrase query）

现状只支持离散关键词，不支持连续短语。而 inner-docs.json 已经记录了每个词的位置列表
（position），天然具备短语查询的数据基础：对短语中相邻两个词取 posting list 交集后，
再检查位置是否连续（docId 相同且位置相差 1）。这是对现有 position 字段的自然利用，
改动小、收益直观。

### 10.2 相关性排序（TF-IDF / BM25）

现状只返回"命中的文档集合"，不区分相关度。可引入 TF-IDF 或 BM25 对命中文档打分排序，
让最相关的文档排前面。inner-docs.json 的频率信息和 inverted-index.json 的 df 信息已经
足够计算这些指标，无需改动数据结构。

### 10.3 posting list 跳表（skip pointers）

posting list 已经升序，多词合并时目前是顺序扫描。可在 posting list 上加 skip pointers
（每隔约 √L 个元素放一个跳指针），把多词合并的代价降下来，在大 df 词的多词查询下收益明显。

### 10.4 通配符查询

支持前缀 / 后缀匹配（如 king*），可用前缀树（trie）或 permuterm index 实现，
提升查询的灵活性。

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
