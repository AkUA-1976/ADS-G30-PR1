from src.search.search import search
threshold = 1.0
threshold = float(input("请输入threshold参数配置："))
while(True):
    ipt = input("请输入关键词：")
    if(not ipt):
        break
    docs = search(ipt, {"threshold": threshold})
    for doc in docs:
        print(doc)
    print("----------------------------")