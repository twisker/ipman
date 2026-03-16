# 当前 Sprint

## Sprint 10（Phase 5 — IpHub Awesome-List 转型, Sub-1）

**状态：** Chunk 1 + Chunk 2 已完成，Chunk 3 验证中

### Chunk 1: ipman CLI 数据模型改动 ✅
- IPPackage 6 个新字段 + parse/dump ✅
- Publisher tags/summary/changelog ✅
- Client --tag search ✅
- CLI hub search/top --tag, info 新字段 ✅

### Chunk 2: iphub 仓库模板 + 脚本 + 工作流 ✅
- i18n 翻译文件 (en + zh-cn) ✅
- README.md + HTML Landing Page 模板 ✅
- generate_pages.py + generate_trending.py ✅
- sync_tag_labels.py ✅
- rebuild-index.yml 更新（tag 聚合 + trending） ✅
- rebuild-pages.yml 新建 ✅
- validate-pr.yml tag 校验 ✅

### Chunk 3: 集成验证 + 人工事项
- [ ] GitHub Pages 启用（人工）
- [ ] 触发 rebuild-pages workflow 验证页面生成
- [ ] 触发 rebuild-index workflow 验证 tag 聚合
