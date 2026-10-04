import random
import string


def make_pool(index, n_each=40):
    items = []
    for w, info in index.items():
        items.append((info["document-frequency"], w))
    items.sort()

    total = len(items)
    high = [w for df, w in items[int(total * 0.9):]]
    mid = [w for df, w in items[int(total * 0.45):int(total * 0.55)]]
    low = [w for df, w in items[:int(total * 0.02)]]

    random.shuffle(high)
    random.shuffle(mid)
    random.shuffle(low)

    return {"high": high[:n_each], "mid": mid[:n_each], "low": low[:n_each]}


def make_queries(pool, sizes=[1, 2, 5, 10], each=20):
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
    out = []
    while len(out) < n:
        w = "".join(random.choice(string.ascii_lowercase) for _ in range(8))
        if w not in index:
            out.append(w)
    return out
