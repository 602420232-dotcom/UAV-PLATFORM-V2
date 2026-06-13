# Contributing to UAV Platform V2

## 开发流程

1. 从 main 分支创建短生命周期 feature 分支：`git checkout -b feat/xxx`
2. 开发完成后提交 PR，需 2 人审查通过
3. CI 全部通过（Java / Python / Frontend / Docker）
4. 合并到 main，按需发布

## 代码规范

- Java：Google Java Format + Checkstyle
- Python：ruff + mypy
- TypeScript：ESLint + Prettier
- 提交前运行 `pre-commit run --all-files`

## 提交规范

使用 Conventional Commits：

```
feat: 新功能
fix: 修复
docs: 文档
style: 格式（不影响代码逻辑）
refactor: 重构
perf: 性能优化
test: 测试
chore: 构建/工具
```

## 测试要求

- Java：单元测试覆盖率 > 60%
- Python：ruff + mypy 通过
- 集成测试：关键链路端到端
