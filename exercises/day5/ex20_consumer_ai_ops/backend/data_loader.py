"""
Data generation & loading for Consumer AI Ops Platform.
Generates realistic consumer-retail data: sales, customers, products, reviews, FAQ.
"""

import json
import random
import math
from pathlib import Path
from datetime import datetime, timedelta

from config import DATA_DIR

random.seed(42)

# ═══════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════

REGIONS = ["华东", "华南", "华北", "西南", "华中"]
CATEGORIES = ["食品饮料", "美妆个护", "家居日用", "数码家电", "服饰鞋包", "母婴用品", "运动户外", "宠物用品"]
CHANNELS = ["线上直营", "线上分销", "线下门店"]
MEMBER_LEVELS = ["普通", "银卡", "金卡", "黑卡"]
GENDERS = ["男", "女"]
SEGMENTS = ["高价值活跃", "高价值沉睡", "中价值成长", "中价值稳定", "低价值潜力", "低价值流失"]

PRODUCTS = [
    {"id": "P001", "name": "鲜萃拿铁咖啡24罐装", "category": "食品饮料", "price": 89.9, "cost": 42},
    {"id": "P002", "name": "有机燕麦奶1L装", "category": "食品饮料", "price": 29.9, "cost": 14},
    {"id": "P003", "name": "坚果混合礼盒1kg", "category": "食品饮料", "price": 128, "cost": 58},
    {"id": "P004", "name": "玻尿酸保湿精华30ml", "category": "美妆个护", "price": 199, "cost": 42},
    {"id": "P005", "name": "烟酰胺亮肤面膜10片", "category": "美妆个护", "price": 69.9, "cost": 18},
    {"id": "P006", "name": "防晒喷雾SPF50+ 150ml", "category": "美妆个护", "price": 89, "cost": 28},
    {"id": "P007", "name": "日本进口洗衣凝珠30颗", "category": "家居日用", "price": 39.9, "cost": 16},
    {"id": "P008", "name": "竹纤维毛巾套装3条", "category": "家居日用", "price": 49.9, "cost": 18},
    {"id": "P009", "name": "智能扫地机器人Pro", "category": "数码家电", "price": 2499, "cost": 1200},
    {"id": "P010", "name": "蓝牙降噪耳机", "category": "数码家电", "price": 399, "cost": 145},
    {"id": "P011", "name": "智能手表运动版", "category": "数码家电", "price": 899, "cost": 380},
    {"id": "P012", "name": "真丝衬衫女士款", "category": "服饰鞋包", "price": 359, "cost": 120},
    {"id": "P013", "name": "运动休闲双肩包", "category": "服饰鞋包", "price": 199, "cost": 68},
    {"id": "P014", "name": "牛皮通勤手提包", "category": "服饰鞋包", "price": 599, "cost": 195},
    {"id": "P015", "name": "婴儿纸尿裤L号72片", "category": "母婴用品", "price": 139, "cost": 62},
    {"id": "P016", "name": "儿童益生菌固体饮料", "category": "母婴用品", "price": 89, "cost": 32},
    {"id": "P017", "name": "婴儿润肤霜200ml", "category": "母婴用品", "price": 69.9, "cost": 22},
    {"id": "P018", "name": "瑜伽垫加厚防滑款", "category": "运动户外", "price": 129, "cost": 38},
    {"id": "P019", "name": "碳纤维登山杖一对", "category": "运动户外", "price": 269, "cost": 88},
    {"id": "P020", "name": "速干运动T恤", "category": "运动户外", "price": 99, "cost": 32},
    {"id": "P021", "name": "猫粮成猫通用5kg", "category": "宠物用品", "price": 159, "cost": 58},
    {"id": "P022", "name": "狗零食鸡肉干500g", "category": "宠物用品", "price": 49.9, "cost": 18},
    {"id": "P023", "name": "自动喂食器WiFi版", "category": "宠物用品", "price": 299, "cost": 98},
    {"id": "P024", "name": "气泡水机家用版", "category": "食品饮料", "price": 399, "cost": 148},
    {"id": "P025", "name": "抗老精华霜50ml", "category": "美妆个护", "price": 329, "cost": 78},
    {"id": "P026", "name": "空气净化器除甲醛款", "category": "家居日用", "price": 1299, "cost": 520},
    {"id": "P027", "name": "便携投影仪", "category": "数码家电", "price": 1599, "cost": 620},
    {"id": "P028", "name": "轻奢羊毛围巾", "category": "服饰鞋包", "price": 259, "cost": 82},
    {"id": "P029", "name": "儿童积木桌游套装", "category": "母婴用品", "price": 199, "cost": 62},
    {"id": "P030", "name": "智能跳绳计数版", "category": "运动户外", "price": 79, "cost": 26},
]

SURNAMES = "王李张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗"
GIVEN_NAMES_M = ["伟", "强", "磊", "洋", "勇", "军", "杰", "涛", "明", "超", "华", "飞", "鑫", "波", "斌"]
GIVEN_NAMES_F = ["芳", "娜", "静", "丽", "敏", "婷", "玲", "雪", "萍", "燕", "慧", "颖", "琳", "露", "倩"]

CITIES = {
    "华东": ["上海", "杭州", "南京", "苏州", "宁波"],
    "华南": ["广州", "深圳", "东莞", "佛山", "厦门"],
    "华北": ["北京", "天津", "石家庄", "济南", "青岛"],
    "西南": ["成都", "重庆", "昆明", "贵阳", "绵阳"],
    "华中": ["武汉", "长沙", "郑州", "南昌", "合肥"],
}

FAQ_CATEGORIES = {
    "订单相关": [
        {"q": "如何查看我的订单状态？", "a": "登录APP→我的→订单中心，可查看全部订单状态。也可在订单详情页点击「物流追踪」查看实时配送进度。"},
        {"q": "订单支付后多久发货？", "a": "现货商品下单后24小时内发货，预售商品按页面标注时间发货。大促期间可能延长至48小时。"},
        {"q": "可以修改已下单的收货地址吗？", "a": "订单未发货前，可在订单详情页修改收货地址。已发货订单需联系客服协助处理。"},
        {"q": "如何取消订单？", "a": "未发货订单可在订单详情页点击「取消订单」。已发货订单需申请退货退款。优惠券将自动退回账户。"},
        {"q": "下单时优惠券没有抵扣怎么办？", "a": "请在下单确认页手动选择优惠券。如仍有问题，可在支付后30分钟内联系客服调整，逾期不予处理。"},
        {"q": "订单显示已签收但未收到货怎么办？", "a": "请联系快递员核实，如确实未收到，请在订单页面申请「未收到货」售后，我们将在48小时内处理。"},
        {"q": "支持哪些支付方式？", "a": "支持微信支付、支付宝、银行卡、花呗、信用卡分期。企业采购支持对公转账。"},
        {"q": "如何开具发票？", "a": "下单时可选择电子普票或纸质专票。电子发票下单后即时生成，专票需3-5个工作日邮寄。"},
    ],
    "退换货": [
        {"q": "退换货期限是多久？", "a": "自签收之日起7天内可无理由退货，15天内可换货。食品、贴身衣物等特殊商品不支持无理由退货。"},
        {"q": "退货运费谁承担？", "a": "商品质量问题运费由我方承担。无理由退货运费由买家承担，可使用运费险抵扣。"},
        {"q": "退款多久到账？", "a": "仓库签收退货后1-3个工作日审核，审核通过后1-5个工作日原路退回。信用卡退款可能需7-15个工作日。"},
        {"q": "收到的商品有破损怎么办？", "a": "请在签收后24小时内拍照并联系客服，我们将免费补发或全额退款。保留原包装有助于快速处理。"},
        {"q": "可以只退部分商品吗？", "a": "可以。在订单详情页选择需要退货的商品申请即可。优惠分摊将按比例退回。"},
        {"q": "换货可以换不同颜色/尺码吗？", "a": "可以。在换货申请中选择目标颜色和尺码，差价多退少补。如目标商品无库存将通知您。"},
    ],
    "会员权益": [
        {"q": "会员等级如何划分？", "a": "分四个等级：普通会员、银卡（年消费满2000）、金卡（年消费满5000）、黑卡（年消费满10000）。等级每年1月1日重算。"},
        {"q": "会员有哪些专属权益？", "a": "银卡：95折+生日礼；金卡：9折+专属客服+新品试用；黑卡：85折+免运费+VIP活动+专属顾问。"},
        {"q": "会员积分如何获取和使用？", "a": "消费1元积1分，评价晒单额外送50分。积分可兑换优惠券（100分=5元券）、实物奖品或抵扣现金。"},
        {"q": "如何升级会员等级？", "a": "系统每月1日自动核算过去12个月消费金额，达标自动升级并短信通知。升级即刻享受新等级权益。"},
        {"q": "会员生日有什么福利？", "a": "银卡及以上会员生日当月可获得：专属优惠券包（满减券3张）+ 生日礼包1份（随机小样组合）。需提前完善生日信息。"},
        {"q": "积分会不会过期？", "a": "积分有效期为获取后12个月，到期自动清零。每年6月和12月会发送积分到期提醒。"},
    ],
    "配送物流": [
        {"q": "配送范围覆盖哪些地区？", "a": "全国31省市区均可配送，偏远地区（西藏、新疆部分区域）需5-7个工作日。港澳台暂不支持。"},
        {"q": "配送时效是多久？", "a": "一线城市次日达，二三线城市2-3天，偏远地区5-7天。大促期间可能延长1-2天。"},
        {"q": "可以指定配送时间吗？", "a": "金卡及以上会员可指定2小时送时段。其他用户可在下单时选择上午/下午/晚间三个时段。"},
        {"q": "配送费怎么计算？", "a": "订单满99元免运费，未满收取8元基础运费。大件商品额外加收20-50元。黑卡会员无限免运费。"},
        {"q": "如何查询物流信息？", "a": "订单详情页点击「查看物流」即可查看实时轨迹。也可通过快递单号在快递公司官网查询。"},
    ],
    "促销活动": [
        {"q": "每月有哪些固定优惠活动？", "a": "每月1号会员日（双倍积分）、15号品牌日（精选5折）、28号清仓日（临期低至3折）。详情见APP首页活动栏。"},
        {"q": "优惠券使用规则是什么？", "a": "每单限用1张优惠券，不叠加。部分商品不参与优惠活动，以商品详情页标注为准。优惠券过期作废。"},
        {"q": "拼团活动怎么参加？", "a": "选择拼团商品→发起或参与拼团→分享链接邀请好友→3人成团享特价→24小时未成团自动退款。"},
        {"q": "限时秒杀有什么技巧？", "a": "提前将商品加入购物车，秒杀开始前1分钟进入结算页，优先使用已保存地址和支付方式，提高抢购成功率。"},
        {"q": "老带新奖励怎么领？", "a": "分享专属邀请码，新用户首单完成后双方各得50元无门槛券。每月最高可获10次奖励。"},
    ],
}

REVIEW_TEMPLATES_POSITIVE = [
    "质量很好，{}用着很舒服，回购了",
    "包装精美，物流也快，{}性价比超高",
    "朋友推荐的{}，确实不错，会继续购买",
    "{}用了两周感觉有明显改善，推荐大家试试",
    "{}这个价位真的很值，比实体店便宜很多",
    "已经是第{}次购买了，一如既往地好",
]

REVIEW_TEMPLATES_NEGATIVE = [
    "{}质量不行，用了几天就出问题了，失望",
    "跟描述不符，{}实物差距很大，希望改进",
    "物流太慢了，{}到货时都快过期了",
    "{}价格虚高，同款别家便宜多了，不推荐",
    "客服态度差，{}有问题也不给解决",
]

REVIEW_TEMPLATES_NEUTRAL = [
    "{}还行吧，一般般，没有特别惊喜",
    "{}中规中矩，这个价位说得过去",
    "收到{}了，还没用，先给个中评吧",
]


# ═══════════════════════════════════════════════════════════
# Generation functions
# ═══════════════════════════════════════════════════════════

def _seasonal_factor(month: int) -> float:
    """Monthly seasonal multiplier (higher in Q4, lower in Q1)."""
    base = [0.75, 0.70, 0.80, 0.85, 0.90, 0.95,
            0.88, 0.92, 1.00, 1.05, 1.30, 1.40]
    return base[month - 1]


def _region_factor(region: str) -> float:
    return {"华东": 1.3, "华南": 1.1, "华北": 1.0, "华中": 0.85, "西南": 0.75}[region]


def _category_base(category: str) -> float:
    return {"美妆个护": 180, "食品饮料": 150, "数码家电": 60, "服饰鞋包": 100,
            "家居日用": 80, "母婴用品": 70, "运动户外": 55, "宠物用品": 45}[category]


def _channel_ratio(channel: str) -> float:
    return {"线上直营": 0.45, "线上分销": 0.30, "线下门店": 0.25}[channel]


def generate_sales() -> list:
    """Generate 18 months of sales data."""
    records = []
    for year_offset, month_start, m_count in [(0, 7, 6), (1, 1, 12)]:
        year = 2024 + year_offset
        for mi in range(month_start, month_start + m_count):
            for region in REGIONS:
                for category in CATEGORIES:
                    for channel in CHANNELS:
                        base = _category_base(category)
                        orders = int(base * _seasonal_factor(mi)
                                     * _region_factor(region)
                                     * _channel_ratio(channel)
                                     * random.uniform(0.80, 1.20))
                        if orders < 5:
                            orders = random.randint(5, 15)
                        avg_price = next(p["price"] for p in PRODUCTS if p["category"] == category)
                        amount = round(orders * avg_price * random.uniform(0.7, 1.4), 2)
                        customers = int(orders * random.uniform(0.55, 0.80))
                        return_rate = round(random.uniform(0.02, 0.12), 4)
                        records.append({
                            "date": f"{year}-{mi:02d}",
                            "region": region,
                            "category": category,
                            "channel": channel,
                            "sales_amount": amount,
                            "order_count": orders,
                            "customer_count": customers,
                            "avg_order_value": round(amount / max(orders, 1), 2),
                            "return_rate": return_rate,
                        })
    return records


def generate_customers() -> list:
    """Generate 120 customer profiles with RFM scores."""
    customers = []
    for i in range(1, 121):
        gender = random.choice(GENDERS)
        surname = random.choice(SURNAMES)
        given = random.choice(GIVEN_NAMES_M if gender == "男" else GIVEN_NAMES_F)
        region = random.choice(REGIONS)
        city = random.choice(CITIES[region])
        age = random.randint(22, 55)
        level = random.choices(MEMBER_LEVELS, weights=[40, 30, 20, 10])[0]

        recency = random.randint(1, 180)
        frequency = random.randint(1, 48)
        monetary = round(random.uniform(200, 80000), 2)

        # RFM scoring (1-5)
        r_score = 5 if recency <= 30 else (4 if recency <= 60 else (3 if recency <= 90 else (2 if recency <= 120 else 1)))
        f_score = 5 if frequency >= 24 else (4 if frequency >= 12 else (3 if frequency >= 6 else (2 if frequency >= 3 else 1)))
        m_score = 5 if monetary >= 20000 else (4 if monetary >= 10000 else (3 if monetary >= 5000 else (2 if monetary >= 2000 else 1)))

        # Segment assignment
        total = r_score + f_score + m_score
        if total >= 13:
            segment = "高价值活跃" if r_score >= 4 else "高价值沉睡"
        elif total >= 9:
            segment = "中价值成长" if r_score >= 3 else "中价值稳定"
        else:
            segment = "低价值潜力" if f_score >= 2 else "低价值流失"

        churn_risk = "高" if r_score <= 2 and f_score <= 2 else ("中" if r_score <= 2 else "低")
        preferred_cat = random.choice(CATEGORIES)
        preferred_ch = random.choice(CHANNELS)
        ltv = round(monetary * random.uniform(1.5, 4.0), 2)

        customers.append({
            "id": f"C{i:03d}",
            "name": surname + given,
            "gender": gender,
            "age": age,
            "region": region,
            "city": city,
            "member_level": level,
            "recency_days": recency,
            "frequency": frequency,
            "monetary": monetary,
            "r_score": r_score,
            "f_score": f_score,
            "m_score": m_score,
            "segment": segment,
            "churn_risk": churn_risk,
            "preferred_category": preferred_cat,
            "preferred_channel": preferred_ch,
            "ltv": ltv,
            "is_active": recency <= 60,
        })
    return customers


def generate_reviews() -> list:
    """Generate 60 customer reviews."""
    reviews = []
    for i in range(1, 61):
        product = random.choice(PRODUCTS)
        sentiment = random.choices(["正面", "中性", "负面"], weights=[55, 25, 20])[0]
        if sentiment == "正面":
            template = random.choice(REVIEW_TEMPLATES_POSITIVE)
            rating = random.choices([4, 5], weights=[40, 60])[0]
        elif sentiment == "负面":
            template = random.choice(REVIEW_TEMPLATES_NEGATIVE)
            rating = random.choices([1, 2], weights=[60, 40])[0]
        else:
            template = random.choice(REVIEW_TEMPLATES_NEUTRAL)
            rating = 3

        content = template.format(product["name"])
        days_ago = random.randint(1, 90)
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        reviews.append({
            "id": f"R{i:03d}",
            "product_id": product["id"],
            "product_name": product["name"],
            "category": product["category"],
            "rating": rating,
            "content": content,
            "sentiment": sentiment,
            "date": date,
        })
    return reviews


def generate_faq() -> list:
    """Generate FAQ knowledge base entries."""
    items = []
    idx = 1
    for cat, qa_list in FAQ_CATEGORIES.items():
        for qa in qa_list:
            items.append({
                "id": f"FAQ{idx:03d}",
                "category": cat,
                "question": qa["q"],
                "answer": qa["a"],
            })
            idx += 1
    return items


# ═══════════════════════════════════════════════════════════
# Save & Load
# ═══════════════════════════════════════════════════════════

def save_all():
    """Generate and save all data to JSON files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    sales = generate_sales()
    customers = generate_customers()
    reviews = generate_reviews()
    faq = generate_faq()

    (DATA_DIR / "sales.json").write_text(json.dumps(sales, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "customers.json").write_text(json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "products.json").write_text(json.dumps(PRODUCTS, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "reviews.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "faq.json").write_text(json.dumps(faq, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Data generated: {len(sales)} sales, {len(customers)} customers, "
          f"{len(PRODUCTS)} products, {len(reviews)} reviews, {len(faq)} FAQ")


class DataLoader:
    """Singleton-like data loader with lazy loading and computed aggregations."""

    _cache = {}

    @classmethod
    def _load(cls, name: str) -> list:
        if name not in cls._cache:
            path = DATA_DIR / f"{name}.json"
            if not path.exists():
                save_all()
            cls._cache[name] = json.loads(path.read_text(encoding="utf-8"))
        return cls._cache[name]

    @classmethod
    def sales(cls) -> list:
        return cls._load("sales")

    @classmethod
    def customers(cls) -> list:
        return cls._load("customers")

    @classmethod
    def products(cls) -> list:
        return cls._load("products")

    @classmethod
    def reviews(cls) -> list:
        return cls._load("reviews")

    @classmethod
    def faq(cls) -> list:
        return cls._load("faq")

    @classmethod
    def dashboard_summary(cls) -> dict:
        """Pre-computed BI dashboard summary."""
        sales = cls.sales()
        total_amount = sum(s["sales_amount"] for s in sales)
        total_orders = sum(s["order_count"] for s in sales)
        total_customers = sum(s["customer_count"] for s in sales)
        avg_aov = round(total_amount / max(total_orders, 1), 2)

        # Latest month metrics
        latest_month = max(s["date"] for s in sales)
        prev_months = sorted(set(s["date"] for s in sales))
        current_idx = prev_months.index(latest_month)
        prev_month = prev_months[current_idx - 1] if current_idx > 0 else latest_month

        latest_amount = sum(s["sales_amount"] for s in sales if s["date"] == latest_month)
        prev_amount = sum(s["sales_amount"] for s in sales if s["date"] == prev_month)
        yoy_growth = round((latest_amount - prev_amount) / max(prev_amount, 1) * 100, 1)

        # Monthly trend
        monthly = {}
        for s in sales:
            monthly.setdefault(s["date"], {"amount": 0, "orders": 0})
            monthly[s["date"]]["amount"] += s["sales_amount"]
            monthly[s["date"]]["orders"] += s["order_count"]
        trend = [{"date": d, "amount": round(v["amount"], 2), "orders": v["orders"]}
                 for d, v in sorted(monthly.items())]

        # Category distribution (latest month)
        cat_dist = {}
        for s in sales:
            if s["date"] == latest_month:
                cat_dist[s["category"]] = cat_dist.get(s["category"], 0) + s["sales_amount"]
        category_pie = [{"name": k, "value": round(v, 2)} for k, v in sorted(cat_dist.items(), key=lambda x: -x[1])]

        # Region comparison (latest month)
        region_dist = {}
        for s in sales:
            if s["date"] == latest_month:
                region_dist[s["region"]] = region_dist.get(s["region"], 0) + s["sales_amount"]
        region_bar = [{"name": k, "value": round(v, 2)} for k, v in sorted(region_dist.items(), key=lambda x: -x[1])]

        # Channel comparison
        channel_dist = {}
        for s in sales:
            if s["date"] == latest_month:
                channel_dist[s["channel"]] = channel_dist.get(s["channel"], 0) + s["sales_amount"]
        channel_pie = [{"name": k, "value": round(v, 2)} for k, v in sorted(channel_dist.items(), key=lambda x: -x[1])]

        # Category x Region heatmap
        cats = CATEGORIES
        regs = REGIONS
        heat_data = []
        for s in sales:
            if s["date"] == latest_month:
                ci = cats.index(s["category"]) if s["category"] in cats else -1
                ri = regs.index(s["region"]) if s["region"] in regs else -1
                if ci >= 0 and ri >= 0:
                    heat_data.append([ci, ri, round(s["sales_amount"], 2)])
        # Aggregate duplicates
        heat_agg = {}
        for ci, ri, v in heat_data:
            key = (ci, ri)
            heat_agg[key] = heat_agg.get(key, 0) + v
        heat_final = [[ci, ri, round(v, 2)] for (ci, ri), v in heat_agg.items()]

        # Recent monthly growth rates
        growth_rates = []
        sorted_dates = sorted(monthly.keys())
        for i in range(1, len(sorted_dates)):
            cur = monthly[sorted_dates[i]]["amount"]
            prev = monthly[sorted_dates[i - 1]]["amount"]
            rate = round((cur - prev) / max(prev, 1) * 100, 1)
            growth_rates.append({"date": sorted_dates[i], "rate": rate})

        return {
            "kpi": {
                "total_amount": round(total_amount, 2),
                "total_orders": total_orders,
                "avg_order_value": avg_aov,
                "yoy_growth": yoy_growth,
                "latest_month": latest_month,
                "latest_amount": round(latest_amount, 2),
            },
            "trend": trend,
            "category_pie": category_pie,
            "region_bar": region_bar,
            "channel_pie": channel_pie,
            "heatmap": {"x_labels": cats, "y_labels": regs, "data": heat_final},
            "growth_rates": growth_rates,
        }

    @classmethod
    def segmentation_data(cls) -> dict:
        """Pre-computed RFM segmentation for marketing dashboard."""
        customers = cls.customers()
        segment_counts = {}
        for c in customers:
            segment_counts[c["segment"]] = segment_counts.get(c["segment"], 0) + 1

        segment_pie = [{"name": k, "value": v} for k, v in sorted(segment_counts.items(), key=lambda x: -x[1])]

        # Scatter data (Recency vs Monetary, colored by segment)
        scatter_data = {}
        for c in customers:
            seg = c["segment"]
            scatter_data.setdefault(seg, []).append({
                "id": c["id"],
                "name": c["name"],
                "recency": c["recency_days"],
                "frequency": c["frequency"],
                "monetary": c["monetary"],
                "segment": seg,
            })

        # RFM distribution
        r_dist = [0] * 5
        f_dist = [0] * 5
        m_dist = [0] * 5
        for c in customers:
            r_dist[c["r_score"] - 1] += 1
            f_dist[c["f_score"] - 1] += 1
            m_dist[c["m_score"] - 1] += 1

        churn_risk_counts = {"高": 0, "中": 0, "低": 0}
        for c in customers:
            churn_risk_counts[c["churn_risk"]] += 1

        return {
            "segment_pie": segment_pie,
            "scatter": scatter_data,
            "rfm_dist": {"r": r_dist, "f": f_dist, "m": m_dist},
            "churn_risk": churn_risk_counts,
            "total_customers": len(customers),
        }

    @classmethod
    def sentiment_data(cls) -> dict:
        """Pre-computed sentiment summary."""
        reviews = cls.reviews()
        counts = {"正面": 0, "中性": 0, "负面": 0}
        cat_sentiment = {}
        for r in reviews:
            counts[r["sentiment"]] += 1
            cat_sentiment.setdefault(r["category"], {"正面": 0, "中性": 0, "负面": 0})
            cat_sentiment[r["category"]][r["sentiment"]] += 1

        sentiment_pie = [{"name": k, "value": v} for k, v in counts.items()]
        cat_bar = [{"category": k, **v} for k, v in sorted(cat_sentiment.items())]

        # Rating distribution
        rating_dist = [0] * 5
        for r in reviews:
            rating_dist[r["rating"] - 1] += 1

        return {
            "sentiment_pie": sentiment_pie,
            "category_sentiment": cat_bar,
            "rating_dist": rating_dist,
            "total_reviews": len(reviews),
            "avg_rating": round(sum(r["rating"] for r in reviews) / max(len(reviews), 1), 1),
        }

    @classmethod
    def cs_stats(cls) -> dict:
        """Pre-computed customer service stats."""
        faq = cls.faq()
        cat_counts = {}
        for f in faq:
            cat_counts[f["category"]] = cat_counts.get(f["category"], 0) + 1
        return {
            "total_faq": len(faq),
            "faq_categories": [{"name": k, "count": v} for k, v in sorted(cat_counts.items(), key=lambda x: -x[1])],
            "today_chats": random.randint(80, 200),
            "satisfaction_rate": round(random.uniform(88, 96), 1),
            "avg_response_time": round(random.uniform(1.2, 3.5), 1),
            "pending_tickets": random.randint(5, 25),
        }

    @classmethod
    def clear_cache(cls):
        cls._cache = {}


if __name__ == "__main__":
    save_all()
