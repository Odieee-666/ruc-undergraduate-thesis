# 内容恢复工具

使用已导入的 `source/glyphs/`，或先运行 `scripts/pdf_inventory.py input.pdf glyphs`。这些工具不调用大模型、不执行论文代码，也不携带任何特定论文的公式修正表。输出是现有内容核对流程中的辅助资料，不新增验收环节。

## 代码缩进与源行映射

先查看原页图，圈定代码区域，在 `regions.json` 中按阅读顺序列出区域。坐标单位为 PDF 点，原点位于页面左上角，`page` 是从 1 开始的物理页码。例如：

```json
[
  {"page": 4, "bbox": [60, 100, 530, 740], "left": 60, "char_width": 6},
  {"page": 5, "bbox": [60, 70, 530, 300], "left": 60, "char_width": 6}
]
```

```text
python <skill>/scripts/recover_content.py code <project>/source/glyphs recovered.py --regions regions.json --python-check
```

按等宽字形横坐标恢复空格；默认筛选字体名 `Mono|Courier|Consolas`，可用每个区域的 `font_pattern` 调整。省略 `left/char_width` 时按所有选定区域的公共左边界和字符宽度中位数推定，跨页不会重新清零缩进。首段代码本来有缩进、跨页页边距改变、字体变化时应显式设置。工具无法确定 PDF 中原本是 tab 还是空格，也不会猜测缺字或自动补齐代码。

`recovered.py.json` 记录每个输出行的物理页码、坐标和推定参数；未对齐字符网格会产生警告。空白行、混合字体、换行续接和多栏代码仍须对照页图。`--python-check` 仅执行 `ast.parse`，结果通过也不证明程序行为一致；不会运行代码。

## 公式编号清点

```text
python <skill>/scripts/recover_content.py equations <project>/source/glyphs equation-numbers.json
```

清点形如 `(3)`、`(2.1)`、`(B.2)`、`(2.1a)` 的候选编号，保留页码、坐标、上下文。默认以页面宽度的 65% 为右侧编号区起点，可通过 `--right-fraction` 调整；报告右侧候选中的重复及数字序列内部缺口。没有自动认定章节从 1 起编号，不展开超大缺口列表。

正文引用可能恰好落在右侧，无编号公式及乱码可能漏检；候选不等同于实际公式数。应结合原图筛选候选，再与转换稿的实际 `tag/label/eqref` 对照。工具不恢复公式语义、不修改公式或编号。

## 源页定位

```text
python <skill>/scripts/recover_content.py locate <project>/source/glyphs locations.json --query "关键词或代码片段"
python <skill>/scripts/recover_content.py locate <project>/source/glyphs locations.json --query "定理.*2" --regex
```

返回匹配行的物理页码、包围框、文字和对应字形资料文件。按行搜索，不承诺跨行词组、复杂数学阅读顺序或无文本层扫描件的匹配。报告带原 PDF SHA-256，可直接用于现有重建记录和 `% Source PDF page N` 注释。

所有命令拒绝覆盖已有输出；生成新文件后核对再采用。单篇论文的特殊规则继续保存在其工程中，不写回这些通用脚本。
