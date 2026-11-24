"""Coarse garment color families; approximate hex fallback for older entries."""
import colorsys
import re

PALETTE = {'米白':'#e8dfca','白色':'#f4f3ee','黑色':'#33353a','灰色':'#a1a49e',
           '蓝色':'#718eaf','绿色':'#7e9c7c','棕色':'#94765e','红色':'#bd655f',
           '粉色':'#d6a7b6','紫色':'#9c88b7','黄色':'#d9c27d','橙色':'#d39964'}


def item_color(item):
    explicit = item.get('color_name')
    if explicit in PALETTE: return explicit
    name = str(item.get('name', ''))
    for key, words in [('米白',('米白','米色','奶油','奶白')),('白色',('白色','小白','白衬')),
                       ('黑色',('黑色','黑裤')),('灰色',('灰色',)),('蓝色',('蓝','牛仔')),
                       ('绿色',('绿',)),('棕色',('棕','咖啡','驼色')),('粉色',('粉',)),
                       ('紫色',('紫',)),('红色',('红',)),('黄色',('黄',)),('橙色',('橙',))]:
        if any(word in name for word in words): return key
    value = item.get('color')
    if not isinstance(value,str) or not re.fullmatch(r'#[a-fA-F0-9]{6}',value): return None
    rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)]
    h,s,v=colorsys.rgb_to_hsv(*rgb)
    if v<.3: return '黑色'
    if s<.1: return '白色' if v>.88 else '灰色'
    if v>.8 and .06<h<.18 and s<.3: return '米白'
    if h<.045 or h>.95: return '粉色' if v>.7 and s<.5 else '红色'
    if h<.12: return '棕色' if v<.72 else '橙色'
    if h<.2: return '黄色'
    if h<.46: return '绿色'
    if h<.72: return '蓝色'
    if h<.87: return '紫色'
    return '粉色'


def preferences(context):
    result=[]
    for key in ('preferred_colors','avoided_colors'):
        values=context.get(key,[])
        if not isinstance(values,list) or len(values)>3 or any(not isinstance(v,str) or v not in PALETTE for v in values):
            raise ValueError('配色请选择最多三种支持的颜色')
        result.append(list(dict.fromkeys(values)))
    if set(result[0]) & set(result[1]): raise ValueError('期望颜色与避开颜色不能重复')
    return result
