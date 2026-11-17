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

## 2026-11-18 GitHub CI（发布前停止）

修复版代码提交：`277a35f467a7c040d27e2dcc70f988c8826b5b18`。[运行记录](https://github.com/Odieee-666/ruc-undergraduate-thesis/actions/runs/44156212083)。用户随后要求停止测试并直接发布 v1.1.0，剩余任务已请求取消，不再重跑。

| 目标系统 | Python | TeX / Pandoc | 修复版结果 |
|---|---|---|---|
| ubuntu-24.04 | 3.10 | TeX Live 2025 / Pandoc 3.8.3 | 通过 |
| ubuntu-24.04 | 3.12 | TeX Live 2025 / Pandoc 3.8.3 | 通过 |
| windows-2022 | 3.12 | TeX Live 2025 / Pandoc 3.8.3 | 通过 |
| windows-2022 | 3.10 | TeX Live 2025 / Pandoc 3.8.3 | 安装阶段取消，未完成 |

已通过的三个组合均完成 28 项回归测试以及真实 TeX/DOCX/PDF 导入、XeLaTeX/Biber 编译、渲染与参考文献示例。不能把本轮发布描述为四个矩阵任务全部通过。

首轮两个 Windows 组合在记录宏包版本时遇到 `tlmgr` 无扩展名启动失败；已改为使用 `shutil.which` 返回的完整批处理文件路径。修复版 Windows + Python 3.12 已通过，Python 3.10 组合按用户要求停止。

CI 从新 runner 安装依赖，关闭 TeX Live 缓存。成功/失败日志与实际依赖版本保留在各任务 artifacts 中，受其保留期限制。CI 使用开放预览字体；商业严格字体的跨平台安装与真实 Tesseract OCR 识别质量不属于本轮覆盖。
