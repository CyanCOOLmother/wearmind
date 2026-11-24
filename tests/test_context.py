import unittest
from app.engine import recommend
from app.colors import item_color


def item(id,cat,color,tags=()):
    return {'id':id,'name':id,'category':cat,'color_name':color,'tags':list(tags)}

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.wardrobe=[item('cream-top','上装','米白',['舒适']),item('blue-top','上装','蓝色',['客户会面']),item('green-top','上装','绿色'),item('black-trousers','下装','黑色',['舒适']),item('blue-trousers','下装','蓝色',['舒适']),item('white-shoes','鞋履','白色',['舒适','怕水']),item('black-boots','鞋履','黑色',['防水','舒适']),item('coat','外套','棕色',['保暖'])]
    def test_palette_coverage(self):
        result=recommend({'preferred_colors':['米白','蓝色']},self.wardrobe)
        self.assertEqual(result['unmet_colors'],[])
        self.assertTrue({'米白','蓝色'} <= {x['color_name'] for x in result['outfit']})
    def test_avoid_color(self):
        result=recommend({'avoided_colors':['黑色']},self.wardrobe)
        self.assertNotIn('黑色',[x['color_name'] for x in result['outfit']])
    def test_missing_color_no_invention(self):
        result=recommend({'preferred_colors':['红色']},self.wardrobe)
        self.assertEqual(result['unmet_colors'],['红色'])
        self.assertEqual(result['shopping_needs'][0]['color'],'红色')
        self.assertTrue(all(x['id'] in [i['id'] for i in self.wardrobe] for x in result['outfit']))
    def test_color_cannot_override_sensitive(self):
        tight=item('tight-red','下装','红色',['紧腰'])
        result=recommend({'preferred_colors':['红色'],'state':'腰腹敏感'},self.wardrobe+[tight])
        self.assertNotIn('tight-red',[x['id'] for x in result['outfit']])
    def test_rain_shoes_over_color(self):
        result=recommend({'preferred_colors':['白色'],'weather':'雨天'},self.wardrobe)
        self.assertEqual(next(x['id'] for x in result['outfit'] if x['category']=='鞋履'),'black-boots')
    def test_destination_overrides_origin(self):
        result=recommend({'temperature':30,'weather':'晴天','origin_weather':{'temperature':30},'destination':'杭州','destination_weather':{'temperature':10,'weather':'雨天','place':'杭州','source':'Open-Meteo','date':'2026-10-14'}},self.wardrobe)
        self.assertEqual(result['effective_weather']['temperature'],10)
        self.assertEqual(len(result['outfit']),4)
        self.assertIn('black-boots',[x['id'] for x in result['outfit']])
        self.assertTrue(any('杭州' in x for x in result['reasons']))
    def test_origin_adds_layer(self):
        result=recommend({'origin_weather':{'temperature':10},'destination_weather':{'temperature':25,'weather':'晴天'}},self.wardrobe)
        self.assertIn('外套',[x['category'] for x in result['outfit']])
    def test_destination_walking(self):
        heels=item('heels','鞋履','红色',['高跟','客户会面'])
        result=recommend({'environment':'户外步行','preferred_colors':['红色']},self.wardrobe+[heels])
        self.assertNotIn('heels',[x['id'] for x in result['outfit']])
    def test_invalid_colors(self):
        for data in [{'preferred_colors':'蓝色'},{'preferred_colors':['蓝色'],'avoided_colors':['蓝色']},{'preferred_colors':['不存在']},{'preferred_colors':[{}]}]:
            with self.assertRaises(ValueError): recommend(data,self.wardrobe)
    def test_old_item_color(self):
        self.assertEqual(item_color({'name':'浅蓝棉衬衫','color':'#b8ced2'}),'蓝色')
        self.assertEqual(item_color({'name':'米白针织衫','color':'#e4d9c4'}),'米白')

if __name__=='__main__': unittest.main()
