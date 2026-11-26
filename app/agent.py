"""Bounded local agent: model chooses read tools, code executes and records steps."""
from urllib.error import HTTPError
from . import local_model
from .engine import recommend


def run(goal, context, read_records, memory=None):
    if not isinstance(goal,str) or not 1 <= len(goal.strip()) <= 500:
        raise ValueError('请描述这次穿搭目标（最多 500 字）')
    if not isinstance(context,dict):
        raise ValueError('穿搭条件无效')
    if len(str(context)) > 8000:
        raise ValueError('穿搭条件过长')
    memory = memory if isinstance(memory,dict) else {}
    applied = {**memory.get('context',{}),**context}
    # A follow-up can correct the previous outfit without re-entering every field.
    if '正式' in goal or '见客户' in goal:
        applied['scene'] = '客户会面'
    elif '休闲' in goal:
        applied['scene'] = '休闲'
    try:
        plan = local_model.choose_tools(goal)
        degraded = False
    except (ValueError,OSError,TimeoutError,HTTPError):
        plan = {'tools':['feedback'],'reason':'','model':None,'elapsed_ms':0}
        degraded = True
    selected = list(plan['tools'])
    # Explicit user requests take precedence over a small model's omitted tools.
    if any(word in goal for word in ('以前避开','之前避开','不喜欢的衣服','反馈')) and 'feedback' not in selected:
        selected.append('feedback')
    if any(word in goal for word in ('上次穿','以前穿','历史穿搭','穿搭记录')) and 'history' not in selected:
        selected.append('history')
    trace = [{'step':'plan','actor':'普通规则恢复' if degraded else 'Qwen 本机模型＋用户明确要求',
              'detail':'本机模型不可用，已改用普通规则推荐' if degraded else '只记录实际选择和执行的本地工具',
              'tools':selected,'elapsed_ms':plan['elapsed_ms']}]
    wardrobe = read_records('wardrobe')
    trace.append({'step':'tool','name':'read_wardrobe','count':len(wardrobe)})
    avoided = []
    for tool in selected:
        if tool == 'history':
            history = read_records('history')
            if history and not applied.get('scene'):
                old = history[-1].get('context',{})
                if old.get('scene') in local_model.SCENES:
                    applied['scene'] = old['scene']
            trace.append({'step':'tool','name':'read_history','count':len(history),
                          'used_scene':applied.get('scene') if history else None})
        elif tool == 'feedback':
            feedback = read_records('feedback')
            avoided = [x['item_id'] for x in feedback if x.get('action') == 'avoid' and x.get('item_id')]
            trace.append({'step':'tool','name':'read_feedback','count':len(feedback),
                          'avoided_count':len(avoided)})
    result = recommend(applied, wardrobe, avoided)
    trace.append({'step':'tool','name':'recommend','outfit_count':len(result['outfit']),
                  'missing':result['missing']})
    result['agent'] = {'mode':'普通规则恢复' if degraded else '受限本机工具调度',
                       'model':plan['model'],'degraded':degraded,'trace':trace,
                       'turn':min(int(memory.get('turn',0))+1,10),
                       'limits':'本次会话最多保留 10 轮；天气需用户提供或另行查询'}
    return result
