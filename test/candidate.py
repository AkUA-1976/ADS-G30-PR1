import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "processed-data"


def make_index(docs, stopwords):
    index = {}
    for doc_id, value in docs.items():
        doc_id = int(doc_id)
        words = value[1]
        for w, entry in words.items():
            if w in stopwords:
                continue
            freq = entry[0]
            if w not in index:
                index[w] = {"total-frequency": 0, "document-frequency": 0, "docId": []}
            index[w]["total-frequency"] = index[w]["total-frequency"] + freq
            index[w]["document-frequency"] = index[w]["document-frequency"] + 1
            index[w]["docId"].append(doc_id)

    for w in index:
        index[w]["docId"].sort()
    return index


def search_index(query_words, index, threshold=1.0):
    n = len(query_words)
    if n == 0:
        return set()

    need = n * threshold
    if need != int(need):
        need = int(need) + 1
    else:
        need = int(need)

    hit_count = {}
    for w in query_words:
        if w not in index:
            continue
        for doc_id in index[w]["docId"]:
            if doc_id in hit_count:
                hit_count[doc_id] = hit_count[doc_id] + 1
            else:
                hit_count[doc_id] = 1

    result = set()
    for doc_id, cnt in hit_count.items():
        if cnt >= need:
            result.add(doc_id)
    return result


def check_index_file(docs, stopwords):
    path = data_dir / "inverted-index.json"
    if not path.exists():
        return "SKIP：还没有 inverted-index.json"

    expected = make_index(docs, stopwords)
    with open(path, "r", encoding="utf-8") as f:
        actual = json.load(f)

    if set(expected.keys()) != set(actual.keys()):
        return "FAIL：词条对不上"
    for w in expected:
        e = expected[w]
        a = actual[w]
        if e["total-frequency"] != a["total-frequency"]:
            return "FAIL：" + w + " 的总次数不一致"
        if e["document-frequency"] != a["document-frequency"]:
            return "FAIL：" + w + " 的文档数不一致"
        if e["docId"] != a["docId"]:
            return "FAIL：" + w + " 的 docId 不一致"
    return "PASS：inverted-index.json 和现场构建一致"
