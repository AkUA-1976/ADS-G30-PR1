import sys

from common import get_inner_docs, get_stopwords, process_query
from reference import search_linear
from candidate import make_index, search_index, check_index_file
from queries import make_pool, make_rare_words

docs = get_inner_docs()
stop = get_stopwords()
index = make_index(docs, stop)

total = 0
failed = 0


def check(name, tokens, threshold=1.0):
    global total, failed
    total = total + 1
    q = process_query(tokens)
    a = search_index(q, index, threshold)    # 倒排索引查出来的
    b = search_linear(q, docs, threshold)    # 线性扫描查出来的（参考答案）
    ok = (a == b)
    if not ok:
        failed = failed + 1
    print(("[通过]" if ok else "[失败]") + " " + name + "  ->  " + str(len(a)) + " 篇")


pool = make_pool(index)

# 1. 单个词，高频/中频/低频各试几个
for band in ["high", "mid", "low"]:
    for w in pool[band][:3]:
        check("单-" + band + "-" + w, [w])

# 2. 多个词，换不同的 threshold 试
for band in ["high", "mid", "low"]:
    ws = pool[band][:4]
    if len(ws) >= 2:
        for th in [0.5, 1.0]:
            check("2词-" + band + "-th" + str(th), ws[:2], th)
    if len(ws) >= 3:
        for th in [0.34, 0.67, 1.0]:
            check("3词-" + band + "-th" + str(th), ws[:3], th)

# 3. 不存在的词，应该查到 0 篇
for w in make_rare_words(index, 3):
    check("罕见-" + w, [w])

# 4. 词形变化：kill / killed / killing 都应该归到 kill，结果一样
check("词形-kill", ["kill"])
check("词形-killed", ["killed"])
check("词形-killing", ["killing"])

# 5. 全是停用词，会被过滤成空，结果应该是 0
check("全停用词", ["the", "and", "of"])

# 6. 停用词和实义词混在一起
check("混合", ["the", "king", "and", "lord"])

# 7. threshold 边界
check("threshold-1.0", ["king"], 1.0)
check("threshold-超过1", ["king"], 2.0)

print()
print("一共 %d 组，失败 %d 组" % (total, failed))

# 8. 顺便检查队友生成的 inverted-index.json（如果有的话）
print()
print(check_index_file(docs, stop))

if failed > 0:
    sys.exit(1)
