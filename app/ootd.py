"""Local photo directions selected from outfit context; no camera inference."""
POSES = {
 'walk': {'title':'自然走来','tag':'街角 · 全身','steps':['身体侧转约 30°，自然向前迈一小步。','手臂放松摆动，另一只手轻扶包带或衣角。','视线看向镜头旁边，连拍后选动作最自然的一张。'], 'lens':'优先 1× 镜头，手机保持竖直；拍摄者后退留出全身空间。','frame':'脚底留少量空间，头顶留约一成画面；人物略偏一侧。','light':'找建筑阴影边缘的柔光，避免正午顶光。'},
 'lean': {'title':'靠墙放松','tag':'建筑 · 半身 / 全身','steps':['靠墙站稳，身体稍微侧向镜头。','一只脚轻向前放，肩膀自然下沉。','手轻扶袖口或包带，避免刻意绷紧身体。'], 'lens':'使用 1×，镜头放在胸口附近高度，保持地面与墙线平直。','frame':'利用门框或墙边形成竖线，让背景留出呼吸空间。','light':'面向明亮的天空方向，脸部尽量获得均匀柔光。'},
 'sit': {'title':'窗边坐一会','tag':'咖啡馆 · 坐姿','steps':['选择稳固座位，身体自然侧坐，双脚舒适落地。','手放在膝上或轻扶杯子，不用一直看镜头。','微微转肩看向窗外，拍下放松的瞬间。'], 'lens':'用 1× 拍半身，镜头与眼睛接近同高。','frame':'窗框放在画面边缘，桌面不要挡住主要衣物。','light':'侧前方窗光更柔和；避免明亮窗户正好处于身后。'},
 'mirror': {'title':'镜前记录','tag':'室内 · 穿搭记录','steps':['擦净镜面，站在镜子前留出完整衣物轮廓。','手机略移到脸旁，一只手自然垂放或整理袖口。','先拍正面，再轻侧身，记录衣服的层次和版型。'], 'lens':'优先 1×，手机保持竖直，不贴近镜子使用超广角。','frame':'镜面边框保持竖直，避免切到鞋尖或衣摆。','light':'面向窗户或均匀室内灯光，留意镜中杂物。'}
}


def guidance(context):
    environment=context.get('environment','室内为主')
    scene=context.get('scene','通勤')
    state=str(context.get('state',''))
    weather=context.get('destination_weather') or context
    weather=weather.get('weather') if isinstance(weather,dict) else ''
    preferred='walk' if environment in ('户外步行','海边','山地') or scene=='运动' else ('lean' if scene in ('通勤','客户会面') else 'sit')
    if any(x in state for x in ('累','疲','腰','腹')): preferred='sit'
    if weather in ('雨天','雪天'): preferred='lean'
    flags=context.get('comfort_flags')
    discomfort=any(x in flags for x in ('疲惫','腰腹敏感')) if isinstance(flags,list) else any(x in state for x in ('累','疲','腰','腹'))
    if discomfort and weather not in ('雨天','雪天'): preferred='sit'
    notes=[]
    if weather=='雨天': notes.append('雨天选有顶棚且地面干燥的地方；伞可作为道具，不做湿滑地面行走抓拍。')
    if weather=='雪天': notes.append('雪天以保暖、防滑为先；在安全干燥位置站定拍摄。')
    if environment=='海边': notes.append('选择远离浪线的稳定位置，背风整理衣摆再拍。')
    if environment=='山地': notes.append('在平整步道或平台站定，不靠近崖边，也不边走边倒退拍。')
    if discomfort: notes.append('按舒服的姿势拍就好；不需要收腹、扭腰或反复大幅度摆动作。')
    if context.get('preferred_colors'): notes.append('可以找与衣服主色协调的干净背景，让已选配色更清楚。')
    return {'recommended':preferred,'poses':[{'id':key,**value} for key,value in POSES.items()], 'notes':notes,
            'scene':scene,'environment':environment,'caption':'今天的穿搭，舒服也有自己的风格。'}
