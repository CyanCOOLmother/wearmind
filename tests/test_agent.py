import unittest
from unittest.mock import patch
from app import agent, local_model


class AgentTests(unittest.TestCase):
    def test_rejects_unapproved_tool(self):
        with patch.object(local_model,'status',return_value={'models':['local']}), \
             patch.object(local_model,'request_json',return_value={'message':{'content':'{"tools":["shell"]}'}}):
            old = local_model.RUNTIME, local_model.MODEL
            try:
                local_model.RUNTIME, local_model.MODEL = 'ollama','local'
                with self.assertRaises(ValueError): local_model.choose_tools('今天通勤')
            finally:
                local_model.RUNTIME, local_model.MODEL = old

    def test_tool_choice_changes_result_and_trace(self):
        items = [{'id':'avoid','name':'旧鞋','category':'鞋履','tags':['通勤'],'color':'#ffffff'},
                 {'id':'keep','name':'新鞋','category':'鞋履','tags':['通勤'],'color':'#ffffff'}]
        data = {'wardrobe':items,'history':[],
                'feedback':[{'action':'avoid','item_id':'avoid'}]}
        with patch.object(local_model,'choose_tools',return_value={
            'tools':['feedback'],'reason':'避免不喜欢的鞋','model':'local','elapsed_ms':3}):
            result = agent.run('今天通勤穿什么',{'scene':'通勤'},lambda kind:data[kind])
        self.assertEqual([x['id'] for x in result['outfit']],['keep'])
        self.assertEqual([x['name'] for x in result['agent']['trace'] if x['step']=='tool'],
                         ['read_wardrobe','read_feedback','recommend'])

    def test_followup_remembers_context_and_changes_scene(self):
        data={'wardrobe':[{'id':'jacket','name':'西装','category':'上装','tags':['客户会面'],'color':'#000000'}],
              'history':[],'feedback':[]}
        with patch.object(local_model,'choose_tools',return_value={
            'tools':[],'reason':'','model':'local','elapsed_ms':2}):
            result=agent.run('换得正式一点',{},lambda kind:data[kind],
                             {'context':{'scene':'休闲','temperature':20},'turn':1})
        self.assertEqual(result['context']['scene'],'客户会面')
        self.assertEqual(result['agent']['turn'],2)

    def test_model_failure_is_labeled_rule_fallback(self):
        data={'wardrobe':[],'history':[],'feedback':[]}
        with patch.object(local_model,'choose_tools',side_effect=TimeoutError()):
            result=agent.run('今天通勤',{'scene':'通勤'},lambda kind:data[kind])
        self.assertTrue(result['agent']['degraded'])
        self.assertIsNone(result['agent']['model'])


if __name__ == '__main__': unittest.main()
