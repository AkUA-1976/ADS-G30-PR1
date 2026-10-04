import json
from pathlib import Path

import Stemmer

root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "processed-data"

stemmer = Stemmer.Stemmer("english")

_stopwords = None


def read_json(name):
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
    return stemmer.stemWord(word.lower())


def process_query(tokens):
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
