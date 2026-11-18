# 中国人民大学本科毕业论文排版 Skill

**Skill 名称：`ruc-undergraduate-thesis`**

**适用环境：Codex**/Qoder/harness等agent

**使用方法：直接复制 https://github.com/Odieee-666/ruc-undergraduate-thesis.git 给agent即可

![Uploading 图片.png…]()


**主要输出：可编辑的 LaTeX 工程与编译后的 PDF**

**v1.1.0：** [下载安装包](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/download/v1.1.0/ruc-undergraduate-thesis-v1.1.0.zip) · [版本说明](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/tag/v1.1.0) · [安装步骤](#安装到-codex)

**其他 AI 工具：** [复用方式与环境要求](#其他-ai-如何复用)

这是一个面向中国人民大学本科毕业论文的文档整理与排版 skill。它指导 Codex（#兼容其他ai） 将已有的 TeX、Word 或 PDF 稿件迁移到统一的论文模板中，完成内容整理、LaTeX 编译、内容比对和逐页版面检查。

它由操作说明、格式依据、LaTeX 模板和辅助脚本组成。脚本负责可重复的提取、工程创建、构建与检查；模型负责理解文档结构、恢复复杂内容、处理格式冲突和查看页面。两者共同完成稿件迁移。

## 适合解决什么问题

- 已有论文内容，希望整理为人大本科毕业论文的 LaTeX 工程。
- 已有 TeX 工程，需要迁移封面、摘要、标题、页眉页脚和参考文献样式。
- 论文写在 Word 中，希望保留公式、表格、图片和脚注，转入 LaTeX 排版。
- 只有论文 PDF，需要恢复可编辑正文，并按照模板重新分页。
- 工程已经可以编译，但仍需检查缺字、引用、公式、表格和页面布局。

## 支持哪些输入

| 输入 | 处理方式 | 重点检查 |
|---|---|---|
| TeX | 保存源工程，提取正文，迁移必要宏与资源，接入模板 | 自定义命令、文件路径、数学环境、引用和旧版式设置 |
| Word `.docx` | 通过 Pandoc 提取结构并生成 LaTeX 初稿 | 标题样式、公式、合并表格、图片、脚注、域及修订 |
| 原生 PDF | 提取文字、字形坐标、字体、线条及链接，结合页图重建内容 | 阅读顺序、上下标、分式、多行公式、表格数据和代码缩进 |
| 扫描 PDF | 渲染页面，结合可用 OCR 或视觉转录恢复内容 | 识别错误、缺失字符、数学符号和低清区域 |

旧版 `.doc` 需要先使用 Word 或 LibreOffice 转为 `.docx`。

PDF 输入采用的是**内容重建与重新排版**：正文、公式和表格尽可能恢复为可编辑源码，图形按独立对象提取或裁切，优先保留矢量内容。原页码与输出页码可以不同，但需要记录内容的对应关系。

## 工作流程

```text
读取格式依据与用户要求
          ↓
保存原稿，清点内容与依赖
          ↓
按输入类型导入，生成待核对初稿
          ↓
整理封面、摘要、正文、图表、参考文献和附录
          ↓
XeLaTeX → Biber → 重复 XeLaTeX，直至辅助文件收敛
          ↓
检查编译日志、比对内容、逐页查看渲染结果
          ↓
修复发现的问题，重新编译与核对
          ↓
交付完整工程、PDF 和检查记录
```

导入命令生成的初稿会标为 `needs-review`。编译成功只代表构建通过；内容核对和视觉验收需要实际完成，另行记录。

## 模板提供的功能

- 参数化封面：题名、副题名、作者、学院、专业、年级、学号、导师、成绩、日期和论文编码。
- 中文与英文摘要、关键词及罗马数字页码。
- 自动目录、可选图表目录，以及四级正文标题。
- 正文页眉页脚、首行缩进、字体字号与行距设置。
- 数学公式、图形、三线表、跨页表格和每页重新编号的脚注。
- 基于 BibLaTeX/Biber 的参考文献，支持数字制与著者年制。
- 按需启用的附录与致谢。

模板默认使用 `ruc-2021-local` 配置，依据项目提供的 2022 年模板中记载的历史要求构建。**它不是已核实的最新全校统一标准。** 使用时应读取适用学院、年份的具体要求，并据此调整。完整依据见 [格式依据与实施决策](ruc-undergraduate-thesis/references/format-basis.md)。

## 安装到 Codex

### 推荐：下载 v1.1.0 安装包

1. 下载 [ruc-undergraduate-thesis-v1.1.0.zip](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/download/v1.1.0/ruc-undergraduate-thesis-v1.1.0.zip)。这是整理好的 skill 安装包；Release 页面中的 **Source code** 是完整仓库源码。
2. 解压安装包，找到其中直接包含 `SKILL.md` 的 `ruc-undergraduate-thesis` 文件夹。
3. 将该文件夹放入 Codex 的 skills 目录：Windows 默认是 `%USERPROFILE%\.codex\skills\`，macOS/Linux 默认是 `~/.codex/skills/`。如果设置了 `CODEX_HOME`，则放入其下的 `skills/`。目录不存在时可先创建；同名 skill 已存在时，先备份并检查差异。
4. 确认目录结构如下，不要多套一层压缩包或仓库目录：

```text
skills/
└── ruc-undergraduate-thesis/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

5. 在支持加载本地 skills 的 Codex 会话中使用 `$ruc-undergraduate-thesis` 调用，示例见下方“如何使用”。

可下载 [SHA256SUMS.txt](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/download/v1.1.0/SHA256SUMS.txt) 校验安装包。版本内容见 [v1.1.0 Release](https://github.com/Odieee-666/ruc-undergraduate-thesis/releases/tag/v1.1.0)。

### 从仓库源码安装

需要查看测试代码或参与开发时，可以下载仓库 ZIP，或运行：

```sh
git clone https://github.com/Odieee-666/ruc-undergraduate-thesis.git
```

将仓库**内部**的 `ruc-undergraduate-thesis` 文件夹按上述步骤放入 skills 目录，而不是复制整个仓库。默认分支可能包含 v1.1.0 之后的改动；需要固定版本时，使用上面的 v1.1.0 安装包。

安装 skill 后，仍需按下文准备 LaTeX、Pandoc、字体及 Python 依赖；安装包和仓库均不包含第三方运行时或真实论文原稿。

## 其他 AI 如何复用

本 skill 的核心是 Markdown 操作说明、Python 脚本和 LaTeX 模板，脚本不调用特定模型的 API。因此，它可以迁移到其他具备相应工具能力的 AI agent；是否能直接安装，取决于目标工具支持的 skill 格式、加载机制和运行环境。

**目前只在 Codex 中完成实测，其他平台尚未验证。** 以下是通用复用方法，不代表已保证所有 AI 工具原样兼容。

| AI 工具的能力 | 复用方式 | 能完成的工作 |
|---|---|---|
| 支持与本包兼容的 `SKILL.md` 加载方式 | 按目标工具的规则安装完整 skill 文件夹 | 加载指令后，结合文件读写、命令执行和页面查看能力完成流程 |
| 不支持 skill，但能读写文件、执行命令和查看图片 | 将完整 skill 文件夹放入工作目录，让 AI 显式读取 `SKILL.md` | 按说明调用脚本、整理内容、编译并逐页检查 |
| 可以执行命令，但不能查看页面图片 | 使用脚本进行导入、构建和日志检查 | 视觉检查交由能查看图片的模型或人工完成，不能自动标记已验收 |
| 只能聊天，不能访问文件或执行命令 | 提供相关说明和必要源码作为参考 | 辅助解释规则、修改源码；无法独立完成本地构建与验收 |

### 支持 skill 的工具

1. 下载上面的 v1.1.0 安装包，解压后保留整个 `ruc-undergraduate-thesis` 文件夹及其内部相对路径。
2. 按目标工具的文档，将文件夹放入其支持的 skills 目录，或通过该工具的导入入口加载。不要直接套用 Codex 的安装路径。
3. 确认工具读取了 `SKILL.md`，并能访问 `references/`、`scripts/` 和 `assets/`。
4. 使用目标工具自己的调用方式。`$ruc-undergraduate-thesis` 是本 README 中的 Codex 调用示例，不保证其他平台支持相同语法；`agents/openai.yaml` 是面向 Codex 的界面元数据，不是运行 Python 脚本的必需配置。

### 不支持 skill 的 agent

将解压后的完整文件夹放入 agent 可访问的工作目录，再提供以下任务说明，并将路径替换为实际位置：

> 请先读取 `<skill目录>/SKILL.md`，以及其中与本次输入类型相关的参考文档。按这些说明，将 `<论文输入路径>` 整理为人大本科毕业论文 LaTeX 工程，输出到 `<新的输出目录>`。先检查依赖，再导入和整理内容，完成编译、内容核对与逐页视觉检查。缺失资料不要编造；无法完成的检查应明确保留为待核对。操作遵守当前环境的权限与我的授权范围。

无需把整份 skill 粘贴到提示词中；让 agent 读取本地文件，更便于同时访问模板、脚本和格式依据。如果目标工具要求单独配置项目规则，可以添加指向 `SKILL.md` 的简短入口，保留现有资源目录结构。

### 运行环境与首次验证

- **文件访问**：AI 执行命令的环境必须能访问原稿、skill 文件夹和输出目录。云端容器通常不能直接访问用户电脑上的 `C:\...` 路径，需要将所需文件放入它实际可访问的位置。
- **命令执行**：准备 Python、XeLaTeX、Biber 和模板所需宏包、字体；Word 导入需要 Pandoc，扫描稿自动 OCR 按需准备 Tesseract。具体依赖见下方“运行依赖”。
- **页面查看**：完整验收需要查看渲染后的页面。仅提取出文字或成功生成 PDF，不能替代视觉核对。
- **权限与资源**：命令执行、文件写入及依赖安装应符合目标环境的授权规则。普通聊天中的附件上传功能不一定意味着能够执行这些脚本。

首次迁移建议先运行环境检查：

```text
python "<skill目录>/scripts/thesis.py" doctor
```

`doctor --input-type tex/docx/pdf` 检查对应输入依赖、宏包、字体和 XeLaTeX/Biber 的最小编译。导入命令也会自动执行同样检查，无需增加独立验收流程。缺失依赖会给出修复建议并停止；只有明确接受预览字体时使用 `--portable`。

无论使用哪种 AI，导入初稿、构建结果和内容/视觉验收必须分别记录。复杂公式、表格、引用及原稿中无法确认的信息，仍需按本 skill 的验收规则逐项核对。

## 如何使用

安装后，可以直接在 Codex 中说明输入文件、目标和需要保留的信息。例如：

> 使用 $ruc-undergraduate-thesis 处理这份论文 PDF，生成完整可编辑的 LaTeX 工程，编译为 PDF，并逐页核对内容和格式。作者、学院等信息以我提供的资料为准，无法确认的内容请标记出来。

迁移已有 TeX 工程时，可以这样描述：

> 使用 $ruc-undergraduate-thesis 将这个 TeX 工程迁移到人大本科毕业论文模板。保留原公式、引用和图表，处理宏包与版式冲突，完成编译和检查。

建议同时提供论文题名、作者、学院、专业、年级、学号、导师，以及学院的格式文件。已明确要求留空的字段保持空白；缺失资料不能由模型自行编造。

### 脚本入口

以下命令中的 `<skill>` 是 skill 目录，`<output>` 是新的输出工程目录；带空格的实际路径应加引号。

```text
python <skill>/scripts/thesis.py doctor
python <skill>/scripts/thesis.py init <output> --metadata metadata.json
python <skill>/scripts/thesis.py import-tex manuscript.tex <output>
python <skill>/scripts/thesis.py import-docx manuscript.docx <output>
python <skill>/scripts/thesis.py import-pdf manuscript.pdf <output>
python <skill>/scripts/thesis.py build <output> --strict
python <skill>/scripts/thesis.py render <output>/build/main.pdf <output>/review/pages-v1
```

`init` 和三个导入命令是不同的工程创建入口，选择其中一个使用，不要依次向同一目录执行。`init --demo` 可创建演示工程；普通 `init` 创建待填稿。导入后还需要整理和核对内容，再进入构建与验收。

每轮渲染使用新的目录或空目录，以免混入旧页面。更多参数见 [输入处理与运行方式](ruc-undergraduate-thesis/references/input-workflows.md)。

## 运行依赖

| 用途 | 主要依赖 |
|---|---|
| 辅助脚本 | Python 3.10 或更高版本 |
| LaTeX 编译 | 已安装的 MiKTeX 或 TeX Live，包含 XeLaTeX、Biber 和模板所需宏包 |
| Word 导入 | Pandoc |
| PDF 提取与渲染 | pypdfium2、Pillow、pdfplumber；有 Poppler 时优先用其渲染 |
| 扫描稿自动 OCR | 可选 Tesseract 及相应语言数据 |
| 正式字体模式 | 宋体、黑体、楷体、仿宋、Times New Roman、Arial、Courier New |

数学字体使用 TeX Gyre Termes Math。`portable` 模式使用 Fandol/TeX Gyre 字体，适合环境预览，会明确报告字体替代。Skill 不分发商业字体，也不会仅因执行环境检查就安装整套 TeX。

## 交付物与检查记录

典型交付包括：

```text
论文工程/
├── main.tex                 # 编译入口
├── ructhesis.cls            # 模板类
├── metadata.tex             # 封面资料
├── preamble-extra.tex       # 稿件所需宏与额外设置
├── references.bib           # 参考文献数据
├── content/                 # 摘要、正文及按需启用的附录、致谢
├── assets/                  # 模板资源
├── source/                  # 导入时保存的原稿与提取资料
├── conversion.json          # 导入与内容核对记录
├── build/
│   ├── main.pdf             # 编译结果
│   └── build-report.json    # 编译状态与诊断
└── review/
    ├── pages-v1/            # 页面图像与渲染记录
    └── acceptance.json      # 完成实际核对后填写的验收记录
```

图片目录、数据文件和额外附件随稿件内容而定。资源齐全的工程可以在具备所需字体与宏包的 LaTeX 环境中独立编译，不依赖 skill 的安装路径。

检查分为三个层面：

1. **构建检查**：确认编译成功、辅助文件收敛，排查缺字、未定义引用、缺失资源和版面越界。
2. **内容检查**：对照原稿检查章节、文字、公式编号、图表数据、参考文献和附录，记录无法确认的内容。
3. **视觉检查**：逐页查看封面、摘要、目录、公式、图表、页眉页脚及参考文献布局，验收记录绑定最终 PDF 哈希。

## 能力边界

- 数学密集 PDF 的恢复需要模型或人工核对；导入脚本本身不是通用的高精度公式转换器。
- TeX 导入不完整解释任意自定义宏、逐字环境或 catcode 修改，复杂工程需要适配。
- Word 的复杂表格、浮动对象、域和修订可能需要额外处理；选择修订版本后仍要检查转换结果。
- 文字比对与编译通过不能替代逐页检查，也不能证明论文研究结论或实验数据正确。
- 当前主要输出为 LaTeX 和 PDF，不承诺反向生成 Word。
- 按模板完成技术检查，不等于学校或学院已经审核通过。

## 项目验证情况

截至 2026-11-18，项目已使用一篇 51 页数学论文进行实际迁移，重排后生成 45 页 PDF，包含 101 个编号公式、9 张表、6 幅矢量图和 16 条参考文献。该工程完成内容核对、逐页查看和解压后的独立编译验证。

随后开展的缺陷检查修复了 TeX 文档边界误判、Word 修订漏检、旧渲染页面残留、无效元数据留下半成品，以及编译失败记录不完整的问题。16 项流程回归测试通过，并对 TeX 正文保留和编译失败日志进行了真实编译验证。这些结果对应已测试的案例，不代表任意论文都能自动无损转换。

## 进一步阅读

- [Skill 主说明](ruc-undergraduate-thesis/SKILL.md)
- [格式依据](ruc-undergraduate-thesis/references/format-basis.md)
- [输入处理与命令参数](ruc-undergraduate-thesis/references/input-workflows.md)
- [验收规则](ruc-undergraduate-thesis/references/acceptance.md)
- [数学密集 PDF 的实测经验](ruc-undergraduate-thesis/references/pdf-reconstruction-lessons.md)
- [模板来源与许可说明](ruc-undergraduate-thesis/assets/template/PROVENANCE.md)

## 干净安装与自动测试

Windows 和 Linux 使用 Python 3.10+、Pandoc 和 TeX Live；Windows 也可使用已有 MiKTeX。仓库 CI 为 `windows-2022`、`ubuntu-24.04` × Python 3.10/3.12，从空环境安装，关闭 TeX Live 缓存。依赖和安装配置参见 [.github/workflows/ci.yml](.github/workflows/ci.yml)。

1. 安装 [Python](https://www.python.org/downloads/)、[Pandoc](https://pandoc.org/installing.html) 和 [TeX Live](https://tug.org/texlive/acquire-netinstall.html)，将可执行文件加入 PATH。CI 固定 TeX Live 2025 和 Pandoc 3.8.3；已完成的 CI 结果和取消的组合见验证记录。已有发行版无需重复安装。
2. 使用 TeX Live 包管理器安装 [tests/texlive-packages.txt](tests/texlive-packages.txt) 中的集合与宏包，或运行以下等价命令：

```text
tlmgr install scheme-basic collection-xetex collection-langchinese collection-latexrecommended collection-latexextra collection-fontsrecommended collection-bibtexextra biber tex-gyre-math
```

3. 在仓库根目录创建隔离 Python 环境：

```text
python -m venv .venv
```

Windows PowerShell 使用 `.venv/Scripts/python.exe`，Linux 使用 `.venv/bin/python` 执行后续命令（也可先激活环境）。以下 `python` 均指该环境的解释器：

```text
python -m pip install -r tests/requirements.txt
python ruc-undergraduate-thesis/scripts/thesis.py doctor --input-type pdf --portable
python -m unittest discover -s tests -p "test_*.py" -v
python tests/smoke_clean.py
```

测试只生成合成输入，覆盖 TeX/DOCX/PDF 导入、失败续跑、源文件与检查点变化、真实 XeLaTeX/Biber 编译、参考文献、PDF 渲染和通用内容工具。测试资料和实际依赖版本保留在 `output/`，CI 无论成功失败都上传日志。`verified-versions.json` 只有流程完成才标为 `passed`；`pip-freeze.log` 和 TeX Live 宏包清单记录解析到的具体版本。已取得的结果见 [tests/verified-environments.md](tests/verified-environments.md)。已完成的 CI 结果和按用户要求取消的组合均在验证记录中注明。

跨平台测试显式使用 Fandol/TeX Gyre 预览字体，不捆绑商业字体。正式排版仍检查 SimSun、SimHei、KaiTi、FangSong、Times New Roman、Arial、Courier New；有这些字体的机器可运行 `python tests/smoke_clean.py --strict-fonts`。Tesseract/OCR 是可选功能，其语言缺失检测有自动测试，真实 OCR 识别质量不属于上述覆盖范围。

## 导入失败后继续

例如导入目标为 `my-thesis`，失败进度保存在同级 `.my-thesis.import/state.json`，依赖报告位于 `environment.json`。最终目录仅在成功后生成。

```text
python ruc-undergraduate-thesis/scripts/thesis.py import-pdf original.pdf my-thesis --resume
python ruc-undergraduate-thesis/scripts/thesis.py import-docx original.docx my-thesis --pandoc <修复后的路径> --resume
```

恢复时保留原转换参数（例如 `--portable`、DPI、OCR 语言和修订选择）。PDF 复用已完成页，DOCX 复用 AST/媒体。输入、模板、脚本或转换参数变更时，用 `--retry` 保存旧工作区后重新处理。已有最终目录不会覆盖。详细行为见 [输入处理](ruc-undergraduate-thesis/references/input-workflows.md#导入失败与恢复)。

## 可复用的内容恢复工具

`scripts/recover_content.py` 提供 `code`（按字形坐标恢复缩进并保留逐行来源）、`equations`（候选编号与重复/缺口清点）、`locate`（关键词对应源页与坐标）。命令、区域参数和限制见 [内容恢复工具](ruc-undergraduate-thesis/references/recovery-tools.md)。这些工具接入原来的内容核对过程；不会执行提取的代码，也不会把某篇论文的公式修正泛化。

## 来源与许可

衍生模板保留 Qiu Renxiang 原模板的来源与 LPPL 声明，详见 [PROVENANCE.md](ruc-undergraduate-thesis/assets/template/PROVENANCE.md)。校标权利归原权利人；本项目不代表中国人民大学官方发布。当前仓库未为新增脚本和说明另行指定统一开源许可证；公开托管不扩大原有许可范围。
