# 数据与获取方式

取证日期：2026-10-26。你也可以使用其他公开数据，或完全使用合成数据；下表分为主数据与可选数据。

## 主数据

PPI 参考实现包 `ppi-python` 附带的示例数据（9 个 `.npz` 集合）。

- 获取：`pip install ppi-python==0.2.3`（PyPI 发布于 2024-12-22；GitHub 标签 `v0.2.3`，提交 `6b8475b`）。首次调用 `ppi_py.datasets.load_dataset('./data/', '<集合名>')` 时由包内代码通过 `gdown` 从 Google Drive 下载到本地 `./data/<集合名>.npz`（`gdown` 已列入该包的依赖）。无需账号或协议。已在宿主机上实测：9 个文件均可匿名下载，合计约 48 MB；容器内未测。
- 仓库：https://github.com/aangelopoulos/ppi_py ；PyPI：https://pypi.org/project/ppi-python/ 。
- 许可：代码仓库为 MIT（`v0.2.3` 的 LICENSE 已核实）。仓库 README、LICENSE 与 PyPI 页面均未给出 `.npz` 数据文件的独立许可声明（PyPI 页面 license 字段为空）；各集合的原始来源见仓库 `examples/*.ipynb` 开头的引文。
- 版本：固定为 `v0.2.3`。

| 集合名 | 大小 | 数组（形状） | 示例 notebook 中的描述 |
| --- | --- | --- | --- |
| `galaxies` | 约 0.3 MB | `Y`、`Yhat`（各 16743） | 星系是否有旋臂：人工标注与计算机视觉预测 |
| `forest` | 约 0.03 MB | `Y`、`Yhat`（各 1596） | 亚马逊地块是否毁林：实地标注与卫星影像预测 |
| `alphafold` | 约 0.4 MB | `Y`、`Yhat`、`phosphorylated`、`ubiquitinated`、`acetylated`（各 10802） | 蛋白无序区域标注与基于 AlphaFold 结构的预测，及三种翻译后修饰的指示变量 |
| `gene_expression` | 约 1 MB | `Y`、`Yhat`（各 61150） | 启动子序列诱导的基因表达水平：实验测量与 Transformer 预测 |
| `census_income` | 约 11 MB | `Y`、`Yhat`（各 380091），`X`（380091×2） | 美国加州 2019 年普查收入：报告值与模型预测，特征为年龄和性别 |
| `census_healthcare` | 约 9 MB | `Y`、`Yhat`（各 318215），`X`（318215×2） | 美国加州 2019 年普查：是否有私人医保（报告值与预测），特征含收入 |
| `census_education` | 约 14 MB | `Y`、`Yhat`（各 318215），`X`（318215×4） | 美国加州 2019 年普查：收入与教育程度相关量及其预测 |
| `plankton` | 约 12 MB | `Y`、`Yhat`（各 421238），`Y_unlabeled`、`Yhat_unlabeled`（各 329832） | 浮游生物成像（2013 年标注、2014 年未标注），含两年不同分布 |
| `ballots` | 约 0.6 MB | `Y`、`Yhat`（各 1027），`Yhat_unlabeled`（78150） | 2022 年旧金山一次特别选举的选票：人工判读与扫描读取 |

除 `plankton`、`ballots` 外，每个集合的 `Y`、`Yhat` 对应同一批记录（标签与预测）；`X` 仅在 `census_*` 集合中出现。

## 可选数据

| 数据 | 获取 | 许可/账号 | 规模与格式 |
| --- | --- | --- | --- |
| Wine Quality（UCI） | https://archive.ics.uci.edu/dataset/186/wine+quality ；压缩包 https://archive.ics.uci.edu/static/public/186/wine+quality.zip | CC BY 4.0（Creative Commons Attribution 4.0 International，UCI 数据集页面注明）；无需账号 | 含 `winequality-red.csv`（1599 条）与 `winequality-white.csv`（4898 条），共 6497 条；分号分隔；11 项理化指标 + `quality` 评分，共 12 列。UCI 页面标注 2009-10-07 捐赠。不含预测值，只含特征与评分 |
| California Housing | `sklearn.datasets.fetch_california_housing`（https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html ）；数据由 figshare 下载（https://ndownloader.figshare.com/files/5976036） | 无明确许可声明（sklearn 文档仅注明数据取自 StatLib 仓库）；无需账号 | 20640 条、8 个特征，目标为区块房价中位数。不含预测值 |
| 美国人口普查类数据（ACS PUMS，通过 `folktables`） | `pip install folktables==0.0.12`（PyPI 2023-02-08）；https://github.com/socialfoundations/folktables 。数据由 census.gov 下载，例如 2019 年 1-Year 加州文件 https://www2.census.gov/programs-surveys/acs/data/pums/2019/1-Year/csv_pca.zip（约 68 MB） | `folktables` 仓库为 MIT；ACS PUMS 为美国人口普查局公开数据；无需账号 | 单州数据量为 10^5 量级。不含预测值 |
| 合成数据 | 自行生成 | 无 | 生成机制与真值由你确定 |

`ppi-python` 示例数据已附带预测值 `Yhat`；Wine Quality、California Housing、folktables 不附带预测值。
