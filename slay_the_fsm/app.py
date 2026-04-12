from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random
import json
import os

app = FastAPI()

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 数据模型 ---

class Entity(BaseModel):
    name: str
    hp: int
    max_hp: int
    shield: int = 0
    status: Dict[str, int] = {"poison": 0, "thorns": 0, "curse": 0}
    state: str = "NORMAL" # NORMAL, ENRAGED
    actions: Dict[str, Any] = {} # 从 JSON 加载的动作配置

class Card(BaseModel):
    id: str
    instance_id: Optional[int] = None # 用于区分手牌中的不同实例
    name: str
    cost: int
    effects: List[Dict[str, Any]]
    description: str

class GameState(BaseModel):
    player: Entity
    enemy: Entity
    deck: List[str] = []      # 抽牌堆 (card_id)
    hand: List[Card] = []     # 当前手牌 (完整对象)
    discard: List[str] = []   # 弃牌堆 (card_id)
    energy: int = 3
    max_energy: int = 3
    turn: int = 1
    level: int = 1
    current_state: str = "PLAYER_TURN" # PLAYER_TURN, ENEMY_TURN, VICTORY, GAME_OVER
    logs: List[str] = []

# --- 核心逻辑系统 ---

def apply_effect(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    """效果分发系统 (Effect System)"""
    eff_type = effect.get("type")
    value = effect.get("value", 0)

    if eff_type == "damage":
        # 计算伤害 (减去护盾)
        actual_damage = max(0, value - target.shield)
        target.shield = max(0, target.shield - value)
        target.hp -= actual_damage
        state.logs.append(f"{source.name} 造成了 {value} 点伤害 (目标吸收 {value - actual_damage}，实际扣除 {actual_damage})")
    
    elif eff_type == "defend":
        source.shield += value
        state.logs.append(f"{source.name} 获得了 {value} 点护甲")
    
    elif eff_type == "apply_status":
        status_name = effect.get("status")
        target.status[status_name] = target.status.get(status_name, 0) + value
        state.logs.append(f"{target.name} 被施加了 {value} 层 {status_name}")

    # TODO: 支持更多效果类型 (如 draw_cards, heal, energy_gain 等)

def apply_status_effects(entity: Entity, state: GameState):
    """状态触发系统 (Status System)"""
    # 1. 中毒 (Poison): 每次触发掉血，且层数减 1
    poison = entity.status.get("poison", 0)
    if poison > 0:
        entity.hp -= poison
        entity.status["poison"] -= 1
        state.logs.append(f"{entity.name} 受到 {poison} 点中毒伤害，剩余中毒层数: {entity.status['poison']}")
    
    # TODO: 实现 thorns (荆棘) 逻辑
    # TODO: 实现 curse (灾厄) 逻辑

def enemy_act(enemy: Entity, player: Entity, state: GameState):
    """敌人行为系统 (Enemy AI)"""
    # 更新敌人 FSM 状态
    if enemy.hp < (enemy.max_hp / 2) and enemy.state == "NORMAL":
        enemy.state = "ENRAGED"
        state.logs.append(f"😡 {enemy.name} 进入狂暴状态！")
    
    # 从配置中读取当前状态下的行为
    action_cfg = enemy.actions.get(enemy.state, {"damage": 6})
    damage = action_cfg.get("damage", 6)
    
    # 执行攻击
    apply_effect({"type": "damage", "value": damage}, enemy, player, state)

# --- 游戏管理器 (FSM) ---

class GameManager:
    def __init__(self):
        self.cards_pool = self._load_json("cards.json")
        # 转化为字典便于快速查找
        self.cards_dict = {c["id"]: c for c in self.cards_pool}
        self.enemies_data = self._load_json("enemies.json")
        self.levels_data = self._load_json("levels.json")
        
        # 实例 ID 计数器，保证唯一性
        # self.card_instance_counter = 0
        
        # 验证必要数据是否加载
        if not self.levels_data:
            raise RuntimeError("CRITICAL: levels.json 无法加载或为空")
        if not self.enemies_data:
            raise RuntimeError("CRITICAL: enemies.json 无法加载或为空")
        if not self.cards_dict:
            raise RuntimeError("CRITICAL: cards.json 无法加载或为空")
            
        self.state = self.init_game()

    def _load_json(self, filename):
        path = os.path.join(BASE_DIR, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def init_deck(self):
        """初始化基础牌组"""
        # 示例：5张打击，5张防御，1张中毒
        basic_deck = ["strike"] * 5 + ["defend"] * 5 + ["poison_stab"] * 1
        random.shuffle(basic_deck)
        self.state.deck = basic_deck
        self.state.discard = []
        self.state.hand = []

    def init_game(self, level=1):
        # 加载关卡配置
        level_cfg = next((l for l in self.levels_data if l["level"] == level), self.levels_data[0])
        enemy_cfg = next((e for e in self.enemies_data if e["id"] == level_cfg["enemy_id"]), self.enemies_data[0])
        
        player = Entity(name="勇者", hp=50, max_hp=50)
        enemy = Entity(
            name=enemy_cfg["name"], 
            hp=enemy_cfg["max_hp"], 
            max_hp=enemy_cfg["max_hp"],
            actions=enemy_cfg.get("actions", {})
        )
        
        self.state = GameState(
            player=player,
            enemy=enemy,
            level=level,
            logs=[f"--- 第 {level} 关: {enemy.name} 出现了！ ---"]
        )
        # 初始化牌组并抽取首轮手牌
        self.init_deck()
        self.draw_cards(5)
        return self.state

    def draw_cards(self, count: int):
        """循环抽牌逻辑"""
        for _ in range(count):
            # 1. 如果抽牌堆为空，将弃牌堆洗回抽牌堆
            if not self.state.deck:
                if not self.state.discard:
                    self.state.logs.append("⚠️ 没牌可抽了！")
                    break
                self.state.logs.append("🔄 正在重新洗牌...")
                self.state.deck = self.state.discard[:]
                random.shuffle(self.state.deck)
                self.state.discard = []

            # 2. 抽牌
            card_id = self.state.deck.pop()
            card_data = self.cards_dict.get(card_id)
            if card_data:
                # 创建卡牌实例并赋予唯一递增 ID
                card_instance = Card(**card_data)
                # self.card_instance_counter += 1
                card_instance.instance_id = random.randint(1, 1000000)
                self.state.hand.append(card_instance)

    def play_card(self, instance_id: int):
        if self.state.current_state != "PLAYER_TURN":
            raise HTTPException(status_code=400, detail="不是玩家的回合")
        
        # 查找卡牌
        card_idx = next((i for i, c in enumerate(self.state.hand) if c.instance_id == instance_id), -1)
        if card_idx == -1:
            raise HTTPException(status_code=404, detail="卡牌未找到")
        
        card = self.state.hand[card_idx]
        if self.state.energy < card.cost:
            raise HTTPException(status_code=400, detail="能量不足")

        # 1. 消耗能量并移出手牌
        self.state.energy -= card.cost
        played_card = self.state.hand.pop(card_idx)
        
        # 2. 放入弃牌堆
        self.state.discard.append(played_card.id)
        
        # 3. 执行效果
        for effect in card.effects:
            apply_effect(effect, self.state.player, self.state.enemy, self.state)

        # 检查战斗结束 (DFA 转换)
        self.check_battle_end()

    def check_battle_end(self):
        if self.state.enemy.hp <= 0:
            self.state.enemy.hp = 0
            self.state.current_state = "VICTORY"
            self.state.logs.append("战斗胜利！")
        elif self.state.player.hp <= 0:
            self.state.player.hp = 0
            self.state.current_state = "GAME_OVER"
            self.state.logs.append("你被击败了...")

    def end_turn(self):
        if self.state.current_state != "PLAYER_TURN":
            return

        # --- 回合结束逻辑 ---
        # 1. 将手牌移动到弃牌堆
        for card in self.state.hand:
            self.state.discard.append(card.id)
        self.state.hand = []

        # --- 转移到敌人回合 ---
        self.state.current_state = "ENEMY_TURN"
        self.state.logs.append(">>> 敌人回合开始")
        
        # 1. 触发敌人身上的状态效果 (如中毒)
        apply_status_effects(self.state.enemy, self.state)
        self.check_battle_end()
        
        if self.state.current_state == "ENEMY_TURN":
            # 2. 敌人行动
            enemy_act(self.state.enemy, self.state.player, self.state)
            self.check_battle_end()

        # --- 转移回玩家回合 ---
        if self.state.current_state == "ENEMY_TURN":
            self.state.current_state = "PLAYER_TURN"
            self.state.turn += 1
            self.state.energy = self.state.max_energy
            self.state.player.shield = 0 # 玩家护甲每回合清空
            self.draw_cards(5) # 补满 5 张
            self.state.logs.append(f"--- 第 {self.state.turn} 回合 ---")
            
            # TODO: 玩家回合开始时触发玩家身上的状态 (如诅咒)

    def next_level(self):
        if self.state.current_state != "VICTORY":
            raise HTTPException(status_code=400, detail="未获得胜利，无法进入下一关")
        
        next_lvl = self.state.level + 1
        # 保留玩家当前血量，进入下一关
        current_hp = self.state.player.hp
        self.state = self.init_game(next_lvl)
        self.state.player.hp = current_hp
        
        # TODO: 支持关卡上限检查
        # TODO: 关卡奖励选择系统

# --- API 路由 ---

manager = GameManager()

@app.get("/", response_class=HTMLResponse)
def get_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/game/status")
def get_status():
    return manager.state

@app.post("/api/game/play/{instance_id}")
def play_card(instance_id: int):
    manager.play_card(instance_id)
    return manager.state

@app.post("/api/game/end-turn")
def end_turn():
    manager.end_turn()
    return manager.state

@app.post("/api/game/next-level")
def next_level():
    manager.next_level()
    return manager.state

@app.post("/api/game/reset")
def reset():
    manager.state = manager.init_game(1)
    return manager.state

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
