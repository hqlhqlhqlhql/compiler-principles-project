你是一名经验丰富的后端工程师，请帮助我重构一个基于 FastAPI 的卡牌回合制小游戏项目，使其结构更清晰、易扩展，同时保证在 6 天内可以完成实现。

⚠️ 重要要求（必须遵守）：

* 只实现“核心骨架 + 少量示例功能”
* 故意保留未完成部分（用 TODO 标注）
* 不要实现完整系统
* 代码必须适合6人小组协作扩展

---

## 技术栈

* 后端：Python + FastAPI
* 前端：HTML + TailwindCSS + JavaScript
* 数据存储：JSON（用于卡牌定义）

---

## 当前问题

目前项目中有一个 GameManager 类，存在以下问题：

* 同时负责：游戏状态、卡牌逻辑、敌人AI、回合控制（FSM）、日志
* 卡牌逻辑写死（if card.type == "ATTACK"）
* 不利于后续扩展（如中毒、荆棘、灾厄等机制）

---

## 项目目标

重构代码，使其能够体现“有限状态机（FSM）”思想，并支持扩展卡牌机制，同时保证低耦合，便于团队协作开发。

---

## 必须满足的要求

### 1️⃣ 保留 FSM 核心结构

游戏主状态：

* PLAYER_TURN（玩家回合）
* ENEMY_TURN（敌人回合）
* VICTORY（胜利）
* GAME_OVER（失败）

要求：

* 状态转移清晰
* 每个输入（play_card / end_turn）都有确定结果（DFA）
* FSM 逻辑集中在 GameManager 中

---

### 2️⃣ 使用 JSON 定义卡牌（必须）

示例：

{
"name": "中毒攻击",
"cost": 1,
"effects": [
{"type": "damage", "value": 5},
{"type": "apply_status", "status": "poison", "value": 3}
]
}

要求：

* 不再使用硬编码 if/else 判断卡牌类型
* 卡牌通过 JSON 加载
* 只实现 2~3 张示例卡牌

---

### 3️⃣ 实现效果系统（Effect System）

设计统一函数：

apply_effect(effect, source, target)

支持类型：

* damage（伤害）
* defend（护盾）
* apply_status（添加状态）

要求：

* 使用 effect["type"] 分发逻辑
* 不允许使用 card.type 硬编码
* 添加 TODO：支持更多效果类型

---

### 4️⃣ 实现状态系统（Status System）

每个角色包含：

status = {
"poison": int,
"thorns": int,
"curse": int
}

规则：

* 中毒（poison）：
  在敌人回合开始时触发，敌人掉血

⚠️ 要求：

* 只完整实现 poison
* thorns / curse 只保留 TODO（不要实现完整逻辑）
* 状态系统独立于 FSM（不要写死在 GameManager 中）

---

### 5️⃣ 敌人系统（必须低耦合）

实现一个简单敌人，但结构必须可扩展：

要求：

* 敌人包含：

  * name（名字）
  * hp / max_hp（血量）
  * state（NORMAL / ENRAGED）

* 实现一个独立函数：

  enemy_act(enemy, player)

* 行为规则：

  * NORMAL：攻击 6
  * ENRAGED：血量低于 50% 时进入，攻击 10

⚠️ 重要要求：

* 不要将敌人逻辑写死在 GameManager 中
* 敌人数据（名字、血量、伤害）应来自 JSON 配置
* 添加 TODO：

  * 支持多敌人
  * 支持 JSON 配置敌人 FSM
  * 更复杂 AI 行为

---

### 6️⃣ 简单关卡系统（轻量实现）

实现基础关卡框架：

* 使用 level 表示当前关卡
* 在 VICTORY 状态下，通过 next_level 进入下一关（不要 reset 游戏）
* 每关敌人参数可调整（例如血量、攻击）

要求：

* 使用 JSON 简单记录关卡配置（如每关对应哪个敌人）
* 只实现线性关卡（不要做地图/肉鸽系统）

⚠️ 必须添加 TODO：

* 多关卡类型
* 奖励系统
* 地图/分支结构

---

### 7️⃣ 前端要求（非常重要）

* 所有界面展示必须使用中文
* 包括：

  * 按钮（如“出牌”“结束回合”）
  * 状态提示（如“玩家回合”“敌人回合”）
  * 日志信息（战斗记录）

---

### 8️⃣ 设计要求（避免过度设计）

* 不使用复杂设计模式
* 不拆太多文件（保持一个文件）
* 代码优先“易读”，而不是“高级”
* 明确分层：

  * GameManager（FSM控制）
  * Effect函数
  * Status处理
  * Enemy行为函数

---

## 请输出以下内容

---

### 1️⃣ 一份完整可运行的 FastAPI 示例代码（但只完成部分功能）

---

### 2️⃣ 示例 JSON 文件：

* cards.json（卡牌）
* enemies.json（敌人）
* levels.json（关卡）

---

### 3️⃣ 简要说明：

* 哪些功能已经实现
* 哪些功能是 TODO（留给队友扩展）

---

## 额外要求

* 代码适合初学者理解（不要太复杂）
* 明确体现 FSM 思想
* 不要一次性生成完整系统
* 简单用md语法写出目前已有的dfa并保存

模块关系图
```plaintext
GameManager（FSM）
│
├── GameState（数据）
│
├── Entity（玩家 / 敌人）
│
├── apply_effect（卡牌效果）
├── apply_status_effects（状态触发）
├── enemy_act（敌人FSM）
│
├── load_cards（JSON）
└── load_enemy（JSON）
```
