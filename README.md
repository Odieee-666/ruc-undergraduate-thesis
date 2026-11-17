# 中国人民大学本科毕业论文排版 Skill

**Skill 名称：`ruc-undergraduate-thesis`**  
**适用环境：Codex**  
**主要输出：可编辑的 LaTeX 工程与编译后的 PDF**

这是一个面向中国人民大学本科毕业论文的文档整理与排版 skill。它指导 Codex 将已有的 TeX、Word 或 PDF 稿件迁移到统一的论文模板中，完成内容整理、LaTeX 编译、内容比对和逐页版面检查。

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

下载仓库 ZIP 并解压，或运行：

```sh
git clone https://github.com/Odieee-666/ruc-undergraduate-thesis.git
```

将仓库内的 `ruc-undergraduate-thesis` 文件夹放到 Codex 的 skills 目录；默认位置为 `~/.codex/skills/`（Windows 为用户目录下的 `.codex\skills\`）。如果设置了 `CODEX_HOME`，使用该目录下的 `skills/`。目标结构应为 `skills/ruc-undergraduate-thesis/SKILL.md`，不要多套一层仓库目录。若同名 skill 已存在，请先备份并检查差异。

安装后，在支持加载本地 skills 的 Codex 会话中使用 `$ruc-undergraduate-thesis` 调用。LaTeX、Pandoc、字体及 Python 依赖需按下文准备；仓库不包含第三方运行时或真实论文原稿。

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

## 开发与测试

安装 Python 测试依赖，并准备可调用的 Pandoc：

```sh
python -m pip install -r tests/requirements.txt
python tests/test_pipeline.py
```

测试生成的数据保存在本地 `output/`，不提交到仓库。`tests/verify_builds.py` 接受一次流程测试输出的目录，可进一步运行真实 LaTeX 构建；需要 XeLaTeX、Biber、模板宏包及字体。

## 来源与许可

衍生模板保留 Qiu Renxiang 原模板的来源与 LPPL 声明，详见 [PROVENANCE.md](ruc-undergraduate-thesis/assets/template/PROVENANCE.md)。校标权利归原权利人；本项目不代表中国人民大学官方发布。当前仓库未为新增脚本和说明另行指定统一开源许可证；公开托管不扩大原有许可范围。
