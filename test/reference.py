# 这是"参考答案"：不用倒排索引，直接老老实实扫每一篇文档。
# 用它和倒排索引的结果对照，如果一样就说明索引没算错。


def search_linear(query_words, docs, threshold=1.0):
    # query_words: 已经处理好的查询词（词干化、去掉停用词、去掉重复了）
    # docs: inner-docs.json 读出来的那个字典
    # threshold: 要命中几个查询词才算匹配（比例，1.0 就是全都要命中）
    n = len(query_words)
    if n == 0:
        return set()

    # 算一下至少要命中几个词。比如 2 个词、threshold=0.5，那 ceil(1)=1 个就够
    need = n * threshold
    if need != int(need):
        need = int(need) + 1
    else:
        need = int(need)

    result = set()
    for doc_id, value in docs.items():
        words = value[1]  # value[0] 是文档总词数，这里用不到
        hit = 0
        for w in query_words:
            if w in words:
                hit = hit + 1
        if hit >= need:
            result.add(int(doc_id))
    return result
