import math
from src.search.preprocess import process
from src.search.finalReturn import final
from pathlib import Path
import json
PROJECT = Path(__file__).resolve().parent.parent.parent
with open(str(PROJECT / "data/processed-data/inverted-index.json"), 'r', encoding="utf-8") as f:
    index = json.load(f)
# index: {stemword: string -> {`totalFrequency`: int, `documentFrequency`: int, `docId`: int[]}}
with open(str(PROJECT / "data/processed-data/inner-docs.json"), 'r', encoding="utf-8") as f:
    docs = json.load(f)
# 我不确定要不要处理短语，不过对应的预处理是已经做好了

def search(ipt, config={"threshold": 1.0}):
    ipt = process(ipt)# 处理词根,删去停用词
    threshold = config["threshold"]
    n = len(ipt)# 关键词数量
    dic={}# 存储每个文件的频数
    frequency = [set() for _ in range(n)]# 从频率到文件id的一个倒排表
    for word in ipt:
        if not word in index:
            continue
        fetch = index[word]
        for id in fetch['docId']:# 顺序串行处理，效率不要太低
            if(id in dic):
                frequency[dic[id]].discard(id)
                dic[id] += 1
                frequency[dic[id]].add(id)
            else:
                dic[id] = 0
                frequency[0].add(id)
    accepted_n = math.ceil(n * threshold)
    accepted_docId = frequency[accepted_n-1:n]
    return final(accepted_docId)# 将接受的文件id转为最终返回的结果（比如文件地址、文件名等等）
