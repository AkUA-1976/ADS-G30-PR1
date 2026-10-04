# 手工小例子：用 3 篇假文档，手算查询结果，再和程序输出对照。
# 这个文件不碰真实数据，就是拿假数据检查倒排索引的匹配逻辑对不对。
# 用法：cd test 然后 python toy_example.py

from reference import search_linear
from candidate import make_index, search_index


def main():
    # 3 篇假文档，格式和 inner-docs.json 一样：[总词数, {词干: [频率, 位置...]}]
    # 0 号文档有 king/dead/live，1 号有 king(两次)/live，2 号有 dead(两次)
    docs = {
        "0": [3, {"king": [1, 0], "dead": [1, 1], "live": [1, 2]}],
        "1": [3, {"king": [2, 0, 1], "live": [1, 2]}],
        "2": [2, {"dead": [2, 0, 1]}],
    }
    stopwords = set()  # 小例子里先不放停用词
    idx = make_index(docs, stopwords)

    failed = 0

    # Q1: 查 king，手算答案 {0, 1}
    q1 = ["king"]
    a1_lin = search_linear(q1, docs)
    a1_idx = search_index(q1, idx)
    ok1 = (a1_lin == {0, 1} and a1_idx == {0, 1})
    if not ok1:
        failed = failed + 1
    print("Q1 king:", sorted(a1_lin), sorted(a1_idx), "->", "通过" if ok1 else "失败(期望{0,1})")

    # Q2: king + dead，threshold=1.0，手算答案 {0}
    q2 = ["king", "dead"]
    a2_lin = search_linear(q2, docs, 1.0)
    a2_idx = search_index(q2, idx, 1.0)
    ok2 = (a2_lin == {0} and a2_idx == {0})
    if not ok2:
        failed = failed + 1
    print("Q2 king+dead th=1.0:", sorted(a2_lin), sorted(a2_idx), "->", "通过" if ok2 else "失败(期望{0})")

    # Q3: king + dead，threshold=0.5，手算答案 {0, 1, 2}
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
