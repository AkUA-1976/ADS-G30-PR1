import json
from pathlib import Path

import Stemmer

# 这个文件在 test 文件夹里，往上跳一级就是项目根目录
root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "processed-data"

stemmer = Stemmer.Stemmer("english")

# 停用词读一次就存起来，后面别再反复读文件了
_stopwords = None


def read_json(name):
    # 读 processed-data 文件夹里的 json
    with open(data_dir / name, "r", encoding="utf-8") as f:
        return json.load(f)


def get_mapping():
    return read_json("mapping.json")


def get_inner_docs():
    return read_json("inner-docs.json")


def get_stopwords():
    global _stopwords
    if _stopwords is None:
        _stopwords = set(read_json("stopword.json"))
    return _stopwords


def stem(word):
    # 先变小写再词干化。这个要和 build 那边保持一致，不然查不到
    return stemmer.stemWord(word.lower())


def process_query(tokens):
    # 把用户敲进来的一串词，变成查索引用的词列表：
    # 词干化 -> 去掉停用词 -> 去掉重复（但保留顺序）
    stop = get_stopwords()
    seen = set()
    out = []
    for t in tokens:
        s = stem(t)
        if s in stop or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out
