from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import json
import os
import random

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARD_LIBRARY: Dict[str, Dict[str, Any]] = {}
STATUS_LABELS = {
    "poison": "中毒",
    "thorns": "荆棘",
    "curse": "灾厄",
}


class Entity(BaseModel):
    name: str
    hp: int
    max_hp: int
    shield: int = 0
    status: Dict[str, int] = Field(
        default_factory=lambda: {"poison": 0, "thorns": 0, "curse": 0}
    )
    state: str = "NORMAL"
    intent: str = ""
    actions: Dict[str, Any] = Field(default_factory=dict)


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
    deck: List[str] = Field(default_factory=list)
    hand: List[Card] = Field(default_factory=list)
    discard: List[str] = Field(default_factory=list)
    energy: int = 3
    max_energy: int = 3
    turn: int = 1
    level: int = 1
    current_state: str = "PLAYER_TURN"
    logs: List[str] = Field(default_factory=list)
    next_card_instance_id: int = 1
    run_completed: bool = False


def clamp_hp(entity: Entity):
    entity.hp = max(0, min(entity.hp, entity.max_hp))


def format_damage_log(source: Entity, target: Entity, amount: int, absorbed: int, actual: int):
    return (
        f"{source.name} 对 {target.name} 造成 {amount} 点伤害"
        f"（护甲吸收 {absorbed}，实际扣除 {actual}）"
    )


def resolve_effect_target(effect: Dict[str, Any], source: Entity, default_target: Entity, state: GameState):
    target_ref = effect.get("target", "opponent")
    if target_ref in {"self", "source"}:
        return source
    if target_ref == "player":
        return state.player
    if target_ref == "enemy":
        return state.enemy
    return default_target


def refresh_enemy_intent(enemy: Entity):
    states_cfg = enemy.actions.get("states", {})
    state_cfg = states_cfg.get(enemy.state, {})
    enemy.intent = state_cfg.get("intent", "未知意图")


def draw_cards_from_library(state: GameState, count: int):
    for _ in range(count):
        if not state.deck:
            if not state.discard:
                state.logs.append("⚠️ 没牌可抽了！")
                break
            state.logs.append("🔄 正在重新洗牌...")
            state.deck = state.discard[:]
            random.shuffle(state.deck)
            state.discard = []

        card_id = state.deck.pop()
        card_data = CARD_LIBRARY.get(card_id)
        if not card_data:
            state.logs.append(f"⚠️ 未找到卡牌配置：{card_id}")
            continue

        card_instance = Card(**card_data)
        card_instance.instance_id = state.next_card_instance_id
        state.next_card_instance_id += 1
        state.hand.append(card_instance)


def apply_damage(
    amount: int,
    source: Entity,
    target: Entity,
    state: GameState,
    *,
    ignore_thorns: bool = False,
    is_status_damage: bool = False,
):
    if amount <= 0:
        return 0

    absorbed = min(target.shield, amount)
    target.shield -= absorbed
    actual_damage = max(0, amount - absorbed)
    target.hp -= actual_damage
    clamp_hp(target)

    if is_status_damage:
        state.logs.append(
            f"{target.name} 受到 {amount} 点状态伤害（护甲吸收 {absorbed}，实际扣除 {actual_damage}）"
        )
    else:
        state.logs.append(format_damage_log(source, target, amount, absorbed, actual_damage))

    thorns = target.status.get("thorns", 0)
    if (
        actual_damage > 0
        and thorns > 0
        and not ignore_thorns
        and source is not target
    ):
        state.logs.append(f"{target.name} 的荆棘反弹 {thorns} 点伤害给 {source.name}")
        apply_damage(
            thorns,
            target,
            source,
            state,
            ignore_thorns=True,
            is_status_damage=True,
        )

    return actual_damage


def apply_effect(effect: Dict[str, Any], source: Entity, target: Entity, state: GameState):
    """统一效果分发系统。"""
    eff_type = effect.get("type")
    value = effect.get("value", 0)
    recipient = resolve_effect_target(effect, source, target, state)

    if eff_type == "damage":
        apply_damage(value, source, recipient, state)

    elif eff_type == "defend":
        recipient.shield += value
        state.logs.append(f"{recipient.name} 获得了 {value} 点护甲")

    elif eff_type == "apply_status":
        status_name = effect.get("status")
        if not status_name:
            return
        recipient.status[status_name] = recipient.status.get(status_name, 0) + value
        status_label = STATUS_LABELS.get(status_name, status_name)
        state.logs.append(f"{recipient.name} 获得了 {value} 层{status_label}")

    elif eff_type == "heal":
        before_hp = recipient.hp
        recipient.hp = min(recipient.max_hp, recipient.hp + value)
        healed = recipient.hp - before_hp
        state.logs.append(f"{recipient.name} 恢复了 {healed} 点生命")

    elif eff_type == "gain_energy":
        state.energy += value
        state.logs.append(f"{source.name} 获得了 {value} 点能量")

    elif eff_type == "draw_cards":
        draw_cards_from_library(state, value)
        state.logs.append(f"{source.name} 抽取了 {value} 张牌")

    elif eff_type == "damage_if_target_has_status":
        status_name = effect.get("status", "")
        fallback = effect.get("fallback", 0)
        damage_value = value if recipient.status.get(status_name, 0) > 0 else fallback
        if recipient.status.get(status_name, 0) > 0:
            state.logs.append(
                f"{recipient.name} 身上有 {STATUS_LABELS.get(status_name, status_name)}，触发额外伤害"
            )
        apply_damage(damage_value, source, recipient, state)

    # TODO: 支持 remove_status、exhaust、vulnerable、weak 等更多效果


def apply_status_effects(entity: Entity, state: GameState, *, owner: str, phase: str):
    """状态系统：根据时机结算持续效果。"""
    if phase != "TURN_START":
        return

    poison = entity.status.get("poison", 0)
    if poison > 0:
        entity.status["poison"] = max(0, poison - 1)
        state.logs.append(
            f"{entity.name} 的中毒发作：当前受到 {poison} 点伤害，中毒剩余 {entity.status['poison']} 层"
        )
        apply_damage(poison, entity, entity, state, ignore_thorns=True, is_status_damage=True)

    curse = entity.status.get("curse", 0)
    if curse > 0:
        state.logs.append(f"{entity.name} 的灾厄发作：受到 {curse} 点伤害")
        apply_damage(curse, entity, entity, state, ignore_thorns=True, is_status_damage=True)
        if owner == "player":
            energy_loss = min(state.energy, curse)
            state.energy -= energy_loss
            state.logs.append(f"灾厄使玩家损失了 {energy_loss} 点能量")

    # TODO: 为 thorns 增加更多触发时机，例如按击中次数结算


def check_transition_condition(condition: str, enemy: Entity, state: GameState):
    if condition == "hp_below_half":
        return enemy.hp <= enemy.max_hp / 2
    if condition == "player_below_half":
        return state.player.hp <= state.player.max_hp / 2
    return False


def evaluate_enemy_transitions(enemy: Entity, state: GameState):
    for transition in enemy.actions.get("transitions", []):
        from_state = transition.get("from", "ANY")
        if from_state not in {"ANY", enemy.state}:
            continue
        if check_transition_condition(transition.get("condition", ""), enemy, state):
            old_state = enemy.state
            enemy.state = transition.get("to", enemy.state)
            if old_state != enemy.state:
                state.logs.append(f"{enemy.name} 切换到状态：{enemy.state}")
            break


def enemy_act(enemy: Entity, player: Entity, state: GameState):
    """敌人行为系统：根据状态机执行一个动作。"""
    evaluate_enemy_transitions(enemy, state)

    states_cfg = enemy.actions.get("states", {})
    action_cfg = states_cfg.get(enemy.state)
    if not action_cfg:
        action_cfg = {
            "intent": "普通攻击",
            "effects": [{"type": "damage", "value": 6}],
            "next_state": enemy.state,
        }

    enemy.intent = action_cfg.get("intent", "普通攻击")
    state.logs.append(f"{enemy.name} 发动：{enemy.intent}")

    for effect in action_cfg.get("effects", []):
        apply_effect(effect, enemy, player, state)

    next_state = action_cfg.get("next_state")
    if next_state:
        enemy.state = next_state

    refresh_enemy_intent(enemy)


class GameManager:
    def __init__(self):
        self.cards_pool = self._load_json("cards.json")
        self.cards_dict = {card["id"]: card for card in self.cards_pool}
        self.enemies_data = self._load_json("enemies.json")
        self.levels_data = self._load_json("levels.json")

        if not self.levels_data:
            raise RuntimeError("CRITICAL: levels.json 无法加载或为空")
        if not self.enemies_data:
            raise RuntimeError("CRITICAL: enemies.json 无法加载或为空")
        if not self.cards_dict:
            raise RuntimeError("CRITICAL: cards.json 无法加载或为空")

        global CARD_LIBRARY
        CARD_LIBRARY = self.cards_dict

        self.state = self.init_game()

    def _load_json(self, filename: str):
        path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_level_config(self, level: int):
        return next((item for item in self.levels_data if item["level"] == level), None)

    def get_enemy_config(self, enemy_id: str):
        return next((item for item in self.enemies_data if item["id"] == enemy_id), None)

    def init_deck(self):
        """初始化演示牌组。"""
        basic_deck = (
            ["strike"] * 4
            + ["defend"] * 4
            + ["poison_stab"] * 2
            + ["guard_spike"]
            + ["tactical_insight"]
            + ["quick_patch"]
            + ["toxic_burst"]
            + ["battle_focus"]
            + ["curse_brand"]
            + ["heavy_slash"]
        )
        random.shuffle(basic_deck)
        self.state.deck = basic_deck
        self.state.discard = []
        self.state.hand = []
        self.state.next_card_instance_id = 1

    def init_game(self, level: int = 1, player_hp: Optional[int] = None):
        level_cfg = self.get_level_config(level)
        if not level_cfg:
            raise RuntimeError(f"未找到关卡配置：level={level}")

        enemy_cfg = self.get_enemy_config(level_cfg["enemy_id"])
        if not enemy_cfg:
            raise RuntimeError(f"未找到敌人配置：enemy_id={level_cfg['enemy_id']}")

        player = Entity(name="勇者", hp=50, max_hp=50)
        if player_hp is not None:
            player.hp = min(player.max_hp, player_hp)

        enemy = Entity(
            name=enemy_cfg["name"],
            hp=enemy_cfg["max_hp"],
            max_hp=enemy_cfg["max_hp"],
            state=enemy_cfg.get("initial_state", "NORMAL"),
            actions=enemy_cfg.get("actions", {}),
        )
        refresh_enemy_intent(enemy)

        self.state = GameState(
            player=player,
            enemy=enemy,
            level=level,
            logs=[f"--- 第 {level} 关：{enemy.name} 出现了！ ---"],
        )
        self.init_deck()
        self.draw_cards(5)
        return self.state

    def draw_cards(self, count: int):
        draw_cards_from_library(self.state, count)

    def start_player_turn(self):
        self.state.current_state = "PLAYER_TURN"
        self.state.turn += 1
        self.state.energy = self.state.max_energy
        self.state.player.shield = 0
        self.state.logs.append(f"--- 第 {self.state.turn} 回合 ---")

        apply_status_effects(self.state.player, self.state, owner="player", phase="TURN_START")
        self.check_battle_end()
        if self.state.current_state != "PLAYER_TURN":
            return

        self.draw_cards(5)
        refresh_enemy_intent(self.state.enemy)

    def play_card(self, instance_id: int):
        if self.state.current_state != "PLAYER_TURN":
            raise HTTPException(status_code=400, detail="不是玩家的回合")

        card_idx = next(
            (index for index, card in enumerate(self.state.hand) if card.instance_id == instance_id),
            -1,
        )
        if card_idx == -1:
            raise HTTPException(status_code=404, detail="卡牌未找到")

        card = self.state.hand[card_idx]
        if self.state.energy < card.cost:
            raise HTTPException(status_code=400, detail="能量不足")

        self.state.energy -= card.cost
        played_card = self.state.hand.pop(card_idx)
        self.state.discard.append(played_card.id)
        self.state.logs.append(f"玩家打出了【{played_card.name}】")

        for effect in card.effects:
            apply_effect(effect, self.state.player, self.state.enemy, self.state)

        self.check_battle_end()

    def check_battle_end(self):
        if self.state.enemy.hp <= 0:
            self.state.enemy.hp = 0
            self.state.current_state = "VICTORY"
            self.state.logs.append("战斗胜利！")
            if not self.get_level_config(self.state.level + 1):
                self.state.run_completed = True
                self.state.logs.append("🏆 你击败了所有敌人，本次爬塔完成！")
            return

        if self.state.player.hp <= 0:
            self.state.player.hp = 0
            self.state.current_state = "GAME_OVER"
            self.state.logs.append("你被击败了...")

    def end_turn(self):
        if self.state.current_state != "PLAYER_TURN":
            raise HTTPException(status_code=400, detail="当前不能结束回合")

        for card in self.state.hand:
            self.state.discard.append(card.id)
        self.state.hand = []

        self.state.current_state = "ENEMY_TURN"
        self.state.logs.append(">>> 敌人回合开始")

        apply_status_effects(self.state.enemy, self.state, owner="enemy", phase="TURN_START")
        self.check_battle_end()

        if self.state.current_state == "ENEMY_TURN":
            enemy_act(self.state.enemy, self.state.player, self.state)
            self.check_battle_end()

        if self.state.current_state == "ENEMY_TURN":
            self.start_player_turn()

    def next_level(self):
        if self.state.current_state != "VICTORY":
            raise HTTPException(status_code=400, detail="未获得胜利，无法进入下一关")
        if self.state.run_completed:
            raise HTTPException(status_code=400, detail="已经通关，没有下一关了")

        next_lvl = self.state.level + 1
        current_hp = self.state.player.hp
        self.state = self.init_game(next_lvl, player_hp=current_hp)


manager = GameManager()


@app.get("/", response_class=HTMLResponse)
def get_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as file:
        return file.read()


@app.get("/api/game/status")
def get_status():
    refresh_enemy_intent(manager.state.enemy)
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
