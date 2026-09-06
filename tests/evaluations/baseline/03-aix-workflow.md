# Baseline Response: Released AIX Workflow

- Scenario: `tests/scenarios/03-aix-workflow.md`
- Conditions: fresh subagent, no web access, no workspace inspection, no AIUI-specific Skill
- Captured: 2026-09-07

## Verbatim response

```bash
# 前置：眼镜开启开发者模式，通过 USB 连接电脑，并确保 AIX CLI 已安装
aix --version

# 1. 创建项目
aix create rokid-aiui-agent
cd rokid-aiui-agent

# 2. 本地开发
aix dev
```

确认本地功能正常后按 `Ctrl+C` 停止开发服务器，再执行：

```bash
# 3. 构建
aix build

# 4. 部署到已连接的眼镜
aix deploy
```

一条连续命令版：

```bash
aix create rokid-aiui-agent \
  && cd rokid-aiui-agent \
  && aix dev
# 验证完成后 Ctrl+C
aix build && aix deploy
```

部署后如果眼镜仍显示旧版本，先退出正在运行的旧 Agent，再重新执行 `aix deploy`。
