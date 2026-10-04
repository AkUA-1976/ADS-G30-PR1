"""
build-index: inner-docs.json + stopword.json => inverted-index.json

输入:
  data/processed-data/inner-docs.json
    {"docId": [length, {stem: [freq, pos0, pos1, ...]}]}
    语义: length = 该文档 token 总数 = 该文档所有 freq 之和
          stem 值列表第 0 位是频率，之后是位置
  data/processed-data/stopword.json
    已排序字符串数组，元素已经词干化，共 135 词

输出:
  data/processed-data/inverted-index.json
    {stem: {"total-frequency": int,
            "document-frequency": int,
            "docId": [int, ...]}}   # docId 升序

运行:
  cd src/build/build-index && python build_index.py

设计:
  - 单遍扫描 inner-docs.json，时间 O(总(文档, 词干)对数)
  - 只读 info[0] = freq
  - 按数字序迭代文档键，保证每个 stem 的 docId 列表天然升序
  - 停用词在 build-index 端过滤，inner-docs.json 不动
"""

import json

INNER_DOCS_PATH = "../../../data/processed-data/inner-docs.json"
STOPWORD_PATH   = "../../../data/processed-data/stopword.json"
OUTPUT_PATH     = "../../../data/processed-data/inverted-index.json"

EXPECTED_DOCS              = 761
EXPECTED_TOKENS            = 938770
EXPECTED_DISTINCT_STEMS    = 18536
EXPECTED_DOC_STEM_PAIRS    = 319686


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_inverted_index(inner_docs, stopword_set):
    """
    单遍扫描构造倒排索引。
    inner_docs: {"docId": [length, {stem: [freq, ...pos]}]}
    stopword_set: set(str)，已词干化
    返回 (index, stats)：
      index 满足 {stem: {total-frequency, document-frequency, docId[]}}
      stats 供对账用
    """
    index = {}
    all_stems_before = set()
    total_tokens = 0
    doc_stem_pairs_before = 0
    doc_stem_pairs_after = 0
    length_mismatches = []

    # 按数字序迭代，保证 docId 列表天然升序
    for doc_id_str in sorted(inner_docs.keys(), key=int):
        length, freq_map = inner_docs[doc_id_str]
        doc_id = int(doc_id_str)

        # ---- 对账: length 应等于本文档所有 freq 之和 ----
        computed_len = 0
        for stem, info in freq_map.items():
            computed_len += info[0]      # 只读第 0 位
        if computed_len != length:
            length_mismatches.append((doc_id, length, computed_len))

        total_tokens += length
        doc_stem_pairs_before += len(freq_map)
        all_stems_before.update(freq_map.keys())

        # ---- 主循环 ----
        for stem, info in freq_map.items():
            if stem in stopword_set:
                continue
            doc_stem_pairs_after += 1
            freq = info[0]

            entry = index.get(stem)
            if entry is None:
                index[stem] = {
                    "total-frequency":    freq,
                    "document-frequency": 1,
                    "docId":              [doc_id],
                }
            else:
                entry["total-frequency"]    += freq
                entry["document-frequency"] += 1
                entry["docId"].append(doc_id)

    stats = {
        "num_docs":              len(inner_docs),
        "total_tokens":          total_tokens,
        "distinct_stems_before": len(all_stems_before),
        "doc_stem_pairs_before": doc_stem_pairs_before,
        "doc_stem_pairs_after":  doc_stem_pairs_after,
        "distinct_stems_after":  len(index),
        "length_mismatches":     length_mismatches,
    }
    return index, stats


def main():
    print(f"Loading {INNER_DOCS_PATH} ...")
    inner_docs = load_json(INNER_DOCS_PATH)

    print(f"Loading {STOPWORD_PATH} ...")
    stopwords = load_json(STOPWORD_PATH)
    stopword_set = set(stopwords)

    print(f"  docs      = {len(inner_docs)}")
    print(f"  stopwords = {len(stopwords)}")

    print("Building inverted index ...")
    index, stats = build_inverted_index(inner_docs, stopword_set)

    indexed_tokens = sum(v["total-frequency"] for v in index.values())

    print("--- Reconciliation ---")
    print(f"  docs                     = {stats['num_docs']}"
          f"   (expected {EXPECTED_DOCS})")
    print(f"  total_tokens             = {stats['total_tokens']}"
          f"   (expected {EXPECTED_TOKENS})")
    print(f"  distinct_stems (before)  = {stats['distinct_stems_before']}"
          f"   (expected {EXPECTED_DISTINCT_STEMS})")
    print(f"  (doc,stem) pairs before  = {stats['doc_stem_pairs_before']}"
          f"   (expected {EXPECTED_DOC_STEM_PAIRS})")
    print(f"  (doc,stem) pairs after   = {stats['doc_stem_pairs_after']}")
    print(f"  distinct_stems (after)   = {stats['distinct_stems_after']}")
    print(f"  indexed token total      = {indexed_tokens}")
    print(f"  stopword token total     = "
          f"{stats['total_tokens'] - indexed_tokens}"
          f"   (stopword covers ~55.5%)")

    if stats["length_mismatches"]:
        print("--- length mismatches (should be empty) ---")
        for d, exp, got in stats["length_mismatches"]:
            print(f"  doc {d}: length={exp}, computed={got}")
    else:
        print("  length check: OK (每篇文档 Σfreq == length)")

    print(f"Writing {OUTPUT_PATH} ...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print("Done.")


if __name__ == "__main__":
    main()
