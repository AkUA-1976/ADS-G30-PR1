'''
在用户输入开始搜索前的预处理
负责词根转化和删除停用词
'''
import Stemmer
stemmer = Stemmer.Stemmer("english")

from pathlib import Path
import json
PROJECT = Path(__file__).resolve().parent.parent.parent
with open(str(PROJECT / "data/processed-data/stopword.json"), 'r', encoding="utf-8") as f:
    stopwords = set(json.load(f))
# stopword: {word1, word2...}

def deleteStopword(stopwords, ipt):
    deleted = set()
    for word in ipt:
        if not word in stopwords:
            deleted.add(word)
    return deleted

def normalize(text):
    ipt = []
    p=0
    while p<len(text):# 复用了text_process的处理方法
        while p<len(text) and not text[p].isalpha() :
            p=p+1
        if p>=len(text):
            break
        word=""
        while p<len(text) and (text[p].isalpha() or ((text[p]=='-'or text[p]=="'")and p+1<len(text) and text[p+1].isalpha())) :
            word+=text[p].lower()   # 扫描时顺便转小写（PyStemmer 对含大写的词几乎不处理）
            p=p+1
        ipt.append(word)
    lenth+=1
    return ipt

def process(ipt):
    ipt = normalize(ipt)
    ipt = stemmer.stemWords(ipt)
    ipt = deleteStopword(stopwords, ipt)
    return ipt