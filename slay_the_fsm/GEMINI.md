# 杀戮有限状态机 (Slay the FSM) - 项目指南

本项目是一个基于 FastAPI 的卡牌回合制小游戏原型，旨在展示有限状态机 (FSM) 在游戏逻辑控制中的应用。项目采用数据驱动设计，便于团队协作扩展。

## 项目概览
- **目的**：通过 FSM 管理游戏状态，实现低耦合的卡牌效果系统、敌人 AI 及关卡流程。
- **核心技术**：
  - **后端**：Python + FastAPI + Pydantic
  - **前端**：HTML5 + TailwindCSS + JavaScript (原生 fetch API)
  - **数据存储**：JSON 文件 (存储卡牌、敌人及关卡配置)
- **核心架构**：
  - `GameManager` (FSM 控制器)：管理 `PLAYER_TURN`, `ENEMY_TURN`, `VICTORY`, `GAME_OVER` 四个主状态。
  - **效果系统 (Effect System)**：通过 `apply_effect` 函数统一分发卡牌和敌人行为。
  - **状态系统 (Status System)**：独立的状态结算逻辑 (如中毒)。
  - **抽卡循环**：实现标准的 抽牌堆 -> 手牌 -> 弃牌堆 循环，支持自动洗牌。

## 构建与运行
- **运行环境**：Python 3.10+
- **安装依赖**：
  ```bash
  pip install fastapi uvicorn pydantic
  ```
- **启动服务**：
  ```bash
  python app.py
  ```
  服务默认在 `http://localhost:8000` 运行。

## 开发约定
- **FSM 逻辑**：所有状态转移必须在 `GameManager` 中完成，确保逻辑集中且确定。
- **数据驱动**：严禁在代码中硬编码卡牌或敌人属性，所有配置应更新至对应的 `.json` 文件。
- **扩展机制**：
  - **卡牌效果**：在 `apply_effect` 中添加新的 `type`。
  - **状态效果**：在 `apply_status_effects` 中实现 `TODO` 部分 (如荆棘、灾厄)。
  - **敌人 AI**：通过 `enemies.json` 的 `actions` 字段配置不同状态下的行为。
- **UI 规范**：前端展示必须使用中文，按钮和日志提示应清晰易懂。

## 关键文件说明
- `app.py`：后端核心逻辑，包含 FastAPI 路由、数据模型及 `GameManager`。
- `index.html`：单页面前端，负责渲染游戏状态及处理用户交互 (点击、上划出牌)。
- `cards.json`：定义卡牌的消耗、效果及描述。
- `enemies.json`：定义敌人的血量及行为 FSM。
- `levels.json`：定义线性关卡序列。
- `DFA.md`：详细描述了游戏状态机的转移图及确定性输入。

## TODO (待扩展功能)
- [ ] 实现 `thorns` (荆棘) 和 `curse` (灾厄) 状态逻辑。
- [ ] 增加更多卡牌效果类型 (如抽牌、回血、能量回复)。
- [ ] 扩展敌人 AI，支持 JSON 配置的复杂行为树。
- [ ] 增加关卡奖励选择系统及更复杂的地图结构。
