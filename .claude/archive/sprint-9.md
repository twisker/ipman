# Sprint 9 存档

**Sprint 9 - 多渠道分发**

**目标：** Windows 打包、多平台二进制构建、CI 自动发布

**状态：** 已完成

**完成日期：** 2026-03-14

---

## 任务列表

| 优先级 | 任务 | 状态 |
|-------|------|------|
| P1 | curl+sh 一键安装脚本 | 已完成（Sprint 8 期间） |
| P1 | iphub 定时统计 + README Top 排名 Action | 已完成 |
| P1 | 多平台 PyInstaller 打包（Linux/macOS/Windows） | 已完成 |
| P2 | GitHub Actions 发布时自动构建 + Release 上传 | 已完成 |

---

## 关键设计决策

1. **PyInstaller --onefile** — 单文件可执行，用户下载即用
2. **三平台矩阵构建** — GitHub Actions matrix 同时构建 Linux/macOS/Windows
3. **softprops/action-gh-release** — 二进制自动附加到 GitHub Release
4. **排名文件独立存储** — top-10-skills.md / top-10-packages.md / top-50-all.md，双仓库嵌入
