# benchmark 与报告（刘恒弋）

本目录是 Project 1 的 benchmark 与实验报告部分。

## 核心思路

以 `data/processed-data/inner-docs.json` 为 **ground truth**，写一个**线性扫描参考实现**
（`reference.py`），与**倒排索引查询**（`candidate.py`）做交叉验证：

- 正确性：两者对同一查询返回的文档 id 集合必须一致；
- 性能：同一查询分别计时，倒排索引相对线性扫描的**加速比**是本报告的看点。

这样 benchmark **不依赖** build-index 负责人产出的 `inverted-index.json` 也能跑通
（`candidate.py` 从 inner-docs 现场构建标准倒排索引）；等对方产出后，
用 `candidate.check_index_file()` 核对文件是否与现场构建一致。

## 前置条件

1. Python 3 + `pip install pystemmer`（Porter2 词干化，与 build 侧一致）；
2. `data/processed-data/` 下就位：`mapping.json`、`inner-docs.json`、`stopword.json`。
   - `inner-docs.json` 不入 git（约 25 MB）。缺失时重建：
     `mapping.json` 的 761 个 docname 对应 `shakespeare/{docname}.html`，
     把它们复制到 `data/raw-data/{docname}.html` 后：
     ```bash
     cd src/build/preprocess && python text_process.py
     ```

## 怎么跑

```bash
cd test
python test_correctness.py   # 正确性：candidate vs reference
python benchmark.py          # 性能：构建耗时 / 查询延迟 / 加速比 / 内存
```

## 文件说明

| 文件 | 作用 |
|---|---|
| `common.py` | 加载数据 + 查询预处理（小写→词干化→去停用词→去重） |
| `reference.py` | 线性扫描参考实现，O(D×n)，作为 ground truth |
| `candidate.py` | 倒排索引构建 + 查询（`make_index` / `search_index` / `check_index_file`） |
| `queries.py` | 按 df 分档（high/mid/low）生成查询用例 |
| `test_correctness.py` | 正确性测试入口 |
| `benchmark.py` | 性能测试入口（输出按 (频段, 词数) 聚合） |
| `verify_teammate_search.py` | 交叉验证查询模块的 search 与 ground truth |
| `report.md` | 正式实验报告（中文） |
| `report-en.md` | 正式实验报告（英文版） |
| `toy_example.py` | 手工小例子：3 篇假文档，手算答案 vs 程序对照 |
| `demo.py` | 演示脚本：逐步打印倒排索引构建/查询过程 |

## 口径注意

- 查询预处理必须与 build 侧一致（`docs/preprocess-notes.md` 第三节）：小写 + Porter2 词干化。
- threshold 约定范围 (0, 1]；`threshold=0` 是退化输入，不做相等断言（倒排索引无法返回不含查询词的文档）。
- 停用词（如 `love`、`time`、`death`）在查询侧会被过滤，选词形变化测试词时要避开它们。
