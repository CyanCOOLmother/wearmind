"""Deterministic local recommender. No network or model calls."""
import math
from itertools import product
from typing import Protocol
from .colors import item_color, preferences

class ModelProvider(Protocol):
    def explain(self, context: dict, outfit: list) -> str: ...

CATEGORIES = ('上装', '下装', '鞋履', '外套')
ENVIRONMENTS = ('室内为主', '户外步行', '海边', '山地')


def recommend(context, wardrobe, avoided=()):
    excluded = context.get('excluded_ids', [])
    locked = context.get('locked_ids', [])
    if not isinstance(excluded, list) or not isinstance(locked, list) or any(not isinstance(x, str) for x in excluded + locked):
        raise ValueError('单品选择无效')
    available = [x for x in wardrobe if x['id'] not in excluded and (not context.get('only_uploaded') or x.get('photo'))]
    locked_items = [x for x in available if x['id'] in locked]
    if len(locked_items) != len(set(locked)):
        raise ValueError('锁定单品不可用，请重新搭配')
    categories = [x['category'] for x in locked_items]
    if len(categories) != len(set(categories)):
        raise ValueError('同一类别只能锁定一件')
    wardrobe = [x for x in available if x['category'] not in categories or x['id'] in locked]
    preferred_colors, avoided_colors = preferences(context)
    # Destination conditions drive the main outfit, while origin conditions may add a layer.
    destination_weather = context.get('destination_weather')
    effective = destination_weather if isinstance(destination_weather,dict) else context
    temp = float(effective.get('temperature', context.get('temperature', 22)))
    if not math.isfinite(temp) or not -30 <= temp <= 50:
        raise ValueError('温度请输入 -30 到 50 之间的数字')
    weather = effective.get('weather', context.get('weather'))
    scene = context.get('scene', '通勤')
    if scene not in ('通勤', '客户会面', '休闲', '运动', '约会'):
        raise ValueError('请选择有效场景')
    environment = context.get('environment','室内为主')
    if environment not in ENVIRONMENTS: raise ValueError('请选择有效的目的地环境')
    destination = str(context.get('destination','')).strip()[:120]
    venue = str(context.get('venue','')).strip()[:120]
    state = str(context.get('state', ''))[:500]
    flags=context.get('comfort_flags')
    if flags is not None and (not isinstance(flags,list) or any(x not in ('疲惫','怕冷','怕热','腰腹敏感') for x in flags)):
        raise ValueError('已确认的身体感受无效')
    sensitive = ('腰腹敏感' in flags) if flags is not None else any(x in state for x in ('经期', '腰', '腹', '勒'))
    tired = ('疲惫' in flags) if flags is not None else (any(x in state for x in ('累', '疲', '困')) and not any(x in state for x in ('不累','不疲惫','不困')))
    feels_hot = ('怕热' in flags) if flags is not None else ('怕热' in state and '不怕热' not in state)
    feels_cold = ('怕冷' in flags) if flags is not None else ('怕冷' in state and '不怕冷' not in state)
    garment_needs=context.get('garment_needs', [])
    allowed_needs=('遮手臂','不卡腰','好活动','耐脏','抗皱','空调房','显高')
    if not isinstance(garment_needs,list) or any(x not in allowed_needs for x in garment_needs):
        raise ValueError('穿衣限制无效')
    walking = environment in ('户外步行','山地')
    origin_weather = context.get('origin_weather')
    origin_temp = None
    if isinstance(origin_weather,dict) and isinstance(destination_weather,dict):
        origin_temp = float(origin_weather.get('temperature',temp))
        if not math.isfinite(origin_temp) or not -30 <= origin_temp <=50: raise ValueError('出发地气温无效')
    cold = weather == '雪天' or temp < 18 or feels_cold
    journey_layer = origin_temp is not None and (origin_temp < 18 or abs(origin_temp-temp)>=8)
    weather_info = destination_weather if isinstance(destination_weather,dict) else context.get('weather_info')
    if isinstance(weather_info,dict) and weather_info.get('source') == 'Open-Meteo':
        reasons = [f'参考 {weather_info.get("place", destination or "所选地点")} {weather_info.get("date", "")} 的 Open-Meteo 天气：{temp:g}℃，{scene} 场景。']
        if isinstance(weather_info.get('low'),(int,float)) and isinstance(weather_info.get('high'),(int,float)) and weather_info['high']-weather_info['low']>=8:
            journey_layer=True
            reasons.append('当日温差较大，增加可穿脱的外层。')
    else:
        reasons = [f'按手动填写的 {temp:g}℃、{scene} 场景选择。']
    if destination or venue: reasons.append('目的地：'+' · '.join(x for x in (destination,venue,environment) if x)+'。')
    if origin_temp is not None:
        reasons.append(f'出发地 {origin_temp:g}℃，目的地 {temp:g}℃；以目的地为主，兼顾路上的冷热变化。')
    if journey_layer: reasons.append('出发地偏冷或途中温差明显：携带方便穿脱的外套，抵达后可调整。')
    if sensitive: reasons.append('腰腹敏感：排除紧腰单品，优先宽松版型。')
    if tired: reasons.append('疲惫状态：优先轻便、宽松的衣物与平底鞋。')
    if walking: reasons.append('目的地需要步行：排除高跟鞋，优先便于活动的单品。')
    if environment == '山地': reasons.append('山地环境可能比城市预报更冷；请按实际海拔另行确认保暖、防风与鞋底抓地力。')
    if environment == '海边': reasons.append('海边留意风感和日晒，衣物选择需兼顾防风与遮阳。')
    if feels_hot: reasons.append('体感怕热：优先透气单品，低温时仍保留可穿脱的保暖层。')
    if garment_needs:
        reasons.append('已纳入你的穿衣限制：'+'、'.join(garment_needs)+'。')
    if cold: reasons.append('体感偏冷或气温较低：增加保暖层。')
    if weather == '雪天': reasons.append('雪天注意防滑、防水，额外确认鞋底抓地力。')
    rain = weather == '雨天'
    if rain: reasons.append('目的地雨天优先防水鞋；出门记得带伞。')
    choices_by_category, missing = [], []
    for category in CATEGORIES if cold or journey_layer else CATEGORIES[:3]:
        choices = []
        for item in wardrobe:
            if item.get('category') != category or item['id'] in avoided: continue
            tags = item.get('tags', [])
            color = item_color(item)
            if color in avoided_colors: continue
            if sensitive and '紧腰' in tags: continue
            if (tired or walking) and '高跟' in tags: continue
            score = 3 * (scene in tags) + 2 * ('舒适' in tags)
            score += 4 * (cold and '保暖' in tags) + 4 * ((temp >= 26 or feels_hot) and '透气' in tags)
            score += 5 * (rain and '防水' in tags) - 5 * (rain and '怕水' in tags)
            score -= 8 * (temp >= 26 and '厚重' in tags)
            score += 5 * sum(need in tags for need in garment_needs)
            score += 3 * (color in preferred_colors)
            choices.append((score, {**item, 'color_name':color}))
        if choices:
            # Keep the best example of every requested color before filling top candidates.
            ranked=sorted(choices,key=lambda x:x[0],reverse=True)
            pool=ranked[:8]
            for color in preferred_colors:
                first=next((x for x in ranked if x[1]['color_name']==color),None)
                if first and first not in pool: pool.append(first)
            choices_by_category.append(pool)
        else: missing.append(category)
    selected = []
    if choices_by_category:
        def combination_score(combo):
            used={i['color_name'] for _,i in combo}
            return sum(score for score,_ in combo) + 4 * len(used & set(preferred_colors))
        best=max(product(*choices_by_category),key=combination_score)
        selected=[item for _,item in best]
    present={i['color_name'] for i in selected}
    unmet=[color for color in preferred_colors if color not in present]
    if preferred_colors:
        reasons.append('期望配色：'+'＋'.join(preferred_colors)+'；优先选择已有衣物，天气与舒适要求同时参与排序。')
    if avoided_colors: reasons.append('已排除颜色：'+'、'.join(avoided_colors)+'。')
    if unmet: reasons.append('本套未能覆盖'+ '、'.join(unmet) +'；可能是衣橱缺色、单品类别重叠或天气/舒适要求冲突。可以调整配色，或加入补购愿望清单。')
    if missing: reasons.append('衣橱缺少适合的' + '、'.join(missing) + '，本次搭配尚不完整。')
    if temp < 5: reasons.append('低温时请另外确认内层、帽子和围巾是否足够保暖。')
    shopping_needs=[{'kind':'color','color':c,'reason':'本次搭配未覆盖期望颜色；先考虑换搭或换色，再决定是否购买。'} for c in unmet]
    return {'outfit': selected, 'reasons': reasons, 'missing': missing,'unmet_colors':unmet,
            'shopping_needs':shopping_needs, 'effective_weather':{'temperature':temp,'weather':weather},
            'source': ('本机模型整理感受 + 本地规则筛选' if context.get('local_understanding') else '本地规则推荐 · 未调用模型'), 'context': context}
