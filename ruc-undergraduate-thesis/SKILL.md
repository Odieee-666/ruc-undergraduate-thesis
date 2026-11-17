---
name: ruc-undergraduate-thesis
description: 将中国人民大学本科毕业论文的 TeX、Word 或 PDF 稿件整理为可用 XeLaTeX 和 Biber 编译的论文工程，检查内容保真与排版。用于人大本科论文模板创建、迁移和格式修复。
---

# 中国人民大学本科毕业论文

交付可编辑、资源齐全的 LaTeX 工程、编译 PDF、转换记录和检查结果。不得把“成功生成 PDF”表述为“学校审核通过”。

## 开始

1. 读取 [格式依据](references/format-basis.md)，识别适用学院、年份及用户提供的补充要求。默认配置名为 `ruc-2021-local`，是用户提供的 2022 模板所记载的历史规则，不能称为最新官方标准。明确要求优先；有冲突记录来源和选择，不猜测学院要求。
2. 在新的输出目录工作，保留输入原件。通过环境依赖工具寻找 Python；脚本入口为本 skill 的 `scripts/thesis.py`。导入会先检查对应输入依赖、XeLaTeX/Biber、关键宏包和实际可加载的字体；`doctor --input-type tex/docx/pdf` 可提前查看缺失项与修复建议。优先使用已有 MiKTeX/TeX Live，不自动安装依赖或替换严格字体；只有明确接受预览字体时使用 `--portable`。
3. 按输入读取 [输入处理](references/input-workflows.md)。先清点内容再转换。TeX 迁移保留数学、引用和标签；DOCX 通过 Pandoc 保留结构；PDF 通过逐页提取、字形坐标资料、渲染及视觉核对重建，不把整页图片当作排版完成。数学密集的原生 PDF 即使能提取大量文字，也须检查上下标、分式、跨行公式和代码缩进。

## 操作

以下 `python` 指已定位的可用解释器；`<skill>` 是本文件所在目录。脚本的 `--help` 给出全部参数。

```text
python <skill>/scripts/thesis.py doctor
python <skill>/scripts/thesis.py init <output> --metadata metadata.json
python <skill>/scripts/thesis.py import-tex manuscript.tex <output>
python <skill>/scripts/thesis.py import-docx manuscript.docx <output> --pandoc <pandoc-executable>
python <skill>/scripts/thesis.py import-pdf manuscript.pdf <output>
python <skill>/scripts/thesis.py build <output>
python <skill>/scripts/thesis.py render <output>/build/main.pdf <output>/review/pages-v1
```

`init --demo` 创建可编译演示，普通 `init` 创建待填稿。导入命令创建新工程，`conversion.json` 记录必须核对的事项。`build` 只证明构建和日志检查结果，不消除这些事项。

导入失败时读取输出旁的 `.<output名>.import/state.json` 和 `environment.json`；修复依赖后在原命令追加 `--resume`。输入或转换参数改变、检查点被编辑时用 `--retry`，旧工作区会留作备份。最终输出目录只在导入成功后出现，已存在的工程不覆盖。详见 [输入处理](references/input-workflows.md#导入失败与恢复)。

PDF 的代码缩进、公式编号清点和源页定位优先使用 `scripts/recover_content.py`，参数与局限见 [内容恢复工具](references/recovery-tools.md)。这些工具产生可追溯的候选和初稿，特定论文的公式修正仍只放在该论文工程内。

转换后填写 `metadata.tex`、`content/abstract-zh.tex`、`content/abstract-en.tex` 和 `content/body.tex`，按需填写附录与致谢，并调整 `main.tex` 的图表目录开关。元数据 JSON 示例及命令说明见输入处理文档。用户已给出的事实直接使用；缺失作者、题名、学院等不得编造。

正文使用四级标题 `section/subsection/subsubsection/paragraph`。参考文献通过 `references.bib` 和真实 `\cite` 关联；选择数字制或著者年制必须与适用规范一致。默认数字制只是兼容现有样稿的工程选择。不要保留旧模板的 `\nocite{*}`，除非确实需要列出未引用文献。

## 验收

按 [验收规则](references/acceptance.md) 检查内容、编译、版面。处理 `build/build-report.json` 中的失败与警告；逐页打开 `render` 输出，检查公式、脚注、表格、封面换行、目录和页码。视觉检查是人工/模型动作，脚本不会伪造“已验收”。

对 DOCX/PDF 的每个待核对项回到原文检查，记录实际处理过程。无法恢复的文字、公式或文献保持待确认，不用合理猜测填补。扫描 PDF 没有可靠 OCR 时，读取渲染图并转录，或说明缺少 OCR；不输出空白正文并宣称完成。旧 `.doc` 先用可用的 Word/LibreOffice 转成 `.docx`，不改扩展名伪装转换。

最终说明规范版本、产物路径、验证结果及剩余问题。默认交付源码和 PDF；Word 是输入格式，不承诺反向生成 Word。保留模板的 [来源说明](assets/template/PROVENANCE.md)。
