# 输入处理与运行方式

## 运行环境

Python 3.10+；编译需要 XeLaTeX、Biber、ctex、fontspec、unicode-math、tex-gyre-math、biblatex-gb7714-2015 和模板导言区所列宏包。PDF 提取/渲染需要 `pypdfium2`、`Pillow`，可用 `python -m pip install -r scripts/requirements.txt` 安装到独立环境。DOCX 需要 Pandoc。扫描件自动 OCR 可用 Tesseract，需安装 `chi_sim`、`eng` 语言数据。优先使用环境提供的 Python 和已有 TeX 安装；不把本机绝对路径写入交付模板。

Pandoc 查找顺序为显式 `--pandoc`、PATH、skill 下 tools、源码项目下 .tools、`CODEX_HOME/tools/ruc-thesis`（默认 `~/.codex/tools/ruc-thesis`）。可将官方解压版和许可证保存在最后一个位置，无需修改系统 PATH。skill 压缩包不包含第三方可执行文件。

编译器使用 argv 参数调用，工作目录固定为新工程，默认关闭 shell escape。`latexmk` 可用时可运行 `latexmk -xelatex -outdir=build main.tex`；Windows 上 latexmk 可能因缺少 Perl 不可用，因此脚本提供 XeLaTeX → Biber → 重复 XeLaTeX 的等价有界序列，最多四次后处理，比较辅助文件确保收敛。

可选依赖应在用户环境或独立环境中安装，不修改只读的 Codex 捆绑运行时。Pandoc 官方安装入口：https://pandoc.org/installing.html 。操作依据：https://pandoc.org/MANUAL.html 。Pandoc 是结构转换工具，复杂表格等不保证无损。

## 元数据

`--metadata` 接受 UTF-8 JSON，字段值作为普通文字转义，不能传入 LaTeX 命令。少填字段自动标为待填写；score/subtitle 默认允许为空。用户明确要求留空的其他字段传入空字符串，并在交付记录列明，不再反复索取。示例：

```json
{
  "title": "论文题名", "subtitle": "副题名", "author": "作者姓名",
  "college": "学院名称", "major": "专业名称", "grade": "2022级",
  "student-id": "实际学号", "supervisor": "指导教师姓名",
  "score": "", "date": "实际完成日期", "code": "实际论文编码"
}
```

直接编辑 `metadata.tex` 时可使用 LaTeX，但需正确转义 `% & _ #` 等特殊字符。`date` 不自动填当前日期；不能把格式处理日期冒充论文完成日期。

## TeX

`import-tex <main.tex> <new-output> [--source-root <project-root>]` 保存源工程，抽取 document 环境正文，导言区另存 `original-preamble.tex.txt`。输出应位于输入工程目录之外，避免递归复制。只需可编译模板时直接 `init`。

导入是保守的初始迁移，不是任意 TeX 解析器：查找 document 边界时跳过注释、标准 `\verb` 和常见逐字环境；复杂宏生成的边界、自定义逐字环境或 catcode 修改仍需要人工/模型读取。正文按原文切片，保留注释及换行，避免改变 `%` 抑制空格的语义；原始文件完整保留。迁移自定义宏和必要宏包到 `preamble-extra.tex`，不要照搬旧 documentclass、geometry、fontspec、fancyhdr、titlesec、bibliography 样式。保留内容中的数学环境、标签与引用键。处理嵌套 input 的相对路径时以实际编译结果验证；绝对路径和目录外资源需主动收集到工程并改为相对路径。

将原封面字段、摘要、关键词和正文正确分离，删除旧封面与旧目录生成命令。将 bibliography/thebibliography 整理为当前工程一致的引用方法，不能同时保留两套参考文献输出。原始 class-specific 宏可能需要适配；每次修改后编译。

## Word

`import-docx <input.docx> <new-output> [--pandoc <exe>]` 使用 Pandoc DOCX → JSON AST → LaTeX，媒体存入 `media/`。`source/document.json` 保留结构，`conversion.json` 记录段落/表格/公式/图片/脚注与特殊对象计数。文件中有修订时默认停止；根据用户意图选择 `--track-changes accept` 或 `reject`，不得静默选取版本。

修订检测覆盖 Word XML 各部件中的插入、删除、移动与属性变更，并在 `details.revision_parts` 记录部件和类型。选择版本后仍需对照源文档检查脚注、尾注、移动文字和格式变更，不能假设 Pandoc 对每种修订均能完整处理。

按语义切分前后置部分，而不是对任意“摘要”字符串全局替换。正确的 Word Heading 样式可转换为章节；手工加粗标题需要识别。核对 Word 公式 OMML、跨页/合并表格、文本框、浮动图片、脚注及域。转换器警告或计数异常需回看原文；保留可识别的内容，不用空白替换。Zotero/EndNote 等域不等于有效 `.bib` 数据；从已有引用资料匹配，不能猜测作者、年份、DOI。

普通 `.doc` 不受 Pandoc DOCX 读取器支持。先用已可用的 Word/LibreOffice 转换为 `.docx`，再进入相同流程。不要在此 skill 中声称已经实现二进制 DOC 的独立解析。

## PDF

`import-pdf <input.pdf> <new-output>` 提取逐页文本并生成页图，保留 `source/pages.json`、每页 `.txt`/`.png`。同时使用 pdfplumber 生成 `source/glyphs/inventory.json` 和逐页字符坐标、字体、基线矩阵、线段及链接资料。已有工程可单独运行 `scripts/pdf_inventory.py <input.pdf> <output-evidence-dir>` 补充这些资料。正文是清楚标记的提取初稿，不是完成版。字符稀少只是一条线索，不等于该页必然为扫描件；封面/空白页也可能触发。

数学字体、细小上下标、分式横线、不可映射字形和等宽代码即使在文字丰富的页面也需要复核。字体名称检测只产生线索，不保证发现所有数学对象。恢复分式时结合横线及上下方字符位置；上下标用基线矩阵区分，不能只按字符出现顺序或从左到右排列。跨行表达式、cases、求和上下限、根号、转置和罗马运算符须回看页图。不要把某篇论文的人工公式修正字典当作通用转换器。

标题识别结合字体、字号、位置和上下文；行首“5.4 横轴……”可能只是上一行正文的延续。保留原公式、定理和图表编号，建立编号清单，检查漏号、重号与全文引用。正文物理换行重连时修复英文断词，并避免吞掉原本的连字符。代码从等宽字形横坐标恢复缩进，跨页续接后可做静态语法检查；文中运行命令是论文内容，不自动执行实验程序。

图形裁切只覆盖单幅图的绘图区、轴刻度、图例与标签，图题另行排版；优先保留矢量。表格逐行核对数值、正负号、指数及有效位数。保留 PDF 的外部链接目标。若所有原文文献均需保留，可按原顺序显式列出 `\nocite{key1,key2,...}` 并保留正文真实引用；不要新增原文没有的作者姓名、日期或 DOI。

需要自动 OCR 时加 `--ocr --tesseract <exe> --ocr-language chi_sim+eng`；默认只 OCR 稀疏页，`--ocr-all` 可强制全页。没有 OCR 时直接查看页图转录。不要安装大型 OCR 环境以掩盖一个可以视觉读取的少量页面；大型扫描论文则应配备可靠 OCR 后逐页校验。

执行语义重建：确定阅读顺序，移除重复页眉页脚，将实际章节转换为标题，将原摘要放入摘要文件，公式重建为 LaTeX，表格重建为表格，图片按单个图对象裁切或提取。保留每个内容块的原页码注释。双栏、文字层乱码、低清扫描、复杂公式和图中标注均须重点检查。脚本不会自动声称识别出正确章节、公式或参考文献。

## 状态与交付

数学密集 PDF 的具体故障与修复经验见 [实测问题](pdf-reconstruction-lessons.md)，尤其注意编号清单、跨页代码及 online 文献的 DOI 输出。

`conversion.json` 默认 `needs-review`。模型完成逐项核对后，将实际处理说明写入该文件的 `resolutions`，设置 `content_reviewed`；只有内容核对完成才改为 `reviewed`。`build-report.json` 每次构建重新生成，`visual_reviewed=false`，避免旧确认被新 PDF 继承。视觉验收另写 `review/acceptance.json`，含最终 PDF SHA256、检查页数、检查内容和未解决事项。不能用简单修改状态代替核对。

`render` 仅接受新目录或空目录，避免较短的新 PDF 与上次多出的旧页图混在一起；每轮使用独立渲染目录。`render-report.json` 记录输入 PDF 哈希、页数、DPI 和渲染器，不标记视觉验收。DPI 必须大于零。

交付工程可通过脚本 `build` 重编译，也可在项目目录运行：

```text
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
biber --input-directory=build --output-directory=build main
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
```

手工命令前先创建 build 目录。需要提交源文件时应包含 `ructhesis.cls`、main/metadata/preamble、content、assets、实际媒体与 bib 数据、PROVENANCE.md，不依赖 skill 安装路径。
