preprocess / stopword-processer 数据说明（组内必读）

维护：preprocess + stopword-processer 负责人。有问题随时找我。
最后更新：2026-10-03。

一、产物清单

- data/processed-data/mapping.json —— 761 篇文档编号表：{"0": "macbeth/macbeth.1.1", ...}
  键为字符串 "0".."760"，连续无缺号。
- data/processed-data/inner-docs.json —— 词频/位置表（约 25 MB），格式见第二节。
- data/processed-data/stopword.json —— 停用词表，排好序的字符串数组。

脚本位置：
- src/build/preprocess/mapping_build.py、text_process.py
- src/build/stopword-processer/stop_word_build.py

二、inner-docs.json 的格式

    {"文档号": [length, {词干: [频率, 位置0, 位置1, ...]}]}

- length = 该文档 token 总数 = 该文档所有频率之和（对账用）。
- 词值 = [频率, 后跟该词在文档中的全部出现位置（0 起编号）]：列表长度 = 频率 + 1，第 0 位是频率。
- 语义提醒：position 目前实现为"全部位置"列表，组内是否以此为准还没正式确认——
  build-index 若要用 position 字段，请先在群里说一声，避免两套理解。

三、词形（最重要的一节）

所有词键都是"小写 + 词干化"之后的形式。查询侧必须用同一套处理，否则查不到：

- 管道：整文本小写 -> 去 HTML 标签 -> 只取字母（撇号 ' 和连字符 - 仅当后面紧跟字母时保留）
  -> PyStemmer 'english'（Porter2）词干化。
- 例：loves / loved / loving -> 键都是 love；thy -> 键是 thi（不是 thy！）。
- 撇号词：tis、twas、i'll、o'er、ne'er 保留撇号形态。
- 大写坑：PyStemmer 对含大写的词几乎不处理（MACBETH 原样返回）——必须先小写再算。
- 已知"怪键"（正常现象，不是 bug）：
  - whate' 等尾部带撇号的键，共 75 个；
  - marrow- 1 个（Poetry 里 marrow-eating 的产物）；
  - 含连字符的键 2,979 个（多为 a-bird 这类 a- 前缀词）。

四、性能

- inner-docs.json 加载约 0.4 秒；"单遍扫描 + 一个累加 dict"统计全部词的频率/文档数约 0.2 秒。
- 不要写"对每个词重扫全库"的代码：实测约 44 倍工作量，且随 文档数 x 词数 乘积增长。
- 位置列表对统计类任务没用，不要读它（读它会把内存和时间都拉差）。

五、stopword.json 怎么来的

- 数据驱动规则：df >= 50% 文档（门槛 381 篇） 或 词流占比 >= 0.1%（门槛 939 次）
  -> 154 个候选词干，覆盖 58.6% 词次。
  df 抓"几乎每篇都出现"（课件对 stop word 的定义口径）；份额抓"体量大"。
  两条互补：exit（df 59%、频 977）只有 df 抓得到；doth（频 996、df 47%）只有份额抓得到。
- 人工层：在候选之上把"有查询价值的实义词"拉回索引（人名/身份词等）。
  名单记录在 stop_word_build.py 里（规则算完后统一剔除，重跑不会丢）；最终 135 词
  （覆盖 55.5%，2026-10-03），以脚本输出为准。
- 存放形态：stem（第三节的规则同样适用），不是原词。
- 过滤位置：build-index 端（inner-docs.json 保持全量，不动）。
- 组内待定：边界实义词（love、man、time、death、say、see 等）收不收——
  直接影响查询演示（被收进停用词表的词查不到）。

六、重新生成

- 前提：Python 3、pip install pystemmer；data/raw-data/ 就位（761 篇，不入 git）。
- raw-data 从哪来：仓库根 shakespeare/ 是语料镜像原样，注意 Comedy/History/Tragedy
  三个子目录是根目录同名剧的重复副本，整包处理会重复计数；raw-data 是整理后的干净版
  （去重、去掉 index/full 等页面），内容 = mapping.json 里的 761 个 docname。
  整理清单/打包找我要。
- 脚本用相对路径 ../../../data/...，必须在脚本所在目录运行：

      cd src/build/preprocess
      python mapping_build.py
      python text_process.py
      cd ../stopword-processer
      python stop_word_build.py

- 重跑后 mapping.json / stopword.json 会更新，请一起 commit。
  （inner-docs.json 不入 git：约 25 MB，太大，可随时重建。）

七、对账数字

- 761 篇；总 token 938,770；不同词干 18,536；(文档, 词干) 对 319,686。
- 抽查 4 篇 length：macbeth.1.1 = 115、cleopatra.3.10 = 383、hamlet.3.1 = 1,641、
  Poetry/sonnets = 1,490。
- 过停用词之前，倒排索引 (词干, 文档) 条目总数上界 = 319,686；过掉停用词后变少属正常。

八、纪律

- 不要手改 data/processed-data/ 下的 json：要改就改脚本重跑（数据可再生）。
- 本仓库已加 .gitignore：__pycache__、.idea、data/raw-data、inner-docs.json 不入库，
  之后新生成的 .pyc 不会再被提交。
- 发现某篇文档词数可疑：先按第六节重跑，再带"文档号 + 词"来找我。
