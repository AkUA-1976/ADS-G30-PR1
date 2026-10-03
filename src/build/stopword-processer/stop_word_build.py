import json

# 从 inner-docs.json 统计停用词，输出 stopword.json（词干形态，已排序）
with open("../../../data/processed-data/inner-docs.json", "r") as f:
    total_dict = json.load(f)

frequency_dict = dict()   # 词干 -> [出现的文档数, 总频率]
total_stop_words = []
total_frequency = 0

for doc in total_dict:
    for word in total_dict[doc][1]:
        if word not in frequency_dict:
            frequency_dict[word] = [1,total_dict[doc][1][word][0]]
            total_frequency +=total_dict[doc][1][word][0]
        else:
            frequency_dict[word][0] += 1
            frequency_dict[word][1] +=total_dict[doc][1][word][0]
            total_frequency += total_dict[doc][1][word][0]

for word in frequency_dict:
    # 规则：df >= 50% 的文档（total_dict 是全部文档，len = 761） 或 总词频占比 >= 0.1%
    if frequency_dict[word][0]>=0.5*len(total_dict) or frequency_dict[word][1]>=0.001*total_frequency:
        total_stop_words.append(word)

# 人工审查（2026-10-03）：以下 19 个"有查询价值"的实义词保留进索引，不进停用词表
keep_words = ["day", "duke", "eye", "father", "first", "friend", "give", "god", "hand", "hear",
              "heart", "henri", "king", "ladi", "lord", "princ", "queen", "sir", "master"]
total_stop_words = [word for word in total_stop_words if word not in keep_words]

total_stop_words = sorted(total_stop_words)
print("stop words:", len(total_stop_words))
# 输出路径是相对路径，要在本目录下运行
with open('../../../data/processed-data/stopword.json', 'w', encoding='utf-8') as f:
    json.dump(total_stop_words, f, indent=2, ensure_ascii=False)

