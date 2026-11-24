# 中国人民大学本科毕业论文排版 Skill

<p align="center"><img src="https://github.com/user-attachments/assets/45c3022e-f3c2-4213-a26e-096bc369a759" alt="本科毕业论文封面示例，含题名、副标题及作者、学院、导师等字段" width="210"></p>

各位RUCer小伙伴们大家好，你写毕业论文时候：老师是不是让你在overleaf里面编辑、让你用Latex，刷了四年手机的你很显然不知道这是啥，我写了这个skill，你只需要把我在下面如何使用里写的那句话，直接**复制**在对话框中，一键直接把你用AI写的毕业论文（bushi），继续用AI转化为高大上的符合模版、精致排版的毕业论文（上图）。

**这个 Skill 已经在 **Codex、DeepSeek Harness、Qoder 和 WorkBuddy** 四个 Agent 中实测过。**（别的AI/agent应该都行）

如果你已经写好了论文，手里是一份 Word 稿、一套 TeX 源码，或者只剩一份 PDF，都可以从这里开始。这个 Skill 帮你把原稿整理成**可以继续修改的 LaTeX 工程**，编译出 PDF，并逐页对照原稿检查公式、图表和参考文献。

[下载 v1.2.0 安装包](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/download/v1.2.0/ruc-undergraduate-thesis-v1.2.0.zip) · [版本说明](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/tag/v1.2.0) · [Agent 实测](#agent-实测) · [安装到 Codex](#安装到-codex) · [运行依赖](#运行依赖)

# 如何使用

# **用法：新开一个对话（这很重要!），直接把你的论文和下面这句话 ，复制粘贴（CTRL+C/V）在对话里发给你的AI，（只用豆包的同学记得开工作模式），然后就完事儿了...** 
（把下面的文件名换成自己的，附上原稿。如果学院发了当年的格式文件 {一般没有}，也一起交给它。）

### > 请读取 https://github.com/Odieee-666/ruc-undergraduate-thesis.git 里的论文排版 Skill，把我的《毕业论文.docx》整理成人大本科毕业论文 LaTeX 工程，放到新目录里，保留原稿。编译后请对照原稿看一遍，尤其是公式编号、跨页表格和参考文献。有看不清的地方，请告诉我是原稿的哪一页。

在 agent 里装好后，直接用 `$ruc-undergraduate-thesis` 调用即可。比如已有 TeX 工程时，可以说：“保留我的公式、引用键和图片，换成人大本科论文的封面和版式。”题名、作者、学院、专业、年级、学号、导师等资料按你提供的内容填写，明确要求留空的字段会保留空白。

## Agent 实测

除了 Codex，**DeepSeek Harness、Qoder 和 WorkBuddy** 也都实际跑过这个项目。三次测试都通过了仓库自带的 **34 项回归测试**，还用样稿检查了编译后的论文。

| Agent | 实际跑出来的结果 |
|---|---|
| **DeepSeek Harness** | 用 UTF-8 和 GB18030 混排的 TeX 稿验证了逐文件解码。另测的 Word 样稿里有 2 个公式、1 张表和 1 幅图，导入后都保留下来，并成功编译。严格字体端到端测试的 18 个步骤全部通过。 |
| **Qoder** | 在 Windows 11、MiKTeX 25.12 和 Python 3.14 下跑通了 TeX、Word、PDF 三种输入的导入、编译和逐页渲染。随后打开 10 页示例，核对了封面、中英文摘要页码、公式编号、三线表和参考文献。 |
| **WorkBuddy** | 在 Windows、MiKTeX 和 Python 3.13 下，用 `build --strict` 编译出 10 页示例，构建报告为零条诊断。另用 GBK 正文和嵌套章节做迁移，核对了新 PDF 中的中文、图片和 Biber 文献条目。 |

结果来自三次 Agent 实测反馈。WorkBuddy 当时缺少 Pandoc，因此整套端到端脚本未跑完。如果你的原稿是 Word，使用仓库的 `import-docx` 入口时请准备好 Pandoc。v1.2.0 另有 Windows 和 Ubuntu 上的四组自动验证，可查看每一步的日志。[GitHub Actions 运行记录](https://github.com/Odieee-666/ruc-undergraduate-thesis/actions/runs/45333654549)

## 支持哪些输入

| 手里的原稿 | 怎样迁移 | 值得逐项核对的地方 |
|---|---|---|
| **TeX 工程** | 保留源文件，迁移正文、嵌套章节、图片和本地文献库。v1.2.0 可逐文件读取 UTF-8 与 GBK/GB18030 混合编码稿件。 | 自定义宏、旧版式、动态路径，以及使用编码回退的中文章节。 |
| **Word 文档** | 用 Pandoc 把 `.docx` 中的标题、段落、公式、表格和脚注转入 LaTeX。旧版 `.doc` 可先用 Word 或 LibreOffice 另存为 `.docx`。 | 合并单元格、浮动图片、域、修订，以及你要保留的修订版本。 |
| **可选中文字的 PDF** | 结合文字、字形坐标、线条和页图重建可编辑内容，图形尽量保留矢量格式。 | 分式与上下标、跨行公式、表格数据、代码缩进和多栏阅读顺序。 |
| **扫描 PDF** | 逐页渲染，结合 OCR 或看图转录。辨认有困难的地方保留原页位置，方便回查。 | 低清区域、数学符号、形近字和缺失字符。 |

PDF 重排后页码可能变化。比如项目早期迁移过一篇 51 页的数学论文，重排后为 45 页，其中有 101 个编号公式、9 张表、6 幅矢量图和 16 条参考文献。这个案例做了内容比对、逐页查看，也验证了把工程解压到新目录后能独立编译。[数学论文重建实录](ruc-undergraduate-thesis/references/pdf-reconstruction-lessons.md)

## 模板提供的功能

封面可填写题名、副标题、作者、学院、专业、年级、学号、导师、成绩、日期和论文编码。正文从中英文摘要和关键词开始，支持罗马数字前置页码、自动目录、可选图表目录和四级标题。

公式、图形、三线表、跨页长表和逐页编号的脚注都有相应样式。参考文献通过 BibLaTeX 与 Biber 处理，可选数字制或著者年制。附录与致谢按需启用。

> **动手前，先看学院要求。** 默认配置 `ruc-2021-local` 依据项目所用的 2022 年模板整理。如果学院或导师提供了当年的格式文件，请以适用要求为准。[格式依据与实施决策](ruc-undergraduate-thesis/references/format-basis.md)

## 安装到 Codex

1. 下载并解压 [v1.2.0 安装包](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/download/v1.2.0/ruc-undergraduate-thesis-v1.2.0.zip)。需要校验下载内容时，可对照 [SHA256SUMS.txt](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/download/v1.2.0/SHA256SUMS.txt)。
2. 找到**打开后直接能看到 `SKILL.md`** 的 `ruc-undergraduate-thesis` 文件夹，将整个文件夹放进下表对应的位置。如果已有同名版本，先备份并核对差异。
3. 在支持本地 skills 的 Codex 会话里输入 `$ruc-undergraduate-thesis`，再告诉它原稿在哪儿、希望输出到哪里。

| 环境 | 放置 Skill 文件夹的位置 |
|---|---|
| Windows | `%USERPROFILE%\.codex\skills\` |
| macOS / Linux | `~/.codex/skills/` |
| 自定义了 `CODEX_HOME` | 该目录下的 `skills/` |

<details>
<summary>从源码安装，或检查解压后的目录层级</summary>

要查看测试代码或参与开发，可以克隆完整仓库。

```sh
git clone https://github.com/Odieee-666/ruc-undergraduate-thesis.git
```

把仓库**内部**的同名文件夹复制到 skills 目录。固定使用 v1.2.0 时可选上面的版本安装包。两种安装方式都需要另行准备运行依赖。

```text
skills/
└── ruc-undergraduate-thesis/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

</details>

## 其他 AI 如何复用

习惯用 Harness、Qoder 或 WorkBuddy 的话，可以把仓库放在它能访问的工作目录，让它先读 [SKILL.md](ruc-undergraduate-thesis/SKILL.md)，再按原稿类型读取对应说明。模板、脚本和参考文档放在一起，保留解压后的目录结构即可。

- **能加载本地 Skill** 的工具可以用自己的导入入口载入完整文件夹。`$ruc-undergraduate-thesis` 是 Codex 的调用写法，其他工具使用各自的调用方式。
- **能操作文件和终端** 的 Agent 可以直接按说明运行 Python 脚本。若它运行在云端，原稿也要放到那个环境能读取的位置。
- **逐页核对**需要打开渲染后的图片。如果工具只能运行命令，可以先让它交付 PDF、页图和日志，再由你或能看图的 Agent 检查。纯聊天工具也能帮你读规则、改源码，编译则需要本地或云端的执行环境。

## 运行依赖

| 用途 | 需要准备什么 |
|---|---|
| 脚本与编译 | Python 3.10+，MiKTeX 或 TeX Live，以及 XeLaTeX、Biber 和模板所需宏包 |
| Word 导入 | Pandoc |
| PDF 提取与渲染 | pypdfium2、Pillow、pdfplumber。安装了 Poppler 时优先用它渲染 |
| 扫描稿自动 OCR | 可选的 Tesseract 及对应语言数据 |
| 正式排版 | 宋体、黑体、楷体、仿宋、Times New Roman、Arial、Courier New，数学字体使用 TeX Gyre Termes Math |

第一次使用时，运行 `doctor --input-type tex` 检查 TeX 环境。处理 Word 或 PDF 时把 `tex` 换成 `docx` 或 `pdf`。它会实际探测宏包、字体和最小编译，并给出缺失项的处理建议。安装包不附带第三方运行时或商业字体。只想先看效果，可以显式选用 `--portable`，以 Fandol 和 TeX Gyre 字体预览。

### 脚本入口

以下示例假设终端位于含有 `SKILL.md` 的目录。建工程时，按手里的原稿选一个入口，并指定一个新的输出目录。带空格的路径请加引号。

| 你的起点 | 命令 |
|---|---|
| 检查环境 | `python scripts/thesis.py doctor` |
| 先编译一份示例 | `python scripts/thesis.py init my-demo --demo`，然后运行 `python scripts/thesis.py build my-demo` |
| 用自己的封面信息建空白工程 | `python scripts/thesis.py init my-thesis --metadata metadata.json` |
| 已有 TeX / Word / PDF | 分别运行 `python scripts/thesis.py import-tex main.tex my-thesis`、`python scripts/thesis.py import-docx paper.docx my-thesis` 或 `python scripts/thesis.py import-pdf paper.pdf my-thesis` |

整理好正文、摘要和文献后，再编译并逐页渲染。每轮渲染选择新的或空的目录，方便知道自己看到的是哪一版。

```sh
python scripts/thesis.py build my-thesis --strict
python scripts/thesis.py render my-thesis/build/main.pdf my-thesis/review/pages-v1
```

v1.2.0 在 MiKTeX 的环境检查和正式构建中都关闭了按需装包。遇到缺包或超时，可以在 `build/build-report.json` 和 `build/build-transcript.txt` 中查看具体命令与原因。[输入处理与命令参数](ruc-undergraduate-thesis/references/input-workflows.md)

## 交付物与检查记录

**要看成稿，打开 `build/main.pdf`。要继续改论文，从 `main.tex` 开始。** 工程里也保留着原稿和检查记录，交接给导师或同学时可以一起带走。

```text
论文工程/
├── main.tex                 # 编译入口
├── ructhesis.cls            # 模板类
├── metadata.tex             # 封面资料
├── preamble-extra.tex       # 稿件需要的额外宏与设置
├── content/                 # 摘要、正文、附录、致谢
├── references.bib           # 参考文献数据
├── assets/                  # 模板资源
├── source/                  # 导入时保存的原稿与提取资料
├── conversion.json          # 转换过程和待核对项
├── build/                   # 最终 PDF、构建报告和日志
└── review/                  # 逐页渲染图与实际验收记录
```

导入初稿的状态是 `needs-review`。交稿前可以按这个顺序过一遍。

1. **看构建报告。** 检查缺字、未定义引用、丢失的资源和版面越界。编译会调用 XeLaTeX，按需调用 Biber，直到辅助文件收敛。
2. **对照原稿。** 核对章节、公式编号、表格数据、参考文献和附录。扫描不清或无法确认的内容，在转换记录中留下对应位置。
3. **打开最终 PDF。** 逐页查看封面换行、摘要页码、跨页表头、图注和脚注。确认后在 `review/acceptance.json` 中记下结果和最终 PDF 的哈希。[完整验收规则](ruc-undergraduate-thesis/references/acceptance.md)

主要交付格式是 LaTeX 和 PDF。论文结论与实验数据仍由作者核实，提交时的格式认定以学院审核为准。

## 导入失败后继续

如果目标目录叫 `my-thesis`，进度会保存在旁边的 `.my-thesis.import/state.json`，同目录的 `environment.json` 列出依赖情况。补好依赖后，在原命令后加 `--resume`，即可复用已完成的页面、媒体或 TeX 工作副本。

```sh
python scripts/thesis.py import-pdf original.pdf my-thesis --resume
```

续跑时保留原来的字体模式、DPI、OCR 语言或修订选择。如果改过输入、脚本、模板、转换参数或已完成的工作文件，使用 `--retry` 保存旧工作区并重新导入。成功后才会生成最终目录。[恢复示例与参数](ruc-undergraduate-thesis/references/input-workflows.md#导入失败与恢复)

## 进一步阅读

- [格式依据](ruc-undergraduate-thesis/references/format-basis.md) · [模板来源与 LPPL 声明](ruc-undergraduate-thesis/assets/template/PROVENANCE.md)
- [数学密集 PDF 的重建经验](ruc-undergraduate-thesis/references/pdf-reconstruction-lessons.md) · [按字形恢复代码缩进、清点公式编号和定位原页](ruc-undergraduate-thesis/references/recovery-tools.md)
- [实测环境与历史回归记录](tests/verified-environments.md) · [CI 工作流](.github/workflows/ci.yml) · [TeX Live 宏包清单](tests/texlive-packages.txt)

<details>
<summary>开发者复现测试（在仓库根目录运行）</summary>

准备 [Python](https://www.python.org/downloads/)、[Pandoc](https://pandoc.org/installing.html) 和 [TeX Live](https://tug.org/texlive/acquire-netinstall.html)，并把工具加入 PATH。已有 MiKTeX 的 Windows 机器也可运行。项目 CI 使用 TeX Live 2025 和 Pandoc 3.8.3。

```sh
tlmgr install scheme-basic collection-xetex collection-langchinese collection-latexrecommended collection-latexextra collection-fontsrecommended collection-bibtexextra biber tex-gyre-math
python -m venv .venv
```

激活虚拟环境，或将下面的 `python` 换成 Windows 下的 `.venv/Scripts/python.exe`、Linux 下的 `.venv/bin/python`。

```sh
python -m pip install -r tests/requirements.txt
python ruc-undergraduate-thesis/scripts/thesis.py doctor --input-type pdf --portable
python -m unittest discover -s tests -p "test_*.py" -v
python tests/smoke_clean.py
```

测试使用合成样稿，覆盖三种格式的导入、编译与渲染，以及失败续跑、参考文献和内容恢复工具。环境版本与日志保存在 `output/`。机器装有正式字体时，可额外运行 `python tests/smoke_clean.py --strict-fonts`。OCR 语言缺失检测有自动测试，真实扫描件的识别质量需结合原页检查。

</details>

## 来源与许可

衍生模板保留了 Qiu Renxiang 原模板的来源和 LPPL 声明。校标权利归原权利人，本项目为非官方项目。仓库新增脚本与说明的统一开源许可证尚未指定。[来源与许可说明](ruc-undergraduate-thesis/assets/template/PROVENANCE.md)
