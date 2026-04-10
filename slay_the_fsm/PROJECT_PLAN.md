# 项目计划书：基于有限自动机的卡牌游戏 (FSM-Spire)

## 1. 项目概览
*   **目标**：模仿《杀戮尖塔》，实现一个基于 **有限自动机 (FSM)** 驱动的单机卡牌战斗系统。
*   **核心学术点**：使用 FSM 严格建模游戏逻辑转换，展示状态（States）、事件（Events）与转换（Transitions）的编译原理核心思想。
*   **技术栈**：
    *   **后端**：Python (FastAPI) —— 负责核心 FSM 逻辑与数值计算。
    *   **前端**：HTML5 + Tailwind CSS + Vanilla JS —— 负责 UI 渲染与状态可视化。
    *   **通讯**：RESTful API (JSON)。

---

## 2. 有限自动机 (FSM) 模型设计
这是本项目的“灵魂”，需在实验报告中重点描述。

### 2.1 状态定义 (States)
*   `INIT`: 游戏初始化（生成手牌、怪物）。
*   `PLAYER_DRAW`: 抽牌阶段（处理抽牌逻辑与动画）。
*   `PLAYER_WAIT`: 等待玩家操作（核心停留状态）。
*   `CARD_RESOLVING`: 卡牌结算（处理伤害、防御、Buffer）。
*   `ENEMY_TURN`: 敌人行动阶段（AI 逻辑执行）。
*   `CHECK_STATUS`: 胜负判定（检查 HP 是否归零）。
*   `VICTORY / GAME_OVER`: 游戏终点。

### 2.2 转换逻辑 (Transitions)
| 起始状态 | 触发事件 (Event) | 目标状态 | 动作 (Action) |
| :--- | :--- | :--- | :--- |
| `INIT` | `START_BATTLE` | `PLAYER_DRAW` | 初始化数值 |
| `PLAYER_DRAW` | `DRAW_COMPLETE` | `PLAYER_WAIT` | 开启玩家操作权限 |
| `PLAYER_WAIT` | `PLAY_CARD` | `CARD_RESOLVING` | 扣除能量，计算效果 |
| `CARD_RESOLVING` | `EFFECT_DONE` | `CHECK_STATUS` | 刷新血条 |
| `PLAYER_WAIT` | `END_TURN` | `ENEMY_TURN` | 弃牌，怪物准备攻击 |
| `ENEMY_TURN` | `ENEMY_DONE` | `PLAYER_DRAW` | 回合数+1 |

---

## 3. 团队分工 (6人)

### **组长 (1人)：系统架构与集成**
*   **职责**：定义后端 API 契约，负责前后端代码联调，监督进度。
*   **关键任务**：确保后端返回的 JSON 结构能被前端正确解析。

### **后端组 (2人)：FSM 引擎与数据管理**
*   **成员 A (FSM Master)**：在 FastAPI 中实现 `GameManager` 类，用字典或类模式硬编码状态转换表。
*   **成员 B (战斗逻辑)**：编写具体的数值计算逻辑（伤害计算、防御堆叠、怪物 AI 简单行为）。

### **前端组 (2人)：Tailwind 界面与交互**
*   **成员 C (UI/UX Designer)**：使用 Tailwind CSS 绘制暗黑风格界面，设计卡牌组件（悬停缩放、发光效果）。
*   **成员 D (JS Connector)**：使用 JS `fetch` 轮询或调用 API，管理前端变量同步。

### **可视化与文档 (1人)：理论展示与 QA**
*   **核心任务**：在页面侧边栏开发 **“实时状态机追踪器”**（用 HTML 元素画出状态图，当前状态高亮），并撰写符合编译原理要求的实验报告。

---

## 4. 8 天冲刺里程碑

| 天数 | 阶段 | 目标 | AI 辅助策略 |
| :--- | :--- | :--- | :--- |
| **Day 1-2** | **建模与框架** | 完成 FastAPI 基础路由，前端 Tailwind 静态布局展示。 | 让 AI 生成“FastAPI 状态机类骨架”和“Tailwind 战斗界面布局”。 |
| **Day 3-4** | **逻辑开发** | 后端实现状态跳转；前端实现卡牌渲染和点击。 | 让 AI 生成“卡牌数组的 JSON 示例”和“JS 处理点击卡牌的事件流”。 |
| **Day 5-6** | **核心集成** | 跑通“出牌-扣血-怪物反击”的完整 FSM 循环。 | 让 AI 辅助排查“后端状态不更新”或“前端渲染冲突”的 Bug。 |
| **Day 7** | **可视化亮点** | 侧边栏“状态机实时日志”上线。 | 让 AI 写一个“JS 实时滚动日志组件”。 |
| **Day 8** | **交付** | 录制演示 Demo，整理实验报告。 | 让 AI 根据代码逻辑生成“状态转换图 (Mermaid)”给文档使用。 |

---

## 5. 关键协议 (API 示例)
**GET `/game/status`**
返回当前游戏全景，前端根据 `current_state` 决定哪些按钮可点。
```json
{
  "current_state": "PLAYER_WAIT",
  "player": { "hp": 50, "energy": 3, "shield": 5 },
  "hand": [
    { "id": 1, "name": "Strike", "dmg": 6, "cost": 1 },
    { "id": 2, "name": "Defend", "shield": 5, "cost": 1 }
  ],
  "enemy": { "name": "Ironclad", "hp": 45, "intent": "ATTACK" },
  "last_event": "DRAW_COMPLETE"
}
```

---

## 6. 评审加分项 (组长关注)
1.  **确定性**：在文档中强调你的状态机是 **DFA (确定性有限自动机)**，不存在状态模糊。
2.  **可视化**：演示时，左边玩游戏，右边状态图实时跳动，老师会非常满意。
3.  **健壮性**：如果玩家在 `ENEMY_TURN` 状态通过控制台强行发请求出牌，后端 FSM 必须返回 `403 Forbidden: Invalid State Transition`。
