# Slay the FSM (杀戮有限状态机) 🃏

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

一个基于 **FastAPI** 的轻量级数据驱动卡牌回合制游戏原型。本项目核心旨在展示 **有限状态机 (FSM)** 和 **策略模式 (Strategy Pattern)** 在游戏逻辑控制与效果结算系统中的应用。

---

## 🌟 技术亮点

### 1. 确定性有限状态机 (FSM)
游戏主流程通过 FSM 严格控制，确保状态转移的确定性与逻辑解耦：
- **状态列表**：`PLAYER_TURN` (玩家回合), `ENEMY_TURN` (敌人回合), `VICTORY` (胜利), `GAME_OVER` (失败), `REWARD_SELECTION` (TODO: 奖励选择)。
- **转换逻辑**：所有状态跳转集中在 `GameManager` 中，避免了逻辑散落在业务代码中。

### 2. 策略模式效果分发 (Effect Handler Map)
卡牌与怪物效果采用“注册表”模式，极大提升了扩展性：
- 使用 `EFFECT_HANDLERS` 映射表代替冗长的 `if/else`。
- **解耦设计**：引入 `pending_actions`（延迟动作队列），实现了效果结算与流程控制的完全分离。

### 3. 数据驱动的怪物 AI
怪物行为不再是简单的随机攻击，而是具备“意图”与“状态机”的高级 AI：
- **意图系统**：玩家可预知怪物的下一步行动（伤害、防御、施加状态）。
- **动态转换**：支持在 `enemies.json` 中配置复杂的条件转换（例如：血量低于 50% 时进入狂暴状态）。

### 4. 丰富的状态结算系统
- **中毒 (Poison)**：回合结算伤害，层数衰减。
- **荆棘 (Thorns)**：受到攻击时按层数反弹伤害。
- **灾厄 (Curse)**：引入“斩杀线”逻辑，当目标 HP 低于层数时直接击杀。

---

## 🛠️ 技术栈

- **后端**: Python 3.10+, FastAPI, Pydantic (数据验证)
- **前端**: 原生 HTML5, TailwindCSS (样式), JavaScript (Fetch API)
- **数据**: JSON (卡牌、敌人、关卡配置)

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install fastapi uvicorn pydantic
```

### 2. 启动游戏
```bash
python app.py
```
访问地址：`http://localhost:8000`

---

## 📂 项目结构

```plaintext
/
├── app.py              # 后端核心：FastAPI 路由、GameManager、效果处理器
├── cards.json          # 全量卡牌库：定义消耗、效果与描述
├── enemies.json        # 怪物状态机配置：定义行为、转换条件与意图
├── levels.json         # 关卡序列定义
├── index.html          # 前端单页面
├── DFA.md              # 状态转移设计文档
└── GEMINI.md           # 项目开发手册与规范
```

---

## 🎮 游戏玩法
1. **抽牌**：每回合自动补满 5 张牌。
2. **出牌**：拖动卡牌上划（或点击）出牌，消耗能量执行效果。
3. **策略**：观察怪物的“意图”，决定是全力输出还是叠甲防御。
4. **进阶**：利用“中毒”和“灾厄”效果对高血量敌人进行比例伤害或直接斩杀。

---

## 🤝 协作建议
- **扩展卡牌**：直接修改 `cards.json` 即可添加新卡，无需修改代码。
- **扩展机制**：在 `app.py` 的 `EFFECT_HANDLERS` 中注册新函数。
- **设计 AI**：在 `enemies.json` 中为怪物设计更复杂的 `states` 循环。

---

## 📄 开源协议
本项目采用 [MIT License](LICENSE) 协议。
