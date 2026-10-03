from search import search
while(True):
    ipt = input("请输入关键词：").split()
    if(not ipt):
        break
    docs = search(ipt)
    for doc in docs:
        print(doc)