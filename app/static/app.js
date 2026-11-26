const $=s=>document.querySelector(s);let agentSessionId=null;let current=null,lastContext=null,weatherInfo=null,weatherPlace=null,photoData=null,photoColor="#c5b5a4",destinationPlace=null,destinationWeather=null;const notice=t=>{$('#status').textContent=t;$('#status').style.display='block';clearTimeout(window.toast);window.toast=setTimeout(()=>$('#status').style.display='none',3500)};
async function api(path,body){const r=await fetch('/api/'+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const d=await r.json();if(!r.ok)throw Error(d.error||'操作失败');return d}
function el(tag,text,cls){const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n}
function art(item){const n=el('div',null,'art');const source=item.photo||item.reference_photo;if(source){const img=el('img');img.src=source;img.alt=item.name+(item.photo?'实拍':'演示参考图');img.loading='lazy';n.append(img)}else{n.append(el('span','等待你的实物照片','photo-placeholder'))}return n}
function card(item,feedback=false){const n=el('article',null,'garment');n.append(art(item),el('small',item.category+(item.color_name?' · '+item.color_name:'')),el('h3',item.name));if(item.reference_photo&&!item.photo){const source=el('a','实物参考图 ↗','photo-source');source.href=item.reference_source;source.target='_blank';source.rel='noopener';n.append(source)}if(feedback){const b=el('button','以后避开这件');b.onclick=async()=>{try{await api('feedback',{action:'avoid',item_id:item.id,reason:'用户主动避开'});await generate(lastContext);notice('已记住，下次推荐会避开这件单品')}catch(e){notice(e.message)}};n.append(b)}else n.append(el('small',item.tags.join(' · ')));return n}
function selectedColors(id){return [...document.querySelectorAll('#'+id+' input:checked')].map(x=>x.value)}
function context(){
 if($('#destination-query').value.trim()&&(!destinationPlace||!destinationWeather))throw Error('请先选择目的地并取得对应日期天气；也可清空目的地，使用当前城市天气');
 return{state:$('#state').value,...(window.edgeContext?window.edgeContext():{}),temperature:Number($('#temperature').value),weather:$('#weather').value,scene:$('#scene').value,weather_info:weatherInfo,
 origin_weather:weatherInfo||{temperature:Number($('#temperature').value),weather:$('#weather').value},destination:destinationPlace?placeName(destinationPlace):'',destination_weather:destinationWeather,
 venue:$('#venue').value,environment:$('#environment').value,preferred_colors:selectedColors('preferred-colors'),avoided_colors:[...$('#avoided-colors').selectedOptions].map(o=>o.value)}
}
async function generate(ctx=context(),useAgent=false){current=useAgent?await api('agent/run',{goal:ctx.state||'按今天的场景和衣橱给我一套穿搭',context:ctx,session_id:agentSessionId}):await api('recommend',ctx);lastContext=current.agent?current.context:ctx;if(current.agent)agentSessionId=current.agent.session_id;$('#outfit').replaceChildren(...current.outfit.map(i=>card(i,true)));$('#reasons').replaceChildren(...current.reasons.map(x=>el('li',x)));$('#source').textContent=current.agent?(current.agent.degraded?'本机模型不可用 · 普通规则推荐':'本机 Qwen 选择工具＋本地规则推荐'):current.source;$('#save').disabled=!!current.missing.length;$('#feedback-status').textContent=current.missing.length?'这套还缺少：'+current.missing.join('、')+'；请先调整条件再保存。':'喜欢这套可以保存；反馈会留在开发板本机。';renderNeeds(current,$('#shopping-needs'));$('#look-context').textContent=[lastContext.destination||'TODAY’S LOOK',lastContext.scene,current.effective_weather.temperature+'℃'].filter(Boolean).join(' · ');$('#look-palette').textContent=(ctx.preferred_colors||[]).join(' + ');const trace=$('#agent-trace');trace.hidden=!current.agent;if(current.agent){$('#agent-trace-steps').replaceChildren(...current.agent.trace.map(step=>el('p',step.step==='plan'?(current.agent.degraded?'备用方案：':'Qwen 选择：')+(step.tools.length?step.tools.join('、'):'直接使用当前条件')+'。'+step.detail:'执行：'+step.name+'。')))}else $('#agent-trace-steps').replaceChildren();if(window.refreshOOTD)window.refreshOOTD().catch(e=>notice('搭配已生成；拍照指导暂未更新：'+e.message));}
$('#agent-outfit').onclick=async()=>{const b=$('#agent-outfit'),status=$('#generation-status');b.disabled=true;status.textContent='本机模型正在选择需要读取的信息并搭配…';try{await generate(context(),true);status.textContent=current.agent.degraded?'本机模型暂不可用；已按普通规则生成搭配。':'✓ 本机助手已完成第 '+current.agent.turn+' 轮搭配。可修改上方想法后再次点击。';$('.result').scrollIntoView({behavior:'smooth',block:'start'})}catch(e){status.textContent='本机助手未完成：'+e.message+'。仍可点“直接给我一套”。'}finally{b.disabled=false}};
$('#context').onsubmit=async e=>{
 e.preventDefault();
 const button=$('#context button[type="submit"]'),status=$('#generation-status');
 button.disabled=true;status.textContent='正在按刚才确认的条件重新搭配，请稍候…';
 try{
  await generate();
  status.textContent='✓ 已重新计算：'+current.outfit.map(item=>item.name).join(' ＋ ')+'。下方可查看推荐理由。';
  $('.result').scrollIntoView({behavior:'smooth',block:'start'});
 }catch(error){status.textContent='这次没有生成成功：'+error.message;notice(error.message)}
 finally{button.disabled=false}
};
let quickNeed='舒服',quickMissing=[];
document.querySelectorAll('[data-quick-need]').forEach(button=>button.onclick=()=>{quickNeed=button.dataset.quickNeed;document.querySelectorAll('[data-quick-need]').forEach(x=>x.setAttribute('aria-pressed',String(x===button)))});
async function quickReadiness(){
 document.querySelectorAll('[data-quick-scene]').forEach(button=>button.disabled=true);
 const items=await api('wardrobe'),required=['上装','下装','鞋履'];
 quickMissing=required.filter(category=>!items.some(item=>item.category===category));
 $('#quick-guide').textContent=quickMissing.length?'本机衣橱还缺 '+quickMissing.join('、')+'。先补每类一件，才能给完整一套。':'衣橱有 '+items.length+' 件记录（可能含演示衣物）。先试一套，正式使用时请录入你自己的衣服。';
 document.querySelectorAll('[data-quick-scene]').forEach(button=>button.disabled=false);
}
document.querySelectorAll('[data-quick-scene]').forEach(button=>button.onclick=async()=>{
 if(quickMissing.length){await view('closet');notice('先补 '+quickMissing.join('、')+'，再回到今天快速开始');return}
 const state=button.dataset.quickState+(quickNeed==='怕冷'?'，今天有点怕冷':quickNeed==='利落'?'，想穿得更利落':'，优先舒服');
 $('#scene').value=button.dataset.quickScene;$('#state').value=state;$('#state').dispatchEvent(new Event('input'));
 if(typeof setBodyFlags==='function')setBodyFlags(quickNeed==='怕冷'?['怕冷']:[]);
 const originalLabel=button.textContent;button.disabled=true;button.textContent='正在搭配…';$('#quick-guide').textContent='本机助手正在查看衣橱和需要的记录，请稍候…';$('#generation-status').textContent='正在按你选的条件生成，请稍候…';$('.result').scrollIntoView({behavior:'smooth',block:'start'});
 try{await generate(context(),true);$('#quick-followup').hidden=false;$('#generation-status').textContent=current.agent.degraded?'本机模型暂不可用，已用规则给出一套。下方可以继续调整。':'已按你选的场景和在意点给出一套；下方可以继续调整。';$('#quick-guide').textContent=current.agent.degraded?'本机模型暂不可用，已按普通规则搭配；你仍可以继续调整。':'先看这一套；不合适可直接说“换得正式一点”，不用重新填写。';$('.result').scrollIntoView({behavior:'smooth',block:'start'})}
 catch(error){$('#quick-guide').textContent='这次没生成成功：'+error.message+'。也可使用下方普通推荐。';$('#generation-status').textContent='本机助手未完成：'+error.message+'。可以点左侧“直接给我一套”使用普通规则。';notice(error.message)}
 finally{button.disabled=false;button.textContent=originalLabel}
});
$('#quick-more-formal').onclick=async()=>{const b=$('#quick-more-formal');b.disabled=true;b.textContent='正在调整…';$('#generation-status').textContent='正在按上一套调整为更正式的场景…';$('#state').value='换得正式一点';$('#state').dispatchEvent(new Event('input'));try{await generate(context(),true);$('#scene').value=current.context.scene;$('#quick-guide').textContent='已按刚才那套调整为更正式的场景。';$('.result').scrollIntoView({behavior:'smooth',block:'start'})}catch(error){$('#generation-status').textContent='调整失败：'+error.message;notice(error.message)}finally{b.disabled=false;b.textContent='换得正式一点'}};
document.querySelectorAll('[data-start-mode]').forEach(button=>button.onclick=async()=>{
 if(button.dataset.startMode==='closet'){await view('closet');return;}
 const start=$('#quick-start');start.hidden=false;
 quickReadiness().catch(error=>$('#quick-guide').textContent='衣橱暂时无法读取：'+error.message+'。可用下方普通推荐。');
 start.scrollIntoView({behavior:'smooth',block:'center'});
 $('#quick-start button').focus();
});
document.querySelectorAll('[data-state]').forEach(b=>b.onclick=()=>{$('#state').value+='，'+b.dataset.state});
$('#save').onclick=async()=>{try{if(!current)return;await api('history',lastContext);$('#feedback-status').textContent='✓ 已保存到穿搭记忆。点顶部“更多 → 穿搭记忆”可以看到。';notice('这套搭配已保存到穿搭记忆')}catch(e){$('#feedback-status').textContent='保存失败：'+e.message;notice(e.message)}};
$('#accept').onclick=async()=>{try{if(!current)return;await api('feedback',{action:'accept',reason:'这套适合我'});$('#feedback-status').textContent='✓ 已记住你喜欢这套。';notice('已记录喜欢这套的反馈')}catch(e){$('#feedback-status').textContent='反馈未保存：'+e.message;notice(e.message)}};
async function view(name){if(name!=='ootd'&&window.stopOOTDCamera)window.stopOOTDCamera();if(name==='ootd'&&window.refreshOOTD)await window.refreshOOTD();document.querySelectorAll('.view').forEach(n=>n.hidden=n.id!==name);document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===name));if(name==='closet'){$('#wardrobe').replaceChildren(...(await api('wardrobe')).map(i=>card(i)));renderWishlist();}if(name==='history'){const items=(await api('history')).reverse();$('#history-list').replaceChildren(...(items.length?items.map(i=>{const n=el('article',null,'panel history-card');n.append(el('small',new Date(i.created_at).toLocaleString('zh-CN')),el('h3',i.outfit.map(x=>x.name).join(' ＋ ')),el('p',i.reasons.join(' ')));return n}):[el('p','还没有保存的搭配，去挑选今天的一套吧。')]))}}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view).catch(e=>notice(e.message)));
const mobileMore=$('#mobile-more'),mobileMenu=$('#mobile-menu');
mobileMore.onclick=()=>{mobileMenu.hidden=!mobileMenu.hidden;mobileMore.setAttribute('aria-expanded',String(!mobileMenu.hidden))};
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{mobileMenu.hidden=true;mobileMore.setAttribute('aria-expanded','false');mobileMore.classList.toggle('active',['trip','history','device'].includes(button.dataset.view))}));
$('#add').onsubmit=async e=>{e.preventDefault();try{await api('wardrobe',{name:$('#name').value,category:$('#category').value,tags:[...$('#tags').selectedOptions].map(o=>o.value),photo:photoData,color:photoColor,color_name:$('#item-color').value||null});$('#add').reset();clearPhoto();await view('closet');notice('衣物已加入衣橱')}catch(e){notice(e.message)}};
const quickItems={
 'white-tee':{name:'白色基础 T 恤',category:'上装',color_name:'白色',tags:['舒适','透气','休闲']},
 'blue-shirt':{name:'浅蓝衬衫',category:'上装',color_name:'蓝色',tags:['通勤','客户会面','透气']},
 knit:{name:'米白针织衫',category:'上装',color_name:'米白',tags:['舒适','保暖','通勤']},
 'wide-pants':{name:'黑色阔腿裤',category:'下装',color_name:'黑色',tags:['舒适','通勤','客户会面']},
 jeans:{name:'直筒牛仔裤',category:'下装',color_name:'蓝色',tags:['休闲','好活动']},
 sneakers:{name:'小白鞋',category:'鞋履',color_name:'白色',tags:['舒适','通勤','休闲']},
 cardigan:{name:'轻薄开衫',category:'外套',color_name:'米白',tags:['舒适','通勤','空调房']},
 blazer:{name:'通勤西装外套',category:'外套',color_name:'黑色',tags:['通勤','客户会面','成熟风']}
};
document.querySelectorAll('[data-quick-item]').forEach(button=>button.onclick=async()=>{
 const item=quickItems[button.dataset.quickItem]; if(!item)return;
 button.disabled=true; $('#quick-add-status').textContent='正在加入“'+item.name+'”…';
 try{await api('wardrobe',item);$('#quick-add-status').textContent='已加入“'+item.name+'”。可以继续点其他常穿单品。';await view('closet');notice(item.name+' 已加入衣橱')}catch(error){$('#quick-add-status').textContent=error.message;notice(error.message)}finally{button.disabled=false}
});
generate().catch(e=>notice('连接未成功：'+e.message));

// Weather: explicit city selection or location; never substitute mock weather.
function placeName(p){return [p.name,p.region,p.country].filter((x,i,a)=>x&&a.indexOf(x)===i).join(' · ')}
async function searchPlaces(query,container,onSelect){
 container.replaceChildren(el('small','正在搜索城市…'));
 try{const places=await api('cities?q='+encodeURIComponent(query));container.replaceChildren();if(!places.length){container.append(el('small','没有找到城市，请尝试其他中文或英文名称'));return}
 for(const p of places){const b=el('button',placeName(p));b.type='button';b.onclick=()=>{container.replaceChildren();onSelect(p)};container.append(b)}}catch(e){container.replaceChildren(el('small',e.message))}
}
function renderWeather(w,place){const n=el('div');n.append(el('strong',place+' · '+w.weather+' · '+w.temperature+'℃'),el('small',w.date+' ｜ '+w.low+'～'+w.high+'℃ ｜ 降水概率 '+(w.rain_probability??'—')+'%'),el('small',w.mode+' · '+w.timezone),el('small','查询时间：'+new Date(w.fetched_at).toLocaleString('zh-CN')));const a=el('a','天气来源 Open-Meteo');a.href=w.source_url;a.target='_blank';a.rel='noopener';n.append(a);return n}
async function selectWeather(p){
 const box=$('#weather-report');box.textContent='正在获取 '+placeName(p)+' 的天气…';$('#refresh-weather').hidden=true;weatherInfo=null;$('#weather-mode').textContent='查询中，尚未使用真实天气';
 try{const w=await api('weather?lat='+p.latitude+'&lon='+p.longitude);weatherPlace=p;weatherInfo={...w,place:placeName(p)};$('#temperature').value=w.temperature;$('#weather').value=w.weather;$('#city-query').value=p.name;box.replaceChildren(renderWeather(w,placeName(p)));$('#weather-mode').textContent='已使用所选地点天气；修改气温或天气后会切回手动模式';$('#refresh-weather').hidden=false;try{localStorage.setItem('wearmind-city',JSON.stringify(p))}catch{};await generate().catch(e=>notice(e.message))}
 catch(e){weatherInfo=null;box.textContent=e.message;$('#weather-mode').textContent='天气获取失败，当前仍使用手动输入';notice(e.message)}
}
$('#city-search').onclick=()=>searchPlaces($('#city-query').value,$('#city-results'),p=>selectWeather(p));
$('#city-query').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();$('#city-search').click()}});
$('#refresh-weather').onclick=()=>weatherPlace&&selectWeather(weatherPlace);
for(const id of ['temperature','weather'])$('#'+id).addEventListener('input',()=>{weatherInfo=null;$('#weather-mode').textContent='已切回手动填写；上方仅保留最近查询记录'});
$('#locate').onclick=()=>{
 if(!navigator.geolocation)return notice('当前浏览器不支持定位，请选择城市');
 $('#weather-report').textContent='等待定位授权…';
 navigator.geolocation.getCurrentPosition(pos=>selectWeather({name:'当前位置',latitude:Math.round(pos.coords.latitude*100)/100,longitude:Math.round(pos.coords.longitude*100)/100}),()=>{$('#weather-report').textContent='未取得定位，可以搜索选择城市。'}, {enableHighAccuracy:false,timeout:12000,maximumAge:300000});
};
try{const remembered=JSON.parse(localStorage.getItem('wearmind-city')||'null');if(remembered&&typeof remembered.name==='string')$('#city-query').value=remembered.name}catch{}

// Photo preview is local. Only the explicit recognize action sends to OpenAI.
function clearPhoto(){photoData=null;photoColor='#c5b5a4';$('#photo').value='';$('#photo-preview').hidden=true;$('#photo-preview').removeAttribute('src');$('#clear-photo').hidden=true;$('#vision-consent').checked=false;$('#recognition-note').textContent='照片先在浏览器内预览；未点击识别，不会发送给云端。'}
$('#clear-photo').onclick=clearPhoto;
$('#photo').onchange=async()=>{
 const file=$('#photo').files[0];clearPhoto();if(!file)return;
 if(!['image/jpeg','image/png','image/webp'].includes(file.type))return notice('请选择 JPG、PNG 或 WebP 图片');
 if(file.size>15*1024*1024)return notice('照片太大，请选择小于 15 MB 的图片');
 try{const image=await createImageBitmap(file);const scale=Math.min(1,1600/Math.max(image.width,image.height));const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(image.width*scale));canvas.height=Math.max(1,Math.round(image.height*scale));const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0,canvas.width,canvas.height);image.close();photoData=canvas.toDataURL(['image/png','image/webp'].includes(file.type)?'image/png':'image/jpeg',0.85);if(photoData.length>4200000){clearPhoto();return notice('图片压缩后仍太大，请选择更小的照片')};$('#photo-preview').src=photoData;$('#photo-preview').hidden=false;$('#clear-photo').hidden=false;$('#recognition-note').textContent='照片已选择并去除原始文件元数据；尚未识别。可以识别后确认，也可以手动填写下方信息入库。'}catch(e){clearPhoto();notice('无法读取照片，请换一张清晰图片')}
};
async function visionStatus(){const s=await api('vision/status');$('#vision-status').textContent=s.cloud_disabled?'开发板本地版：云端识别已关闭，本地视觉模型待接入':s.configured?'图片识别已配置 · OpenAI / '+s.model:'图片识别尚未启用：需填写 OpenAI API Key。照片仍可手动入库。';$('#vision-model').value=s.model;return s}
$('#configure-vision').onclick=async()=>{try{await api('vision/config',{key:$('#vision-key').value,model:$('#vision-model').value});$('#vision-key').value='';await visionStatus();notice('本次会话已配置，尚未发送照片')}catch(e){notice(e.message)}};
$('#recognize').onclick=async()=>{
 if(!photoData)return notice('请先选择衣物照片');if(!$('#vision-consent').checked)return notice('请先确认将本次照片发送给 OpenAI');
 const submittedPhoto=photoData;const b=$('#recognize');b.disabled=true;$('#recognition-note').textContent='正在识别，请稍候…';
 try{const r=await api('vision/recognize',{image:submittedPhoto,consent:true});if(photoData!==submittedPhoto){notice('照片已改变，请重新识别当前照片');return;}$('#name').value=r.name;$('#category').value=r.category;photoColor=r.color;for(const o of $('#tags').options)o.selected=r.tags.includes(o.value);$('#recognition-note').textContent='识别完成，尚未入库。'+r.notes+' 请检查下方名称、分类和标签，再点击“确认并加入衣橱”。'}catch(e){$('#recognition-note').textContent=e.message+'。你仍可手动填写并入库。';notice(e.message)}finally{b.disabled=false}
};
visionStatus().catch(e=>$('#vision-status').textContent=e.message);

// Travel itinerary: user-defined stops and dates, weather-based daily outfits.
let stopId=0;
function localDate(){const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-')}
function addStop(){
 const id=++stopId,row=el('section',null,'trip-stop');row.dataset.stop=id;
 const dateLabel=el('label','日期'),date=el('input');date.type='date';date.value=localDate();date.className='stop-date';dateLabel.append(date);
 const cityLabel=el('label','目的地'),input=el('input');input.placeholder='输入城市名';input.className='stop-city';cityLabel.append(input);
 const sceneLabel=el('label','当天场景'),scene=el('select');scene.className='stop-scene';for(const value of ['休闲','通勤','客户会面','运动','约会']){const o=el('option',value);scene.append(o)}sceneLabel.append(scene);const envLabel=el('label','目的地环境'),env=el('select');env.className='stop-environment';for(const value of ['室内为主','户外步行','海边','山地'])env.append(el('option',value));envLabel.append(env);const search=el('button','选择城市'),results=el('div',null,'city-results'),selected=el('small','尚未选择目的地');search.type='button';search.onclick=()=>searchPlaces(input.value,results,p=>{row.place=p;input.value=p.name;selected.textContent='已选择：'+placeName(p)});
 input.oninput=()=>{row.place=null;selected.textContent='城市已修改，请重新选择搜索结果'};
 const remove=el('button','移除');remove.type='button';remove.onclick=()=>row.remove();row.append(dateLabel,cityLabel,sceneLabel,envLabel,search,remove,results,selected);$('#trip-stops').append(row);
}
$('#add-stop').onclick=addStop;addStop();
$('#plan-trip').onclick=async()=>{
 const rows=[...document.querySelectorAll('.trip-stop')];if(!rows.length)return notice('请先添加一站行程');if(rows.length>10)return notice('每次最多规划 10 站');if(rows.some(r=>!r.place||!r.querySelector('.stop-date').value))return notice('请为每一站选择城市搜索结果和日期');
 const button=$('#plan-trip');button.disabled=true;const dest=$('#trip-result');dest.replaceChildren();const packing=new Map();let completed=0;
 try{for(const row of rows){const p=row.place,date=row.querySelector('.stop-date').value,n=el('article',null,'panel trip-day');n.append(el('h2',date+' · '+placeName(p)));dest.append(n);
 try{const w=await api('weather?lat='+p.latitude+'&lon='+p.longitude+'&date='+date);n.append(renderWeather(w,placeName(p)));const result=await api('recommend',{state:$('#trip-state').value,scene:row.querySelector('.stop-scene').value,environment:row.querySelector('.stop-environment').value,destination:placeName(p),destination_weather:{...w,place:placeName(p)},temperature:w.temperature,weather:w.weather,weather_info:{...w,place:placeName(p)},preferred_colors:selectedColors('trip-colors')});const clothes=el('div',null,'outfit');clothes.append(...result.outfit.map(i=>card(i)));n.append(clothes);const reasons=el('ul');reasons.append(...result.reasons.map(r=>el('li',r)));n.append(reasons);const needs=el('div');renderNeeds(result,needs);n.append(needs);for(const item of result.outfit)packing.set(item.id,item.name);completed++}catch(e){n.append(el('p',e.message+'；该站暂未生成穿搭。'))}}
 if(completed){const pack=el('section',null,'panel packing');pack.append(el('h2','旅行打包清单'),el('p',[...packing.values()].join(' · ')),el('small','已汇总 '+completed+' 站成功查询的单品并去重；请按天数补充换洗衣物。'));dest.append(pack)}
 }finally{button.disabled=false}
};

// Explicit destination and palette are carried into recommendations and saved history.
const palette={'米白':'#e8dfca','白色':'#f4f3ee','黑色':'#33353a','灰色':'#a1a49e','蓝色':'#718eaf','绿色':'#7e9c7c','棕色':'#94765e','红色':'#bd655f','粉色':'#d6a7b6','紫色':'#9c88b7','黄色':'#d9c27d','橙色':'#d39964'};
for(const [name,color] of Object.entries(palette)){
 for(const target of ['preferred-colors','trip-colors']){const label=el('label',null,'color-choice'),input=el('input'),swatch=el('span',null,'swatch');input.type='checkbox';input.value=name;swatch.style.background=color;label.append(input,swatch,document.createTextNode(name));input.onchange=()=>{if(selectedColors(target).length>3){input.checked=false;notice('最多选择三种期望颜色')}};$('#'+target).append(label)}
 const o=el('option',name);o.value=name;$('#avoided-colors').append(o);const itemOption=el('option',name);itemOption.value=name;$('#item-color').append(itemOption);
}
$('#destination-date').value=localDate();
let destinationRequest=0;
async function fetchDestination(p){
 const request=++destinationRequest;destinationWeather=null;$('#destination-weather').textContent='正在查询目的地对应日期的天气…';
 try{const day=$('#destination-date').value;if(!day)throw Error('请选择到达日期');const w=await api('weather?lat='+p.latitude+'&lon='+p.longitude+'&date='+day);if(request!==destinationRequest)return;destinationWeather={...w,place:placeName(p)};$('#destination-weather').replaceChildren(renderWeather(w,placeName(p)));await generate().catch(e=>notice(e.message))}
 catch(e){if(request!==destinationRequest)return;destinationWeather=null;$('#destination-weather').textContent=e.message+'；不会用出发地天气代替目的地天气。';notice(e.message)}
}
$('#destination-search').onclick=()=>searchPlaces($('#destination-query').value,$('#destination-results'),p=>{destinationPlace=p;$('#destination-query').value=p.name;fetchDestination(p)});
$('#destination-query').addEventListener('input',()=>{destinationRequest++;destinationPlace=null;destinationWeather=null;$('#destination-weather').textContent=$('#destination-query').value.trim()?'城市已修改，请重新选择目的地并查询天气。':'未选择目的地，使用上方天气。'});
$('#destination-query').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();$('#destination-search').click()}});
$('#destination-date').onchange=()=>{destinationWeather=null;if(destinationPlace)fetchDestination(destinationPlace)};
function renderNeeds(result,container){
 container.replaceChildren();if(!result.unmet_colors?.length)return;
 const box=el('div',null,'color-gap');box.append(el('strong','期望颜色暂未全部满足'),el('p','本套未覆盖：'+result.unmet_colors.join('、')+'。可减少期望色、重新换搭，或先记入补购愿望清单。'));
 const change=el('button','重新选择配色');change.type='button';change.onclick=()=>{const field=container.closest('.trip-day')?$('#trip-colors'):$('#preferred-colors');field.scrollIntoView({behavior:'smooth',block:'center'})};
 const wish=el('button','加入补购愿望');wish.type='button';wish.onclick=()=>{try{const stored=JSON.parse(localStorage.getItem('wearmind-wishlist')||'[]');const list=Array.isArray(stored)?stored:[];for(const color of result.unmet_colors)if(!list.some(x=>x.color===color))list.push({color,reason:'期望配色未在本次搭配中满足',created_at:new Date().toISOString()});localStorage.setItem('wearmind-wishlist',JSON.stringify(list));renderWishlist();notice('已记入本机补购愿望，可在我的衣橱查看')}catch{notice('无法保存愿望，请检查浏览器存储权限')}};box.append(change,wish);container.append(box)
}

function renderWishlist(){try{const data=JSON.parse(localStorage.getItem('wearmind-wishlist')||'[]');const list=Array.isArray(data)?data:[];$('#wishlist').replaceChildren(...(list.length?list.map(x=>el('p',String(x.color)+' · '+String(x.reason))):[el('p','还没有补购愿望，先看看已有衣物能否满足。')]))}catch{$('#wishlist').textContent='暂时无法读取本机补购愿望'}}
