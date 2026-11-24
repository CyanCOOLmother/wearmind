let bodyFlagsConfirmed=false,bodyModelSource=null,pendingBody=null;
function bodyFlags(){return [...document.querySelectorAll('#body-flags input:checked')].map(x=>x.value)}
window.edgeContext=()=>bodyFlagsConfirmed?{comfort_flags:bodyFlags(),local_understanding:bodyModelSource}:{};
function setBodyFlags(values){for(const input of document.querySelectorAll('#body-flags input'))input.checked=values.includes(input.value);bodyFlagsConfirmed=true;}
for(const input of document.querySelectorAll('#body-flags input'))input.onchange=()=>{bodyFlagsConfirmed=true;bodyModelSource=null;};
$('#state').addEventListener('input',()=>{bodyFlagsConfirmed=false;bodyModelSource=null;pendingBody=null;$('#body-preview').replaceChildren();for(const input of document.querySelectorAll('#body-flags input'))input.checked=false});
async function detectModels(){const b=$('#detect-local-model');b.disabled=true;$('#local-model-status').textContent='正在检查此设备的本机模型服务…';try{const result=await api('local-model/status?runtime='+$('#local-runtime').value);$('#local-model-status').textContent=result.message;$('#local-model-name').replaceChildren(...(result.models.length?result.models.map(name=>{const o=el('option',name);o.value=name;return o}):[el('option','未检测到本机模型')]));if(result.selected)$('#local-model-name').value=result.selected;$('#use-local-model').disabled=!result.available;$('#edge-status').textContent=result.available?'● 本机模型服务可用 · 请确认所选模型':'● 本机模型未就绪 · 可手动使用'}catch(e){notice(e.message)}finally{b.disabled=false}}
$('#detect-local-model').onclick=detectModels;
$('#local-runtime').onchange=()=>{$('#local-model-name').replaceChildren(el('option','请重新检测本机模型'));$('#use-local-model').disabled=true;$('#local-model-status').textContent='运行服务已改变，请先检测。'};
$('#use-local-model').disabled=true;
$('#use-local-model').onclick=async()=>{try{const r=await api('local-model/config',{runtime:$('#local-runtime').value,model:$('#local-model-name').value});$('#local-model-status').textContent='已选择 '+r.runtime+' / '+r.model+'；实际推理速度与 NPU 使用情况需实机测量。';$('#edge-status').textContent='● 本机模型已选择：'+r.model;notice('已保存本机模型选择')}catch(e){notice(e.message)}};
$('#understand-body').onclick=async()=>{const text=$('#state').value,b=$('#understand-body');b.disabled=true;$('#body-preview').textContent='本机模型正在整理，请稍候；你仍可手动勾选感受。';try{const r=await api('local-model/understand',{text});if($('#state').value!==text){$('#body-preview').textContent='自述已变化，请重新整理当前描述。';return;}pendingBody=r;const box=el('div',null,'body-confirm');box.append(el('strong','先确认，本机模型理解得对吗？'));const list=el('ul');list.append(...r.feelings.map(x=>el('li',x.label+'：引用“'+x.evidence+'”')));if(!r.feelings.length)list.append(el('li','未提取明确感受，请手动勾选。'));if(r.scene)list.append(el('li','场景：'+r.scene));if(r.preferred_colors.length)list.append(el('li','期望颜色：'+r.preferred_colors.join('、')));box.append(list,el('small',r.runtime+' / '+r.model+' · 本次 '+r.elapsed_ms+' ms · 不是医学判断'));const confirm=el('button','确认并使用这些条件');confirm.type='button';confirm.onclick=()=>{if($('#state').value!==text)return notice('描述已变化，请重新整理');setBodyFlags(r.feelings.map(x=>x.label));bodyModelSource={model:r.model,runtime:r.runtime};if(r.scene)$('#scene').value=r.scene;for(const input of document.querySelectorAll('#preferred-colors input'))input.checked=r.preferred_colors.includes(input.value);$('#body-preview').textContent='已确认本机模型整理的条件。现在点击下方蓝色的“直接给我一套”。';$('#context button[type=submit]').scrollIntoView({behavior:'smooth',block:'center'});};box.append(confirm);$('#body-preview').replaceChildren(box);box.scrollIntoView({behavior:'smooth',block:'center'})}catch(e){$('#body-preview').textContent=e.message+'。可直接手动勾选感受并继续搭配。'}finally{b.disabled=false}};
$('#save-body').onclick=async()=>{try{await api('body-state',{date:localDate(),text:$('#state').value,comfort_flags:bodyFlagsConfirmed?bodyFlags():null});notice('今日感受已保存在运行衣伴的这台设备上')}catch(e){notice(e.message)}};
$('#run-demo-check').onclick=async()=>{
 const button=$('#run-demo-check'), output=$('#demo-check-result');
 button.disabled=true; output.textContent='正在检查衣橱、NPU 和本机模型，请稍候…';
 try{
   const [items,npu,understanding]=await Promise.all([
     api('wardrobe'),
     api('npu-pose/status'),
     api('local-model/understand',{text:'今天通勤，想舒服一点，穿蓝色。'})
   ]);
   const npuText=npu.configured?'NPU 姿势模型已就绪':'NPU 姿势模型未就绪（不影响文字搭配）';
   const modelText=understanding.model?'本机 Qwen 理解成功':'本机文字模型未返回模型信息';
   output.replaceChildren(el('strong','自检完成 ✓'),el('p','衣橱：'+items.length+' 件已读取。'),el('p',modelText+'；用时 '+understanding.elapsed_ms+' ms。'),el('p',npuText+'。'));
 }catch(error){output.textContent='自检没有完全通过：'+error.message+'。文字搭配仍可按页面提示手动完成。'}finally{button.disabled=false}
};
Promise.all([api('device'),api('body-state')]).then(([device,history])=>{$('#device-storage').textContent=device.environment+'；'+device.storage+'；当前应用：'+device.profile;$('#edge-status').textContent=device.environment+' · 模型待检测';const last=history.find(x=>x.date===localDate());if(last){$('#state').value=last.text;if(Array.isArray(last.comfort_flags))setBodyFlags(last.comfort_flags);$('#body-preview').textContent='已恢复今天主动保存的感受，可以修改后重新保存。';generate().catch(e=>notice(e.message));}}).catch(e=>notice(e.message));

document.querySelectorAll('[data-state]').forEach(button=>button.addEventListener('click',()=>$('#state').dispatchEvent(new Event('input'))));
