from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import random
import json
import os

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 数据模型 ---

class Entity(BaseModel):
    name: str
    hp: int
    max_hp: int
    shield: int = 0
    status: Dict[str, int] = Field(default_factory=lambda: {"poison": 0, "thorns": 0, "curse": 0})
    state: str = "NORMAL"
    intent: str = "" 
    actions: Dict[str, Any] = {}

class Card(BaseModel):
    id: str
    instance_id: Optional[int] = None
    name: str
    cost: int
    effects: List[Dict[str, Any]]
    description: str

class GameState(BaseModel):
    player: Entity
    enemy: Entity
    deck: List[str] = []
    hand: List[Card] = []
    discard: List[str] = []
    energy: int = 3
    max_energy: int = 3
    turn: int = 1
    level: int = 1
    current_state: str = "PLAYER_TURN"
    logs: List[str] = []
    pending_actions: List[Dict[str, Any]] = []

# ================== 核心系统：FSM 与 效果结算 ==================

def check_survival(target: Entity, state: GameState):
    """统一检查死亡及灾厄斩杀线"""
    curse = target.status.get("curse", 0)
    if curse > 0 and target.hp > 0 and target.hp <= curse:
        target.hp = 0
        state.logs.append(f"💀 灾厄降临！{target.name} 因血量 ≤ {curse} 被直接斩杀！")
    
    if target.hp < 0: target.hp = 0

def get_actual_target(effect: Dict[str, Any], source: Entity, target: Entity):
    if effect.get("target") == "self": return source, source
    return source, target

# --- 怪物 FSM 核心驱动 ---

def update_enemy_intent(enemy: Entity):
    """同步当前状态对应的意图描述文字"""
    states_cfg = enemy.actions.get("states", {})
    current_cfg = states_cfg.get(enemy.state)
    if current_cfg:
        enemy.intent = current_cfg.get("intent", "准备中...")

def check_monster_transitions(enemy: Entity, state: GameState):
    """实时检查怪物状态切换 (例如：血量低于 50% 立即进入狂暴并刷新意图)"""
    actions_cfg = enemy.actions
    transitions = actions_cfg.get("transitions", [])
    changed = False
    for trans in transitions:
        if trans.get("condition") == "hp_below_half" and enemy.hp < (enemy.max_hp / 2):
            if trans.get("from") == "ANY" or trans.get("from") == enemy.state:
                if enemy.state != trans.get("to"):
                    enemy.state = trans.get("to")
                    state.logs.append(f"💢 {enemy.name} 进入了 {enemy.state} 状态！")
                    changed = True
    if changed:
        update_enemy_intent(enemy)

# --- 效果处理器 (Strategy Pattern) ---

def handle_damage(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    src, tgt = get_actual_target(effect, source, target)
    value = effect.get("value", 0)
    actual_damage = max(0, value - tgt.shield)
    tgt.shield = max(0, tgt.shield - value)
    tgt.hp -= actual_damage
    state.logs.append(f"{src.name} 对 {tgt.name} 造成了 {value} 点伤害 (吸收 {value - actual_damage})")
    
    # 荆棘反弹
    if actual_damage > 0 and tgt.status.get("thorns", 0) > 0:
        thorn_dmg = tgt.status["thorns"]
        src.hp -= thorn_dmg
        state.logs.append(f"🌵 {tgt.name} 的荆棘反弹了 {thorn_dmg} 点伤害！")
        check_survival(src, state)
        if src.name != "勇者": check_monster_transitions(src, state) # 怪物受反伤可能转相
    
    check_survival(tgt, state)
    if tgt.name != "勇者": check_monster_transitions(tgt, state) # 怪物受直伤可能转相

def handle_damage_if_status(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    src, tgt = get_actual_target(effect, source, target)
    required_status = effect.get("status")
    if tgt.status.get(required_status, 0) > 0:
        value = effect.get("value", 0)
        state.logs.append(f"💥 联动：{tgt.name} 处于 {required_status} 状态，触发强化打击！")
        handle_damage({"value": value}, source, target, state)
    else:
        fallback = effect.get("fallback", 0)
        handle_damage({"value": fallback}, source, target, state)

def handle_defend(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    src, tgt = get_actual_target(effect, source, target)
    value = effect.get("value", 0)
    tgt.shield += value
    state.logs.append(f"{tgt.name} 获得 {value} 点护甲")

def handle_apply_status(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    src, tgt = get_actual_target(effect, source, target)
    status_name = effect.get("status")
    value = effect.get("value", 0)
    tgt.status[status_name] = tgt.status.get(status_name, 0) + value
    state.logs.append(f"✨ {tgt.name} 获得 {value} 层 {status_name}")

def handle_remove_status(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    src, tgt = get_actual_target(effect, source, target)
    status_name = effect.get("status")
    tgt.status[status_name] = 0
    state.logs.append(f"🧹 {tgt.name} 的 {status_name} 被清除")

def handle_draw_cards(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    value = effect.get("value", 1)
    state.pending_actions.append({"type": "draw", "value": value})

def handle_heal(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    src, tgt = get_actual_target(effect, source, target)
    value = effect.get("value", 0)
    heal = min(value, tgt.max_hp - tgt.hp)
    tgt.hp += heal
    state.logs.append(f"❤️ {tgt.name} 恢复了 {heal} 生命")

def handle_gain_energy(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    value = effect.get("value", 0)
    state.energy += value
    state.logs.append(f"⚡ 能量 +{value}")

def handle_break_shield(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    _, tgt = get_actual_target(effect, source, target)
    tgt.shield = 0
    state.logs.append(f"🔨 {tgt.name} 的护盾粉碎了！")

EFFECT_HANDLERS = {
    "damage": handle_damage,
    "damage_if_target_has_status": handle_damage_if_status,
    "defend": handle_defend,
    "apply_status": handle_apply_status,
    "remove_status": handle_remove_status,
    "draw_cards": handle_draw_cards,
    "heal": handle_heal,
    "gain_energy": handle_gain_energy,
    "break_shield": handle_break_shield,
}

def apply_effect(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    handler = EFFECT_HANDLERS.get(effect.get("type"))
    if handler: handler(effect, source, target, state)
    else: state.logs.append(f"❓ 未知效果: {effect.get('type')}")

def apply_status_effects(entity: Entity, state: GameState):
    """每回合状态结算"""
    poison = entity.status.get("poison", 0)
    if poison > 0:
        entity.hp -= poison
        entity.status["poison"] -= 1
        state.logs.append(f"🧪 {entity.name} 中毒损血 {poison}")
        check_survival(entity, state)
        if entity.name != "勇者": check_monster_transitions(entity, state) # 中毒损血也可能转相

# --- 敌人行动执行 ---

def enemy_act(enemy: Entity, player: Entity, state: GameState):
    # 行动前再次确认状态
    check_monster_transitions(enemy, state)
    
    states_cfg = enemy.actions.get("states", {})
    current_cfg = states_cfg.get(enemy.state)
    if not current_cfg: return

    state.logs.append(f"👹 {enemy.name} 执行：{enemy.intent}")
    for effect in current_cfg.get("effects", []):
        apply_effect(effect, enemy, player, state)
    
    check_survival(enemy, state)
    check_survival(player, state)

    # 循环状态转移
    if "next_state" in current_cfg:
        enemy.state = current_cfg["next_state"]
    
    # 预告下回合意图
    update_enemy_intent(enemy)

# --- 游戏管理器 ---

class GameManager:
    def __init__(self):
        self.cards_pool = self._load_json("cards.json")
        self.cards_dict = {c["id"]: c for c in self.cards_pool}
        self.enemies_data = self._load_json("enemies.json")
        self.levels_data = self._load_json("levels.json")
        self.card_instance_counter = 0
        self.state = self.init_game()

    def _load_json(self, filename):
        path = os.path.join(BASE_DIR, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        return []

    def init_deck(self):
        basic_deck = list(self.cards_dict.keys()) * 2
        random.shuffle(basic_deck)
        self.state.deck = basic_deck
        self.state.discard = []
        self.state.hand = []

    def init_game(self, level=1):
        if not self.levels_data: raise RuntimeError("levels.json 缺失")
        level_cfg = next((l for l in self.levels_data if l["level"] == level), self.levels_data[0])
        enemy_cfg = next((e for e in self.enemies_data if e["id"] == level_cfg["enemy_id"]), self.enemies_data[0])
        
        player = Entity(name="勇者", hp=50, max_hp=50)
        enemy = Entity(
            name=enemy_cfg["name"],
            hp=enemy_cfg["max_hp"],
            max_hp=enemy_cfg["max_hp"],
            state=enemy_cfg.get("initial_state", "NORMAL"),
            actions=enemy_cfg.get("actions", {})
        )
        update_enemy_intent(enemy)
        
        self.state = GameState(player=player, enemy=enemy, level=level, logs=[f"--- 第 {level} 关: {enemy.name} ---"])
        self.init_deck()
        self.draw_cards(5)
        return self.state

    def draw_cards(self, count: int):
        for _ in range(count):
            if not self.state.deck:
                if not self.state.discard: break
                self.state.deck = self.state.discard[:]
                random.shuffle(self.state.deck)
                self.state.discard = []
            card_id = self.state.deck.pop()
            card_data = self.cards_dict.get(card_id)
            if card_data:
                card = Card(**card_data)
                self.card_instance_counter += 1
                card.instance_id = self.card_instance_counter
                self.state.hand.append(card)

    def process_pending_actions(self):
        while self.state.pending_actions:
            act = self.state.pending_actions.pop(0)
            if act["type"] == "draw": self.draw_cards(act["value"])

    def play_card(self, instance_id: int):
        if self.state.current_state != "PLAYER_TURN": raise HTTPException(status_code=400, detail="不是玩家回合")
        card_idx = next((i for i, c in enumerate(self.state.hand) if c.instance_id == instance_id), -1)
        if card_idx == -1: raise HTTPException(status_code=404, detail="卡牌未找到")
        
        card = self.state.hand[card_idx]
        if self.state.energy < card.cost: raise HTTPException(status_code=400, detail="能量不足")

        self.state.energy -= card.cost
        played = self.state.hand.pop(card_idx)
        self.state.discard.append(played.id)
        self.state.logs.append(f"玩家打出了【{played.name}】")
        
        for effect in card.effects:
            apply_effect(effect, self.state.player, self.state.enemy, self.state)

        self.process_pending_actions()
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
        if self.state.current_state != "PLAYER_TURN": return
        for c in self.state.hand: self.state.discard.append(c.id)
        self.state.hand = []
        self.state.current_state = "ENEMY_TURN"
        self.state.logs.append(">>> 敌人回合开始")
        
        apply_status_effects(self.state.enemy, self.state)
        self.check_battle_end()
        
        if self.state.current_state == "ENEMY_TURN":
            enemy_act(self.state.enemy, self.state.player, self.state)
            self.process_pending_actions()
            self.check_battle_end()

        if self.state.current_state == "ENEMY_TURN":
            self.state.current_state = "PLAYER_TURN"
            self.state.turn += 1
            self.state.energy = self.state.max_energy
            self.state.player.shield = 0
            apply_status_effects(self.state.player, self.state)
            self.check_battle_end()
            
            if self.state.current_state == "PLAYER_TURN":
                self.draw_cards(5)
                self.state.logs.append(f"--- 第 {self.state.turn} 回合 ---")
                update_enemy_intent(self.state.enemy)

    def next_level(self):
        if self.state.current_state != "VICTORY": raise HTTPException(status_code=400, detail="未胜利")
        hp = self.state.player.hp
        self.state = self.init_game(self.state.level + 1)
        self.state.player.hp = hp

# --- API ---

manager = GameManager()

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f: return f.read()

@app.get("/api/game/status")
def get_status(): return manager.state

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
