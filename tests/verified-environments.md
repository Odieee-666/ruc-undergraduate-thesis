# 实际验证记录

本表区分实测结果和 CI 目标配置，不把已写入工作流的环境称为已通过。

## 2026-11-18 本机 Windows

Windows 11，Python **3.12.14**。使用新建 venv，从 `tests/requirements.txt` 下载并安装依赖，未继承运行时的 Python site-packages；XeLaTeX/Biber 和严格字体使用本机已有安装，因此这不是全新 Windows 系统的验证。

| 依赖 | 实际验证版本 |
|---|---|
| MiKTeX / XeTeX | MiKTeX 25.12 / MiKTeX-XeTeX 4.16 |
| Biber | 2.21 |
| Pandoc | 3.14 |
| pypdfium2 | 5.15.2 |
| Pillow | 13.0.0 |
| pdfplumber | 0.11.10 |
| pypdf | 6.21.4 |
| ReportLab | 4.5.1 |
| Fandol | 0.3（本次补装） |
| TeX Gyre | 2.501 |

28 项回归测试通过，覆盖导入保真边界、依赖缺失、阶段失败恢复、源输入/检查点变化、并发锁、代码缩进、编号候选和源页定位。通用工具的三个 CLI 入口也已对合成 PDF 的字形资料运行。

真实命令行验证使用 `python tests/smoke_clean.py --strict-fonts`：三种格式导入、编译及渲染；预览字体示例的实际参考文献处理；严格字体环境检查与示例构建。每次运行在 `output/clean-smoke-*/verified-versions.json` 记录最终 `passed/failed`，同时保留环境报告、宏包版本、pip freeze 和失败日志。失败运行不覆盖先前记录。

## 待 CI 验证

| 目标系统 | Python | TeX / Pandoc | 状态 |
|---|---|---|---|
| windows-2022 | 3.10、3.12 | TeX Live 2025 / Pandoc 3.8.3 | 工作流已配置，尚未远端运行 |
| ubuntu-24.04 | 3.10、3.12 | TeX Live 2025 / Pandoc 3.8.3 | 工作流已配置，尚未远端运行 |

工作流关闭 TeX Live 缓存，每次安装测试所需集合，不依赖开发机私有路径。各矩阵任务在完成真实测试后，以 artifact 保留解析出的 Python/TeX 版本及报告。只有对应任务通过后，才可将目标环境补记为已验证。本次未推送仓库或触发远端 CI，本机也没有可用 Linux 运行环境。

CI 使用开放的预览字体；商业严格字体的跨平台安装，以及真实 Tesseract OCR 识别质量，不属于已验证范围。
