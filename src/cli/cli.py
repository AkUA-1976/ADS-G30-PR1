from src.search.search import search
threshold = 1.0
threshold = float(input("请输入threshold参数配置："))
if not 0 < threshold <= 1:
    raise ValueError("threshold must be in (0, 1]")
while(True):
    ipt = input("请输入关键词：")
    if(not ipt):
        break
    docs = search(ipt, {"threshold": threshold})
    for doc in docs:
        print(doc[0], ": ", doc[1])
    print("----------------------------")