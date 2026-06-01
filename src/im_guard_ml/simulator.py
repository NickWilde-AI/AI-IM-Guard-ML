"""数据模拟器：模拟 IM 后端持续发送审核请求到 /judge 接口。

启动方式:
    python -m im_guard_ml.simulator --interval 1 --port 8000

模拟逻辑:
    - 时间感知：凌晨低谷(0.3x)、午间平稳(1x)、晚高峰(2-3x)
    - 突发事件：随机触发"代刷团伙集中作案"或"引流批量投放"
    - 话术多样：每条消息带随机变体（错别字、谐音、缩写）
    - 用户画像：注册天数、历史违规次数、设备类型等
    - 多轮对话：部分案例包含 2-4 条聊天记录
"""
from __future__ import annotations

import argparse
import math
import random
import time
from datetime import datetime

import httpx

# ===== 话术模板库 =====

# 安全对话（50+ 条，覆盖日常社交各场景）
SAFE_CHATS = [
    # 日常问候
    "你最近在忙什么呀？周末有空一起开黑吗？",
    "今天心情怎么样？看你动态说加班了",
    "早啊，昨晚睡得好吗",
    "好久没聊了，最近还好吗",
    "在吗？想问你个事",
    # 直播相关
    "今天直播唱的那首歌好好听，叫什么名字？",
    "明天几点开播呀？我准时来看",
    "你声音好好听，能唱首周杰伦的歌吗",
    "刚下班好累，来看你直播放松一下",
    "你直播间的氛围真好，大家都很友善",
    "昨天那个连麦的人好搞笑哈哈",
    "你今天穿的衣服好好看",
    "能不能唱一下那个《晴天》",
    "你开播我每次都来，加个粉丝团呗",
    # 游戏互动
    "你推荐的那个游戏我下了，确实好玩",
    "一起打排位吗？我段位掉了好多",
    "你那个皮肤怎么获得的？好帅",
    "今晚有空吗，组队打团",
    "你操作好厉害，带带我呗",
    # 生活闲聊
    "生日快乐！送你个小礼物",
    "最近天气好热，注意防暑啊",
    "你的猫好可爱，是什么品种？",
    "哈哈哈你说话太搞笑了，笑死我了",
    "推荐个好吃的外卖呗",
    "你那边下雨了吗？我这边暴雨",
    "周末要不要一起看电影",
    "你健身多久了？效果好明显",
    "最近在追什么剧？推荐一下",
    "你头像好好看，在哪拍的",
    # 粉丝互动
    "关注你好久了，终于鼓起勇气私聊",
    "你上次推荐的书我看完了，很好看",
    "今天的直播内容太有意思了",
    "能加个粉丝群吗？想认识其他粉丝",
    "你的声音好治愈，每天听着睡觉",
    "支持你！继续加油",
    "什么时候出新内容呀，期待",
    "你和上次那个连麦好有默契",
]

# 代刷/包榜（含变体、谐音、缩写）
BRUSH_CHATS = [
    "帮我代刷一下今晚的周榜，包榜到第一。",
    "老规矩，这次冲月榜前三，价格私聊。",
    "上次帮你刷的那个主播，这次还要继续吗？",
    "包榜费用怎么算？我要冲日榜第一。",
    "帮我把这个主播顶上去，预算两万。",
    "dai刷一下今晚的榜，保第一，价格好说",
    "冲bang费用多少？我要日ban前三",
    "兄弟，帮忙冲一下周榜，全包，钱不是问题",
    "上次那个事还能搞吗？这次目标月榜",
    "我出钱你出号，把她顶上去，三七分",
    "有没有资源帮我包一下今晚的榜单？要稳的",
    "找你帮忙刷一下，上次效果很好，继续合作",
    "能不能安排几个号帮我冲？预算五万以内",
    "这次搞大的，包周榜前三，多少钱你说",
    "帮我顶一下对面那个主播，让她掉出前五",
]

# 诈骗引流（含变体、谐音）
FRAUD_CHATS = [
    "加我私V，发你一个稳赚的项目，本金500起。",
    "加微信 xxx888，带你日入过千，零风险。",
    "私聊我，有个好项目介绍给你，保本保息。",
    "想赚钱吗？加我外部联系方式，带你上车。",
    "我这边有个投资渠道，回报率很高，感兴趣私我。",
    "加V: money666，每天稳定收入，不用你操心",
    "有个兼zhi的活，日结200-500，想做吗",
    "我朋友在做一个pj，收益很可观，了解一下？",
    "扫码加我，带你了解一个稳赚不赔的路子",
    "最近发现一个漏dong，稳定出jin，私我详聊",
    "你听说过XX平台吗？我在上面赚了不少，带你",
    "加我v信详聊，有个躺赚的事情跟你说",
    "兄弟想不想搞点外快？无风险那种",
    "我有个渠道可以低价充值，需要的私我",
    "帮你开通一个VIP渠道，半价，感兴趣吗",
]

# 私下交易
TRADE_CHATS = [
    "私下转账给我吧，平台抽成太高了。",
    "加我微信转账，给你打八折。",
    "别在平台充了，直接转我支付宝，便宜很多。",
    "我给你个收款码，走外部比较划算。",
    "走平台太贵了，你直接转给我，我给你发货",
    "咱们私下交易吧，省下手续费对半分",
    "加我V转钱，平台扣的太狠了",
    "你在app里充值不划算，我这里有折扣渠道",
    "直接发红包给我就行，不用走平台了",
    "我给你个链接，从那边下单便宜一半",
]

# 赌博引流
GAMBLE_CHATS = [
    "有个棋牌平台很赚钱，要不要一起玩？",
    "我在一个平台押注，赢了不少，带你。",
    "加群看走势图，跟着买稳赚不赔。",
    "兄弟玩不玩？昨天赢了三千多",
    "有个pg平台，充100送100，老稳了",
    "来我群里看分析师的计划，命中率90%以上",
    "那个BC平台还在搞活动，冲一波？",
    "有个jc群，每天跟单就行，上周赚了一万",
]

# 色情引流
PORN_CHATS = [
    "想看pian吗？加我另一个号",
    "有兴趣看那种视频吗？私密的那种",
    "加我telegram，有好东西分享",
    "想找小jj聊天吗？加我推荐",
    "有需要的私我，各种资源都有",
]

# 灰区 / 边界案例（看起来像违规但其实正常，或看起来正常但可能有风险）
GRAY_ZONE_CHATS = [
    "我在淘宝开了个店，有空来逛逛",  # 可能引流但也可能是正常分享
    "上次说的那个事，咱们见面再聊",  # 含糊
    "你那个号还在用吗？能不能借我一下",  # 账号借用
    "我朋友想找人帮忙运营账号，有兴趣吗",
    "帮我点个赞呗，互帮互助",
    "你那个优惠券还有吗？能不能分享一下",
    "这个链接你看一下，是我做的小程序",
    "咱们换个地方聊吧，这里不方便",
]

# ===== 行为异常模板库 =====
ABNORMAL_TEMPLATES = {
    "brush": [
        {"abnormal_type": "代刷/包榜行为", "abnormal_description": "30分钟内对目标主播突发性大额打赏{amount}元。"},
        {"abnormal_type": "代刷/包榜行为", "abnormal_description": "连续{days}天对同一主播固定时段打赏，疑似合同式包榜。"},
        {"abnormal_type": "异常打赏模式", "abnormal_description": "打赏间隔极短(平均{sec}秒/笔)，疑似脚本操作。"},
    ],
    "fraud": [
        {"abnormal_type": "批量投放", "abnormal_description": "10分钟内向{count}个不同主播账号私聊同一话术。"},
        {"abnormal_type": "批量投放", "abnormal_description": "24小时内向{count}个新用户发送相似消息，疑似批量引流。"},
        {"abnormal_type": "外部链接分发", "abnormal_description": "消息中包含外部链接/二维码，已向{count}人发送。"},
    ],
    "trade": [
        {"abnormal_type": "私下交易引导", "abnormal_description": "引导用户跳转外部支付渠道，涉及金额约{amount}元。"},
        {"abnormal_type": "绕过平台支付", "abnormal_description": "多次提及外部转账方式，历史{count}次类似行为。"},
    ],
    "gamble": [
        {"abnormal_type": "赌博引流", "abnormal_description": "发送疑似赌博平台链接，近7天向{count}人投递。"},
        {"abnormal_type": "赌博引流", "abnormal_description": "消息中包含赌博相关关键词(走势/押注/下注)，触发{count}次。"},
    ],
    "porn": [
        {"abnormal_type": "色情引流", "abnormal_description": "发送疑似色情内容引导，涉及外部平台跳转。"},
        {"abnormal_type": "色情引流", "abnormal_description": "私聊中发送疑似不雅图片/视频链接，已向{count}人发送。"},
    ],
}

# ===== 用户画像模板 =====
DEVICE_TYPES = ["iOS 17.4", "Android 14", "iOS 16.2", "Android 13", "HarmonyOS 4"]
REGIONS = ["广东", "浙江", "北京", "上海", "四川", "江苏", "福建", "湖北", "河南", "山东"]


def _time_factor() -> float:
    """基于当前小时返回请求频率因子，模拟真实流量曲线。

    凌晨 2-6 点: 0.2-0.4x (低谷)
    上午 9-12 点: 0.8-1.0x (平稳)
    下午 14-17 点: 0.9-1.1x (平稳)
    晚上 19-23 点: 1.5-3.0x (高峰)
    """
    hour = datetime.now().hour
    # 用正弦曲线模拟一天内的流量变化，高峰在 21 点
    base = 0.5 + 0.5 * math.sin((hour - 6) / 24 * 2 * math.pi)
    # 晚高峰额外加成
    if 19 <= hour <= 23:
        base *= 1.8
    elif 0 <= hour <= 5:
        base *= 0.4
    return max(base, 0.2)


class EventSimulator:
    """突发事件模拟器。

    随机触发短时间内违规率飙升的事件，模拟：
    - 代刷团伙集中上线
    - 引流机器人批量投放
    - 新型话术爆发
    """

    def __init__(self):
        self.active_event: str | None = None
        self.event_remaining: int = 0
        self.event_cooldown: int = 0  # 冷却计数，避免事件太频繁

    def tick(self) -> str | None:
        """每次请求调用，返回当前活跃事件类型或 None。"""
        if self.event_remaining > 0:
            self.event_remaining -= 1
            if self.event_remaining == 0:
                event = self.active_event
                self.active_event = None
                self.event_cooldown = random.randint(30, 80)
                return event  # 最后一条还是事件
            return self.active_event

        if self.event_cooldown > 0:
            self.event_cooldown -= 1
            return None

        # 2% 概率触发突发事件
        if random.random() < 0.02:
            self.active_event = random.choice(["brush_raid", "fraud_wave", "porn_burst"])
            self.event_remaining = random.randint(8, 20)
            return self.active_event

        return None


def _build_user_profile() -> dict:
    """生成随机用户画像。"""
    reg_days = random.choices(
        [random.randint(0, 3), random.randint(4, 30), random.randint(31, 365), random.randint(366, 1500)],
        weights=[15, 25, 40, 20],
    )[0]
    return {
        "user_id": f"U{random.randint(100000000, 999999999)}",
        "register_days": reg_days,
        "history_violations": random.choices([0, 1, 2, random.randint(3, 8)], weights=[70, 15, 10, 5])[0],
        "device_type": random.choice(DEVICE_TYPES),
        "region": random.choice(REGIONS),
        "level": random.randint(1, 60),
    }


def _fill_abnormal(template: dict) -> dict:
    """填充异常模板中的占位符。"""
    desc = template["abnormal_description"]
    desc = desc.replace("{amount}", str(random.choice([3000, 5000, 8000, 10000, 15000, 20000, 30000])))
    desc = desc.replace("{count}", str(random.randint(4, 30)))
    desc = desc.replace("{days}", str(random.randint(3, 14)))
    desc = desc.replace("{sec}", str(random.randint(2, 8)))
    return {"abnormal_type": template["abnormal_type"], "abnormal_description": desc}


def _multi_round_chat(primary: str, category: str) -> list[dict]:
    """生成多轮对话证据（1-3 条）。"""
    evidence = [
        {
            "occur_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "original_content": primary,
            "risk_point": "存在违规关键词。" if category != "safe" else "无明显风险词。",
        }
    ]
    # 30% 概率有第二条回复
    if random.random() < 0.3 and category != "safe":
        replies = {
            "brush": ["好的，老价格，包你满意。", "没问题，今晚给你安排。", "行，这次冲前三保底。"],
            "fraud": ["好的加了，什么项目？", "真的假的？靠谱吗", "行，我看看怎么回事"],
            "trade": ["好，那你发收款码吧", "行，支付宝还是微信？", "了解，那走外部吧"],
            "gamble": ["听起来不错，怎么玩？", "赢了怎么提现？", "行，你拉我进群"],
            "porn": ["什么资源？", "私密的？", "加了"],
        }
        if category in replies:
            reply = random.choice(replies[category])
            evidence.append({
                "occur_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "original_content": reply,
                "risk_point": "回复确认违规意图。" if category != "safe" else "",
            })
    return evidence


def generate_case(event: str | None = None) -> dict:
    """根据概率分布和当前事件生成一条模拟审核工单。"""

    # 事件期间强制覆盖分布
    if event == "brush_raid":
        category = "brush" if random.random() < 0.7 else "safe"
    elif event == "fraud_wave":
        category = "fraud" if random.random() < 0.6 else "safe"
    elif event == "porn_burst":
        category = "porn" if random.random() < 0.5 else "safe"
    else:
        # 正常分布
        r = random.random()
        if r < 0.78:
            category = "safe"
        elif r < 0.88:
            category = "brush"
        elif r < 0.93:
            category = "fraud"
        elif r < 0.96:
            category = "trade"
        elif r < 0.98:
            category = "gamble"
        elif r < 0.99:
            category = "porn"
        else:
            category = "gray"

    # 选择话术
    chat_map = {
        "safe": SAFE_CHATS,
        "brush": BRUSH_CHATS,
        "fraud": FRAUD_CHATS,
        "trade": TRADE_CHATS,
        "gamble": GAMBLE_CHATS,
        "porn": PORN_CHATS,
        "gray": GRAY_ZONE_CHATS,
    }
    chat = random.choice(chat_map[category])

    # 用户画像
    profile = _build_user_profile()
    # 违规用户画像偏向：新号、有历史违规
    if category not in ("safe", "gray"):
        if random.random() < 0.4:
            profile["register_days"] = random.randint(0, 7)
        if random.random() < 0.3:
            profile["history_violations"] = random.randint(1, 5)

    # 礼物金额
    if category == "brush":
        gift_value = random.choices(
            [random.randint(5000, 10000), random.randint(10000, 30000), random.randint(30000, 80000)],
            weights=[40, 40, 20],
        )[0]
    elif category == "trade":
        gift_value = random.randint(500, 5000)
    elif category == "safe":
        gift_value = random.choices(
            [0, random.randint(1, 100), random.randint(100, 500), random.randint(500, 2000)],
            weights=[40, 30, 20, 10],
        )[0]
    else:
        gift_value = random.randint(0, 200)

    # 亲密度
    intimacy_map = {
        "safe": random.choice(["高", "中", "低", "中", "高"]),
        "brush": random.choice(["无", "低", "无"]),
        "fraud": "无",
        "trade": random.choice(["中", "低"]),
        "gamble": "无",
        "porn": "无",
        "gray": random.choice(["中", "低", "无"]),
    }
    intimacy = intimacy_map[category]

    # 登录行为
    login = "异地登录。" if category in ("fraud", "gamble", "porn") or (category == "brush" and random.random() < 0.6) else "本机登录。"

    # 行为异常
    abnormals = []
    if category in ABNORMAL_TEMPLATES:
        tmpl = random.choice(ABNORMAL_TEMPLATES[category])
        abnormals = [_fill_abnormal(tmpl)]
        # 20% 概率有第二条异常
        if random.random() < 0.2 and len(ABNORMAL_TEMPLATES[category]) > 1:
            tmpl2 = random.choice([t for t in ABNORMAL_TEMPLATES[category] if t != tmpl])
            abnormals.append(_fill_abnormal(tmpl2))

    # 聊天证据（多轮）
    evidence = _multi_round_chat(chat, category)

    ticket_id = f"im-audit-{time.strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"

    return {
        "ticket_id": ticket_id,
        "audit_scene": {
            "chat_type": "IM私聊",
            "user_intimacy": intimacy,
            "user_profile": profile,
            "behavior_key_summary": {
                "login_behavior": login,
                "search_behavior": "搜索UID。" if category in ("fraud", "brush") else "无搜索行为。",
                "follow_behavior": random.choice(["互关。", "单向关注。", "无关注。"]),
                "enter_room_behavior": random.choice(["近30日频繁进房。", "偶尔进房。", "首次进房。", "短时间内连续进入多个房间。"]),
                "mic_interact_behavior": random.choice(["无互动。", "偶尔连麦。", "频繁连麦。"]),
                "t_bean_consume": "极大额消费。" if gift_value > 10000 else "大额消费。" if gift_value > 5000 else "中等额度消费。" if gift_value > 500 else "少量消费。" if gift_value > 0 else "无消费。",
                "reward_behavior": "持续高频大额打赏，旨在推高榜单。" if gift_value > 10000 else "大额打赏。" if gift_value > 5000 else "礼物记录稳定，无突发尖峰。" if gift_value > 0 else "无礼物记录。",
                "gift_total_value": gift_value,
                "gift_total_count": max(1, gift_value // random.randint(500, 3000)) if gift_value > 0 else 0,
            },
        },
        "chat_evidence_list": evidence,
        "behavior_abnormal_list": abnormals,
    }


def run_simulator(host: str = "127.0.0.1", port: int = 8000, interval: float = 1.0):
    """持续向审核服务发送模拟请求，带时间波动和突发事件。"""
    url = f"http://{host}:{port}/judge"
    event_sim = EventSimulator()

    print(f"╔══════════════════════════════════════════╗")
    print(f"║   IM Guard 数据模拟器 v2.0               ║")
    print(f"╠══════════════════════════════════════════╣")
    print(f"║  目标: {url:<32} ║")
    print(f"║  基础间隔: {interval:.1f}s (带时间波动)            ║")
    print(f"║  突发事件: 随机触发                       ║")
    print(f"╚══════════════════════════════════════════╝")
    print()
    print("按 Ctrl+C 停止")
    print("-" * 60)

    count = 0
    with httpx.Client(timeout=10.0) as client:
        while True:
            event = event_sim.tick()
            case = generate_case(event)
            try:
                resp = client.post(url, json=case)
                resp.raise_for_status()
                result = resp.json()
                count += 1

                risk = result.get("risk_level", "?")
                topic = result.get("topic", "?")
                action = result.get("handling_suggestion", "?")
                route = result.get("route", "?")

                # 彩色输出
                risk_icon = {"high_risk": "🔴", "mid_risk": "🟡", "low_risk": "🟢"}.get(risk, "⚪")
                event_tag = f" ⚡{event}" if event else ""

                print(
                    f"[{count:04d}] {risk_icon} {case['ticket_id'][-15:]} │ "
                    f"{risk:<10} {topic:<10} {action:<14} {route}{event_tag}"
                )
            except httpx.HTTPError as e:
                print(f"[错误] 请求失败: {e}")
            except KeyboardInterrupt:
                break

            # 动态间隔 = 基础间隔 / 时间因子 + 随机抖动
            factor = _time_factor()
            jitter = random.uniform(-0.3, 0.3)
            actual_interval = max(0.2, (interval / factor) + jitter)
            time.sleep(actual_interval)

    print(f"\n{'='*60}")
    print(f"模拟器停止 | 共发送 {count} 条请求")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="IM Guard 数据模拟器 v2.0")
    parser.add_argument("--host", default="127.0.0.1", help="服务地址")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--interval", type=float, default=1.0, help="基础间隔(秒)，实际会受时间波动影响")
    args = parser.parse_args()
    run_simulator(args.host, args.port, args.interval)


if __name__ == "__main__":
    main()
