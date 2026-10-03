import json
import pathlib
import Stemmer
import re

# 对每篇文档分词 -> 词干化 -> 统计词频和位置，输出 inner-docs.json
# 词干化统一用 Porter2（'english'，全组一致）
stemmer = Stemmer.Stemmer('english')

with open('../../../data/processed-data/mapping.json', 'r', encoding='utf-8') as f :
        obj = json.load(f)
total_doc=0
for doc in obj:
    total_doc+=1
RAW_DATA = pathlib.Path('../../../data/raw-data')
total_dict={}
for i in range(total_doc):
    docname = obj[str(i)]
    path =  RAW_DATA / f'{docname}.html'
    total_words = []
    lenth=0
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
        text = re.sub(r'<[^>]+>', '', text)   # 去 html 标签
        p=0
        # 分词：跳过非字母，取连续字母段；连字符/撇号只在后面还跟字母时保留
        # （这样 i'll、twenty-one 不会被拆开，proved--that 也不会粘成一个词）
        while p<len(text):
            while p<len(text) and not text[p].isalpha() :
                p=p+1
            if p>=len(text):
                break
            word=""
            while p<len(text) and (text[p].isalpha() or ((text[p]=='-'or text[p]=="'")and p+1<len(text) and text[p+1].isalpha())) :
                word+=text[p].lower()   # 扫描时顺便转小写（PyStemmer 对含大写的词几乎不处理）
                p=p+1
            total_words.append(word)
            lenth+=1
    # 收集完再统一批量词干化
    total_words=stemmer.stemWords(total_words)
    j=0
    dic={}
    # 词干 -> [频率, 出现位置...]（位置是 0 起的词序）
    for j in range(len(total_words)):
        if total_words[j] not in dic:
            dic[total_words[j]]=[1,j]
        else:
            dic[total_words[j]][0]=dic[total_words[j]][0]+1
            dic[total_words[j]].append(j)
    total_dict[str(i)] = [lenth,dic]   # [该文档总词数, 词频表]
# 输出路径是相对路径，要在本目录下运行
with open('../../../data/processed-data/inner-docs.json', 'w', encoding='utf-8') as f:
    json.dump(total_dict, f, indent=2, ensure_ascii=False)