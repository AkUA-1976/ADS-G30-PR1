# 交叉验证 search 模块是否和 ground truth 一致。
# 思路：用线性扫描(reference)算出标准答案(docId 集合)，
#       再用 src.search 的 search 模块跑一遍(返回 [docId, docname] 列表)，
#       取其中 docId 对照。
# 用法：在项目根目录下  python test/verify_teammate_search.py
#       （search 模块用 from src... 绝对导入，需要项目根目录在 sys.path 上）

import sys
from pathlib import Path

# 把项目根目录加进 sys.path，让 `src` 包可以被 import
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))       # 项目根目录
sys.path.insert(0, str(root / "test"))

from common import get_inner_docs, process_query
from reference import search_linear
from src.search.search import search as teammate_search


def main():
    docs = get_inner_docs()

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
    print("%-28s %6s %6s %6s" % ("用例", "标准", "search", "结果"))
    for words, threshold, label in cases:
        # 标准答案：预处理后线性扫描
        q = process_query(words)
        expected = search_linear(q, docs, threshold)

        # search 模块答案：传原始字符串进去，返回 [[docId, docname], ...]
        got_pairs = teammate_search(" ".join(words), {"threshold": threshold})
        got = set(doc_id for doc_id, _ in got_pairs)

        ok = (expected == got)
        if not ok:
            failed += 1
        print("%-28s %6d %6d %6s" % (label, len(expected), len(got),
                                     "通过" if ok else "失败"))

    print()
    if failed == 0:
        print("全部 %d 个用例通过：search 模块和 ground truth 完全一致。" % len(cases))
    else:
        print("有 %d 个用例没通过，需要检查 search 模块的实现。" % failed)


if __name__ == "__main__":
    main()
