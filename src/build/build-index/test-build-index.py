"""
冒烟测试：验证 inverted-index.json 与 inner-docs.json + stopword.json 的一致性
运行: cd src/build/build-index && python test_build_index.py
"""
import json
import random

INNER_DOCS_PATH = "../../../data/processed-data/inner-docs.json"
STOPWORD_PATH   = "../../../data/processed-data/stopword.json"
INDEX_PATH      = "../../../data/processed-data/inverted-index.json"


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_no_stopword_leaks():
    inner = load(INNER_DOCS_PATH)
    stop = load(STOPWORD_PATH)
    idx = load(INDEX_PATH)
    leaked = [w for w in stop if w in idx]
    assert not leaked, f"stopwords leaked into index: {leaked[:10]}"
    print(f"PASS: 0 stopword leaked ({len(stop)} checked)")


def test_random_stems_match_hand_count():
    inner = load(INNER_DOCS_PATH)
    stop = set(load(STOPWORD_PATH))
    idx = load(INDEX_PATH)

    random.seed(20261004)
    stems = random.sample(list(idx.keys()), 5)
    for s in stems:
        tf = 0
        docs = []
        for d_str, (_, fm) in inner.items():
            if s in fm:
                tf += fm[s][0]
                docs.append(int(d_str))
        docs.sort()
        e = idx[s]
        assert e["total-frequency"] == tf, (s, e["total-frequency"], tf)
        assert e["document-frequency"] == len(docs), s
        assert e["docId"] == docs, s
        print(f"PASS: hand-counted {s!r}: "
              f"tf={tf}, df={len(docs)}, docId[:5]={docs[:5]}")


def test_distinct_stem_count():
    inner = load(INNER_DOCS_PATH)
    stop = set(load(STOPWORD_PATH))
    idx = load(INDEX_PATH)

    before = set()
    for _, (_, fm) in inner.items():
        before.update(fm.keys())
    expected = len(before - stop)
    assert len(idx) == expected, (len(idx), expected)
    print(f"PASS: distinct stems after filtering = {expected}")


def test_global_token_reconciliation():
    inner = load(INNER_DOCS_PATH)
    idx = load(INDEX_PATH)
    total = sum(length for length, _ in inner.values())
    indexed = sum(v["total-frequency"] for v in idx.values())
    assert 0 < indexed < total, (indexed, total)
    ratio = indexed / total
    print(f"PASS: indexed/total token ratio = {ratio:.3f} "
          f"(stopword covers {1 - ratio:.3f})")


if __name__ == "__main__":
    test_no_stopword_leaks()
    test_random_stems_match_hand_count()
    test_distinct_stem_count()
    test_global_token_reconciliation()
    print("\nALL TESTS PASSED")