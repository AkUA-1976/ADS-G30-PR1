def search_linear(query_words, docs, threshold=1.0):
    n = len(query_words)
    if n == 0:
        return set()

    need = n * threshold
    if need != int(need):
        need = int(need) + 1
    else:
        need = int(need)

    result = set()
    for doc_id, value in docs.items():
        words = value[1]
        hit = 0
        for w in query_words:
            if w in words:
                hit = hit + 1
        if hit >= need:
            result.add(int(doc_id))
    return result
