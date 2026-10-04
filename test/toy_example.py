from reference import search_linear
from candidate import make_index, search_index


def main():
    docs = {
        "0": [3, {"king": [1, 0], "dead": [1, 1], "live": [1, 2]}],
        "1": [3, {"king": [2, 0, 1], "live": [1, 2]}],
        "2": [2, {"dead": [2, 0, 1]}],
    }
    stopwords = set()
    idx = make_index(docs, stopwords)

    failed = 0

    q1 = ["king"]
    a1_lin = search_linear(q1, docs)
    a1_idx = search_index(q1, idx)
    ok1 = (a1_lin == {0, 1} and a1_idx == {0, 1})
    if not ok1:
        failed = failed + 1
    print("Q1 king:", sorted(a1_lin), sorted(a1_idx), "->", "通过" if ok1 else "失败(期望{0,1})")

    q2 = ["king", "dead"]
    a2_lin = search_linear(q2, docs, 1.0)
    a2_idx = search_index(q2, idx, 1.0)
    ok2 = (a2_lin == {0} and a2_idx == {0})
    if not ok2:
        failed = failed + 1
    print("Q2 king+dead th=1.0:", sorted(a2_lin), sorted(a2_idx), "->", "通过" if ok2 else "失败(期望{0})")

    q3 = ["king", "dead"]
    a3_lin = search_linear(q3, docs, 0.5)
    a3_idx = search_index(q3, idx, 0.5)
    ok3 = (a3_lin == {0, 1, 2} and a3_idx == {0, 1, 2})
    if not ok3:
        failed = failed + 1
    print("Q3 king+dead th=0.5:", sorted(a3_lin), sorted(a3_idx), "->", "通过" if ok3 else "失败(期望{0,1,2})")

    print()
    if failed == 0:
        print("全部通过：3 个查询的手算结果都和程序输出一致。")
    else:
        print("有 %d 个查询没通过，需要检查。" % failed)


if __name__ == "__main__":
    main()
