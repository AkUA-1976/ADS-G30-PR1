from preprocess import process
from finalReturn import final
from pathlib import Path
import json
PROJECT = Path(__file__).resolve().parent.parent.parent
with open(str(PROJECT / "data/processed-data/docs.json"), 'r', encoding="utf-8") as f:
    index = json.load(f)
print(index)
'''
index: {stemword: {`totalFrequency`: int, `documentFrequency`: int, `docId`: int[]}}
'''
def search(ipt, config):
    ipt = process(ipt)# 处理词根,删去停用词
    threshold = config.threshold
    n = len(ipt)# 关键词数量
    dic={}
    frequency = [set() for _ in range(n)]
    for word in ipt:
        fetch = index[word]
        for id in fetch.docId:# 顺序串行处理，效率不要太低
            if(id in dic):
                frequency[dic[id]].discard(id)
                dic[id] += 1
                frequency[dic[id]].add(id)
            else:
                dic[id] = 0
                frequency[0].add(id)
    accepted_n = int(n * threshold)
    accepted_docId = frequency[accepted_n:n]
    return final(accepted_docId)# 将接受的文件id转为最终返回的结果（比如文件地址、文件名等等）

print(PROJECT)