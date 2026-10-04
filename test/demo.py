from candidate import make_index, search_index


def main():
    docs = {
        "0": [3, {"king": [1, 0], "dead": [1, 1], "live": [1, 2]}],
        "1": [3, {"king": [2, 0, 1], "live": [1, 2]}],
        "2": [2, {"dead": [2, 0, 1]}],
    }
    stopwords = set()

    print("================ 第 1 步：构建倒排索引 ================")
    index = {}
    for doc_id in ["0", "1", "2"]:
        words = docs[doc_id][1]
        print("\n处理文档 " + doc_id + "，它包含的词：" + str(list(words.keys())))
        for w, entry in words.items():
            freq = entry[0]
            if w not in index:
                index[w] = {"total-frequency": 0, "document-frequency": 0, "docId": []}
                print("  词 '" + w + "' 第一次出现，先在索引里建个空条目")
            index[w]["total-frequency"] = index[w]["total-frequency"] + freq
            index[w]["document-frequency"] = index[w]["document-frequency"] + 1
            index[w]["docId"].append(int(doc_id))
            print("    词 '" + w + "': 总次数+" + str(freq) + "，出现文档数+1，docId 加入 " + doc_id)

    print("\n建好的倒排索引长这样：")
    for w in sorted(index):
        print("  " + w + " -> " + str(index[w]))

    print("\n================ 第 2 步：查询 ['king', 'dead']（threshold=0.5） ================")
    query = ["king", "dead"]
    threshold = 0.5
    n = len(query)
    need = n * threshold
    if need != int(need):
        need = int(need) + 1
    else:
        need = int(need)
    print("查询词 " + str(query) + "，一共 " + str(n) + " 个词")
    print("threshold=" + str(threshold) + "，所以至少要命中 " + str(int(need)) + " 个词")

    hit_count = {}
    for w in query:
        print("\n查词 '" + w + "'：")
        if w not in index:
            print("  '" + w + "' 不在索引里，跳过")
            continue
        posting = index[w]["docId"]
        print("  它的 posting list（包含它的文档 id）是 " + str(posting))
        for doc_id in posting:
            if doc_id in hit_count:
                hit_count[doc_id] = hit_count[doc_id] + 1
            else:
                hit_count[doc_id] = 1
            print("    文档 " + str(doc_id) + " 的命中数变成 " + str(hit_count[doc_id]))

    print("\n每个文档的命中数：" + str(hit_count))
    result = []
    print("命中数 >= " + str(int(need)) + " 的文档入选：")
    for doc_id, cnt in hit_count.items():
        if cnt >= need:
            result.append(doc_id)
            print("  文档 " + str(doc_id) + "（命中 " + str(cnt) + " 个）=> 入选")
        else:
            print("  文档 " + str(doc_id) + "（命中 " + str(cnt) + " 个）=> 不选")
    print("\n手推出来的结果：" + str(sorted(result)))

    print("\n================ 第 3 步：用真实的 make_index/search_index 对照 ================")
    real_idx = make_index(docs, stopwords)
    real_result = search_index(query, real_idx, threshold)
    print("真实函数 make_index 建出来的索引：")
    for w in sorted(real_idx):
        print("  " + w + " -> " + str(real_idx[w]))
    print("真实函数 search_index 的结果：" + str(sorted(real_result)))
    print("手推结果：" + str(sorted(result)))
    if sorted(result) == sorted(real_result):
        print("\n一致：手推过程和真实代码的结果对上了。")


if __name__ == "__main__":
    main()
