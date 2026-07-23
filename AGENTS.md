# Agents 多智能体协作系统

Atoms MVP 采用 **4 个 AI Agent** 组成的团队，通过 SOP（标准作业流程）协作，将自然语言需求自动转化为可运行的 Web 应用。

---

## 架构概览

```
用户输入 → Team Lead (Mike) → PM (Emma) → Architect (Bob) → Engineer (Alex) → 代码输出
              │                   │              │                  │
              │ 分析需求           │ 生成 PRD     │ 设计架构          │ 编写代码 + 工具调用
              │ 输出 JSON 计划     │ 输出 JSON    │ 输出 JSON         │ 输出可运行文件
```

---

## Agent 角色定义

### 1. Team Lead — Mike

| 属性 | 值 |
|------|-----|
| **内部名称** | `team_lead` |
| **角色** | Team Lead |
| **工具** | 无（纯分析角色） |
| **文件** | [backend/agents/team_lead.py](../backend/agents/team_lead.py) |

**职责**：分析用户需求，生成结构化任务计划。

**输出格式**（JSON）：
```json
{
  "summary": "一句话总结用户需求",
  "task_type": "web_app | landing_page | tool | game | dashboard | other",
  "complexity": "simple | medium | complex",
  "recommended_mode": "engineer | team",
  "instructions_for_pm": "PM 应关注的内容",
  "instructions_for_architect": "Architect 应关注的内容",
  "instructions_for_engineer": "Engineer 的关键技术要点",
  "key_requirements": ["核心需求1", "核心需求2"]
}
```

**决策规则**：
- 简单任务（todo 列表、计算器、落地页）→ 推荐 `engineer` 模式
- 复杂任务（多页应用、仪表盘、游戏）→ 推荐 `team` 模式

---

### 2. PM — Emma

| 属性 | 值 |
|------|-----|
| **内部名称** | `pm` |
| **角色** | Product Manager |
| **工具** | 无（纯文档角色） |
| **文件** | [backend/agents/pm.py](../backend/agents/pm.py) |

**职责**：基于 Team Lead 的分析，生成产品需求文档（PRD）。

**输出格式**（JSON）：
```json
{
  "project_name": "项目名称",
  "goal": "项目目标一句话",
  "user_stories": ["作为用户，我可以...", "..."],
  "features": [
    { "name": "功能名", "description": "详细描述", "priority": "high|medium|low" }
  ],
  "ui_requirements": {
    "pages": ["页面1", "页面2"],
    "components": ["组件1", "组件2"],
    "style": "modern | minimalist | playful | professional"
  },
  "technical_notes": "技术注意事项"
}
```

**规则**：
- 只输出 JSON，不输出其他内容
- 功能描述具体可执行
- 只包含 MVP 所需功能
- 用户故事可测试、可验证
- 风格匹配项目类型（游戏用 playful，仪表盘用 professional）

---

### 3. Architect — Bob

| 属性 | 值 |
|------|-----|
| **内部名称** | `architect` |
| **角色** | Software Architect |
| **工具** | 无（纯设计角色） |
| **文件** | [backend/agents/architect.py](../backend/agents/architect.py) |

**职责**：基于 PRD 设计技术架构。

**输出格式**（JSON）：
```json
{
  "tech_stack": {
    "frontend": "HTML/CSS/JS | React | Vue | ...",
    "styling": "Tailwind CSS | plain CSS | ...",
    "state_management": "None | Zustand | Redux | ...",
    "build_tool": "None | Vite | Webpack | ..."
  },
  "directory_structure": ["index.html", "src/", "src/App.tsx", "..."],
  "data_model": {
    "entities": [{ "name": "...", "fields": [...] }],
    "storage": "localStorage | IndexedDB | in-memory | ..."
  },
  "component_tree": {
    "App": ["Header", "MainContent", "Footer"],
    "MainContent": ["ItemList", "ItemForm"]
  },
  "api_design": { "description": "..." },
  "implementation_notes": "..."
}
```

**规则**：
- 简单 MVP 优先用单个 index.html（内嵌 CSS/JS），避免过度工程化
- 只在确实需要复杂状态管理或路由时才推荐 React/Vite
- 文件路径和组件名必须具体明确

---

### 4. Engineer — Alex

| 属性 | 值 |
|------|-----|
| **内部名称** | `engineer` |
| **角色** | Senior Full-Stack Engineer |
| **工具** | `write_file` / `read_file` / `list_dir` / `run_shell` |
| **文件** | [backend/agents/engineer.py](../backend/agents/engineer.py) |

**职责**：将需求/PRD/架构设计转化为可运行的代码。

**工作流程**：
1. 先用 1-2 句话说明计划
2. 调用 `write_file` 创建文件（`index.html` → `styles.css` → 其他）
3. 用 `list_dir` 验证文件结构
4. 完成后输出摘要

**设计规范**：
- 现代配色（蓝色、紫色、渐变）
- 平滑过渡和悬停效果
- 移动端和桌面端响应式
- 合适的间距、排版和视觉层次
- 微妙的阴影和圆角

---

## 工具集（仅 Engineer 可用）

| 工具 | 描述 | 参数 |
|------|------|------|
| `write_file` | 创建或更新文件 | `path`（相对路径）, `content`（文件内容） |
| `read_file` | 读取文件内容 | `path`（相对路径） |
| `list_dir` | 列出目录内容 | `path`（相对路径，默认 `.`） |
| `run_shell` | 执行 Shell 命令 | `command`（命令）, `cwd`（工作目录） |

**安全限制**：
- 所有文件操作限制在项目目录内（路径穿越防护）
- Shell 命令白名单：`npm`、`npx`、`node`、`ls`、`cat`、`mkdir`、`cd`、`echo`、`pwd`
- Shell 命令超时 60 秒

---

## 执行模式

### Engineer Mode（单 Agent）

```
用户输入 → Alex (Engineer) → 代码输出
```

- 适用场景：简单任务（todo 列表、计算器、落地页）
- 耗时最短，约 30 秒 - 2 分钟

### Team Mode（4 Agent 流水线）

```
用户输入 → Mike (Team Lead) → Emma (PM) → Bob (Architect) → Alex (Engineer) → 代码输出
```

- 适用场景：复杂任务（多页应用、仪表盘、游戏）
- 每个 Agent 的输出作为下一个 Agent 的输入（上下文传递）
- 耗时约 2 - 5 分钟

### Race Mode（并行竞赛）

```
用户输入 ─┬─ Alex (Model A) → 代码 A
          ├─ Alex (Model B) → 代码 B
          └─ Alex (Model C) → 代码 C
                    ↓
              用户选择最佳结果
```

- 适用场景：对质量要求高、愿意等待
- 3 个相同 Engineer Agent 用不同 LLM 模型并行生成代码
- 用户从 3 份结果中手动选择最佳版本

---

## Base Agent 基类

所有 Agent 继承自 `Agent(ABC)` 基类：

```python
class Agent(ABC):
    name: str          # 内部标识符，如 "engineer"
    role: str          # 显示名称，如 "Senior Full-Stack Engineer"
    system_prompt: str # 系统提示词，定义 Agent 的行为和输出格式

    @abstractmethod
    def tools(self) -> Optional[list]:  # 返回可用工具列表
    def get_system_message(self) -> dict:  # 返回 LLM 格式的 system message
```

**文件**：[backend/agents/base.py](../backend/agents/base.py)

---

## ReAct 循环

每个 Agent 执行时通过 ReAct（Reasoning + Acting）循环运行：

```
for step in range(MAX_STEPS=15):
    LLM 生成回复（流式）
    ├── 有 tool_calls → 执行工具 → 结果反馈给 LLM → 继续循环
    └── 无 tool_calls → Agent 完成，输出最终结果
```

**文件**：[backend/orchestrator/runner.py](../backend/orchestrator/runner.py)

---

## 总结

| Agent | 角色 | 有工具？ | 输出 |
|-------|------|---------|------|
| Mike | Team Lead | ❌ | JSON 任务计划 |
| Emma | PM | ❌ | JSON PRD |
| Bob | Architect | ❌ | JSON 架构设计 |
| Alex | Engineer | ✅ (4 tools) | 可运行代码文件 |