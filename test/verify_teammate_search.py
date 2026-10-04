# 交叉验证队友的 search 模块是否和我们的 ground truth 一致。
# 思路：用线性扫描(reference)算出标准答案(docId 集合)，
#       再用队友的 search 跑一遍(返回 docname 列表)，
#       把 docname 反查回 docId 后对照。
# 用法：cd test 然后 python verify_teammate_search.py

import sys
from pathlib import Path

# 让脚本能 import 到 test 目录下的 common/reference，
# 以及 src/search 目录下的队友 search 模块
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "test"))
sys.path.insert(0, str(root / "src" / "search"))

import json
from common import get_inner_docs, get_stopwords, process_query, read_json
from reference import search_linear
from search import search as teammate_search


def load_mapping():
    return read_json("mapping.json")


def main():
    docs = get_inner_docs()
    stop = get_stopwords()
    mapping = load_mapping()

    # docname -> docId 的反查表
    name_to_id = {}
    for doc_id, docname in mapping.items():
        name_to_id[docname] = int(doc_id)

    # (查询词列表, threshold, 说明)
    cases = [
        (["kill"], 1.0, "单高频词 kill"),
        (["feed"], 1.0, "单高频词 feed"),
        (["young"], 1.0, "单高频词 young"),
        (["fledg"], 1.0, "单中频词 fledg"),
        (["tress"], 1.0, "单中频词 tress"),
        (["aim'st"], 1.0, "单低频词 aim'st"),
        (["antick'd"], 1.0, "单低频词 antick'd"),
        (["kill", "king"], 0.5, "两词 kill+king th0.5"),
        (["kill", "king"], 1.0, "两词 kill+king th1.0"),
        (["feed", "young", "king"], 0.34, "三词 th0.34"),
        (["feed", "young", "king"], 0.67, "三词 th0.67"),
        (["feed", "young", "king"], 1.0, "三词 th1.0"),
        (["killed"], 1.0, "词形变化 killed -> kill"),
        (["killing"], 1.0, "词形变化 killing -> kill"),
        (["wrlengme"], 1.0, "不存在的词 wrlengme"),
        (["love"], 1.0, "停用词 love(应被过滤)"),
    ]

    failed = 0
    print("对照结果：")
    print("%-28s %6s %6s %6s" % ("用例", "标准", "队友", "结果"))
    for words, threshold, label in cases:
        # 标准答案：预处理后线性扫描
        q = process_query(words)
        expected = search_linear(q, docs, threshold)

        # 队友答案：search 返回 docname 列表，反查成 docId 集合
        got_names = teammate_search(words, {"threshold": threshold})
        got = set()
        for name in got_names:
            if name in name_to_id:
                got.add(name_to_id[name])
            else:
                # 有 docname 不在 mapping 里，说明返回格式有问题
                pass

        ok = (expected == got)
        if not ok:
            failed += 1
        print("%-28s %6d %6d %6s" % (label, len(expected), len(got),
                                     "通过" if ok else "失败"))

    print()
    if failed == 0:
        print("全部 %d 个用例通过：队友 search 和 ground truth 完全一致。" % len(cases))
    else:
        print("有 %d 个用例没通过，需要检查队友 search 的实现。" % failed)


if __name__ == "__main__":
    main()
