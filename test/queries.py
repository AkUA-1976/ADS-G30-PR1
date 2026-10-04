import random
import string

# 生成测试用的查询词。按"出现在多少篇文档里"（df）分成高频/中频/低频三组


def make_pool(index, n_each=40):
    # 先把所有词按 df 从小到大排好序
    items = []
    for w, info in index.items():
        items.append((info["document-frequency"], w))
    items.sort()  # 按元组第一个元素（df）排

    total = len(items)
    high = [w for df, w in items[int(total * 0.9):]]              # df 最大的 10%
    mid = [w for df, w in items[int(total * 0.45):int(total * 0.55)]]  # 中间一段
    low = [w for df, w in items[:int(total * 0.02)]]              # df 最小的 2%

    random.shuffle(high)
    random.shuffle(mid)
    random.shuffle(low)

    return {"high": high[:n_each], "mid": mid[:n_each], "low": low[:n_each]}


def make_queries(pool, sizes=[1, 2, 5, 10], each=20):
    # 对每个频段、每种词数，随机抽 each 组查询出来
    out = []
    for band, words in pool.items():
        for size in sizes:
            if len(words) < size:
                continue
            for i in range(each):
                picked = random.sample(words, size)
                out.append((band, size, picked))
    return out


def make_rare_words(index, n=10):
    # 随机拼一些不存在的词，专门用来测"查不到结果"的情况
    out = []
    while len(out) < n:
        w = "".join(random.choice(string.ascii_lowercase) for _ in range(8))
        if w not in index:
            out.append(w)
    return out
