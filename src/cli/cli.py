from search import search
ipt = input("请输入关键词：").split()
docs = search(ipt)
for doc in docs:
    print(doc)