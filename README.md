# ADS G30 —— P0：Roll Your Own Mini Search Engine

《高级数据结构与算法分析》第一次 project（PTA 8-1）。语料：《莎士比亚全集》（shakespeare.mit.edu 镜像）。
项目理解与任务拆解另见仓库根目录《项目描述.md》；**数据格式、口径、坑：上手前先读 `docs/preprocess-notes.md`**。

## 数据流

    data/raw-data（761 篇 html，不入 git，可从 shakespeare/ 整理重建）
      →（src/build/preprocess）        → data/processed-data/mapping.json
                                        data/processed-data/inner-docs.json（约 25 MB，不入 git，可重建）
      →（src/build/stopword-processer）→ data/processed-data/stopword.json
      →（src/build/build-index）       → data/processed-data/inverted-index.json
      →（src/search、src/cli）         → 查询结果

## 目录

    src/build/preprocess/           tokenizer + stemmer + word count（→ mapping.json、inner-docs.json）
    src/build/stopword-processer/   inner-docs → stopword.json
    src/build/build-index/          inner-docs + stopword → inverted-index.json
    src/search/                     查询侧：preprocess / search / final-return
    src/cli/                        输入 / 配置 / 输出
    data/processed-data/            数据产物（inner-docs.json 不入 git：约 25 MB，可重建）
    shakespeare/                    语料镜像原样
                                   ⚠ Comedy/History/Tragedy 三个子目录是根目录同名剧的重复副本，
                                     整包统计会重复计数，不要直接全量处理
    docs/preprocess-notes.md        数据说明与注意事项（必读）
    test/

## 怎么重新生成数据

前提：Python 3 + `pip install pystemmer`；`data/raw-data/` 就位（761 篇）。
（raw-data 不入 git：它就是 mapping.json 里那 761 个 docname，从 `shakespeare/` 对应路径整理而来；
重建清单/打包找 preprocess 负责人。）

脚本用相对路径 `../../../data/…`，**必须 cd 到脚本所在目录再跑**：

    cd src/build/preprocess
    python mapping_build.py
    python text_process.py
    cd ../stopword-processer
    python stop_word_build.py

## 对账数字（交叉验证用）

- 文档数 761（mapping.json 键 `"0"`..`"760"`，连续无缺号）
- 总 token 938,770 ｜ 不同词干 18,536 ｜ (文档,词干) 对 319,686
- 抽查 length：macbeth.1.1=115 ｜ cleopatra.3.10=383 ｜ hamlet.3.1=1,641 ｜ Poetry/sonnets=1,490
