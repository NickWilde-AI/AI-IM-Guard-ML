"""数据模拟器：模拟 IM 后端持续发送审核请求到 /judge 接口。

启动方式:
    python -m im_guard_ml.simulator --interval 2 --port 8000

模拟逻辑:
    - 80% 概率生成安全对话
    - 10% 概率生成代刷/包榜
    - 5% 概率生成诈骗引流
    - 3% 概率生成私下交易
    - 2% 概率生成赌博引流
"""
from __future__ import annotations

import argparse
import random
import time

import httpx

# 安全对话模板
SAFE_CHATS = [
    "你最近在忙什么呀？周末有空一起开黑吗？",
    "今天直播唱的那首歌好好听，叫什么名字？",
    "哈哈哈你说话太搞笑了，笑死我了",
    "明天几点开播呀？我准时来看",
    "你推荐的那个游戏我下了，确实好玩",
    "生日快乐！送你个小礼物",
    "最近天气好热，注意防暑啊",
    "你的猫好可爱，是什么品种？",
    "刚下班好累，来看你直播放松一下",
    "你声音好好听，能唱首周杰伦的歌吗？",
    "今天心情不好，来你直播间待会儿",
    "你直播间的氛围真好，大家都很友善",
]

# 代刷/包榜模板
BRUSH_CHATS = [
    "帮我代刷一下今晚的周榜，包榜到第一。",
    "老规矩，这次冲月榜前三，价格私聊。",
    "上次帮你刷的那个主播，这次还要继续吗？",
    "包榜费用怎么算？我要冲日榜第一。",
    "帮我把这个主播顶上去，预算两万。",
]

# 诈骗引流模板
FRAUD_CHATS = [
    "加我私V，发你一个稳赚的项目，本金500起。",
    "加微信 xxx888，带你日入过千，零风险。",
    "私聊我，有个好项目介绍给你，保本保息。",
    "想赚钱吗？加我外部联系方式，带你上车。",
    "我这边有个投资渠道，回报率很高，感兴趣私我。",
]

# 私下交易模板
TRADE_CHATS = [
    "私下转账给我吧，平台抽成太高了。",
    "加我微信转账，给你打八折。",
    "别在平台充了，直接转我支付宝，便宜很多。",
    "我给你个收款码，走外部比较划算。",
]

# 赌博引流模板
GAMBLE_CHATS = [
    "有个棋牌平台很赚钱，要不要一起玩？",
    "我在一个平台押注，赢了不少，带你。",
    "加群看走势图，跟着买稳赚不赔。",
]

ABNORMAL_TYPES = {
    "brush": {"abnormal_type": "代刷/包榜行为", "abnormal_description": "30分钟内对目标主播突发性大额打赏"},
    "fraud": {"abnormal_type": "批量投放", "abnormal_description": "10分钟内向多个主播账号私聊同一话术"},
    "trade": {"abnormal_type": "私下交易引导", "abnormal_description": "引导用户跳转外部支付渠道"},
    "gamble": {"abnormal_type": "赌博引流", "abnormal_description": "发送疑似赌博平台链接或邀请"},
}


def generate_case() -> dict:
    """根据概率分布生成一条模拟审核工单。"""
    r = random.random()

    if r < 0.80:
        # 安全对话
        chat = random.choice(SAFE_CHATS)
        gift_value = random.randint(0, 500)
        abnormals = []
        intimacy = random.choice(["高", "中", "低"])
        login = "本机登录。"
    elif r < 0.90:
        # 代刷/包榜
        chat = random.choice(BRUSH_CHATS)
        gift_value = random.randint(5000, 30000)
        abnormals = [ABNORMAL_TYPES["brush"]]
        intimacy = "无"
        login = "异地登录。"
    elif r < 0.95:
        # 诈骗引流
        chat = random.choice(FRAUD_CHATS)
        gift_value = 0
        abnormals = [ABNORMAL_TYPES["fraud"]]
        intimacy = "无"
        login = "异地登录。"
    elif r < 0.98:
        # 私下交易
        chat = random.choice(TRADE_CHATS)
        gift_value = random.randint(1000, 5000)
        abnormals = [ABNORMAL_TYPES["trade"]]
        intimacy = random.choice(["中", "低"])
        login = "本机登录。"
    else:
        # 赌博引流
        chat = random.choice(GAMBLE_CHATS)
        gift_value = 0
        abnormals = [ABNORMAL_TYPES["gamble"]]
        intimacy = "无"
        login = "异地登录。"

    ticket_id = f"im-audit-{time.strftime('%Y%m%d')}-{random.randint(100000, 999999)}"

    return {
        "ticket_id": ticket_id,
        "audit_scene": {
            "chat_type": "IM私聊",
            "user_intimacy": intimacy,
            "behavior_key_summary": {
                "login_behavior": login,
                "follow_behavior": random.choice(["互关。", "单向关注。", "无关注。"]),
                "enter_room_behavior": random.choice(["近30日频繁进房。", "偶尔进房。", "首次进房。"]),
                "t_bean_consume": "极大额消费。" if gift_value > 5000 else "中等额度消费。" if gift_value > 500 else "少量消费。",
                "reward_behavior": "持续高频大额打赏，旨在推高榜单。" if gift_value > 5000 else "礼物记录稳定。",
                "gift_total_value": gift_value,
                "gift_total_count": random.randint(1, 20),
            },
        },
        "chat_evidence_list": [
            {
                "occur_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "original_content": chat,
                "risk_point": "无明显风险词。" if r < 0.80 else "存在违规关键词。",
            }
        ],
        "behavior_abnormal_list": abnormals,
    }


def run_simulator(host: str = "127.0.0.1", port: int = 8000, interval: float = 2.0):
    """持续向审核服务发送模拟请求。"""
    url = f"http://{host}:{port}/judge"
    print(f"模拟器启动，目标: {url}，间隔: {interval}秒")
    print("按 Ctrl+C 停止\n")

    count = 0
    with httpx.Client(timeout=10.0) as client:
        while True:
            case = generate_case()
            try:
                resp = client.post(url, json=case)
                resp.raise_for_status()
                result = resp.json()
                count += 1
                risk = result.get("risk_level", "?")
                topic = result.get("topic", "?")
                action = result.get("handling_suggestion", "?")
                route = result.get("route", "?")
                print(
                    f"[{count:04d}] {case['ticket_id']} | "
                    f"风险:{risk:<10} 主题:{topic:<10} "
                    f"处置:{action:<14} 路由:{route}"
                )
            except httpx.HTTPError as e:
                print(f"[错误] 请求失败: {e}")
            except KeyboardInterrupt:
                break

            time.sleep(interval + random.uniform(-0.5, 0.5))

    print(f"\n模拟器停止，共发送 {count} 条请求。")


def main():
    parser = argparse.ArgumentParser(description="IM审核数据模拟器")
    parser.add_argument("--host", default="127.0.0.1", help="服务地址")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--interval", type=float, default=2.0, help="发送间隔(秒)")
    args = parser.parse_args()
    run_simulator(args.host, args.port, args.interval)


if __name__ == "__main__":
    main()
