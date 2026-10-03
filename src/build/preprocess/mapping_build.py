import json
from pathlib import Path

# 遍历 raw-data 的场次页，生成 mapping.json（编号 -> 文档名）
pre_root = Path(__file__).resolve().parents[3]
RAW_DATA = pre_root / 'data' / 'raw-data'
set=[]
for f in RAW_DATA.rglob('*.html'):
    docname = f.relative_to(RAW_DATA).with_suffix('').as_posix()   # macbeth/macbeth.1.1
    set=set+[docname]
set.sort()   # 排序后再编号，保证每次生成结果一致
i=0
dic={}
for docname in set:
    dic[str(i)] = docname
    i=i+1

# 输出路径是相对路径，要在本目录下运行
with open('../../../data/processed-data/mapping.json', 'w', encoding='utf-8') as f:
    json.dump(dic, f, indent=2, ensure_ascii=False)
