import time
import tracemalloc

from common import get_inner_docs, get_stopwords, process_query
from reference import search_linear
from candidate import make_index, search_index
from queries import make_pool, make_queries


def average(nums):
    return sum(nums) / len(nums)


def p95(nums):
    nums = sorted(nums)
    return nums[int(len(nums) * 0.95)]


def time_avg(fn, times=100):
    ts = []
    for i in range(times):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return average(ts), p95(ts)


def main():
    print("加载数据...")
    docs = get_inner_docs()
    stop = get_stopwords()

    print("\n=== 1. 构建倒排索引 ===")
    tracemalloc.start()
    t0 = time.perf_counter()
    index = make_index(docs, stop)
    t1 = time.perf_counter()
    cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print("词条数(去掉停用词): %d" % len(index))
    print("构建耗时: %.1f ms" % ((t1 - t0) * 1000))
    print("内存峰值: %.1f MB" % (peak / 1024 / 1024))

    pool = make_pool(index)
    queries = make_queries(pool)
    all_q = []
    for band, size, words in queries:
        all_q.append((band, size, process_query(words)))

    print("\n=== 2. 查询延迟(倒排索引) ===")
    print("%-6s %-6s %10s" % ("频段", "词数", "平均(ms)"))
    for band in ["high", "mid", "low"]:
        for size in [1, 2, 5, 10]:
            ms = []
            for b, s, q in all_q:
                if b == band and s == size:
                    m, p = time_avg(lambda: search_index(q, index), 200)
                    ms.append(m)
            print("%-6s %-6d %10.3f" % (band, size, average(ms) * 1000))

    print("\n=== 3. 线性扫描 vs 倒排索引 ===")
    print("%-6s %-6s %10s %10s %8s" % ("频段", "词数", "线性(ms)", "倒排(ms)", "加速比"))
    for band in ["high", "mid", "low"]:
        for size in [1, 2, 5, 10]:
            lin = []
            idx = []
            for b, s, q in all_q:
                if b == band and s == size:
                    lm, p1 = time_avg(lambda: search_linear(q, docs), 50)
                    cm, p2 = time_avg(lambda: search_index(q, index), 200)
                    lin.append(lm)
                    idx.append(cm)
            lm = average(lin)
            cm = average(idx)
            print("%-6s %-6d %10.3f %10.3f %8.1fx" % (band, size, lm * 1000, cm * 1000, lm / cm))

    print("\n完成。")


if __name__ == "__main__":
    main()
