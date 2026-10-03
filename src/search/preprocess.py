'''
在用户输入开始搜索前的预处理
负责词根转化和删除停用词
'''
from pathlib import Path
import json
PROJECT = Path(__file__).resolve().parent.parent.parent
with open(str(PROJECT / "data/processed-data/stopwords.json"), 'r', encoding="utf-8") as f:
    stopwords = json.load(f)

def deleteStopword(stopwords, ipt):
    deleted = set()
    for word in ipt:
        if not word in stopwords:
            deleted.add(word)
    return deleted

def stemmer():
    return 0

def process(ipt):
    ipt = stemmer(ipt)
    ipt = deleteStopword(stopwords, ipt)
    return ipt