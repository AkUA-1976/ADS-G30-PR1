from pathlib import Path
import json
PROJECT = Path(__file__).resolve().parent.parent.parent
with open(str(PROJECT / "data/processed-data/mapping.json"), 'r', encoding="utf-8") as f:
    mapping = json.load(f)
# mapping: {docId: int -> doc}

def final(docIdSet):
    docs = []
    for docsId in docIdSet:
        for docId in docsId:
            docs.append(mapping[str(docId)])
    return docs