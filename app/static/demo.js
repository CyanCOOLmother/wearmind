/* Home-page demo layer: works with or without the local model service. */
(()=>{
  const style=document.createElement('style');
  style.textContent=`.demo-strip{border-top:1px solid #d6d5d0;margin:22px 0;padding:15px 0}.demo-strip b{font-size:12px;letter-spacing:1px}.demo-strip button,.check-ai{font-size:12px;padding:8px 12px}.ai-ready{color:#174f27;font-weight:bold}.ai-waiting{color:#7a5c10}.ai-card{margin:14px 0;padding:18px;border-radius:18px;background:#e7ecff;border:1px solid #bdcaff}.ai-card[hidden]{display:none}.ai-card h3{margin:0 0 7px;font-size:16px}.ai-card p{font-size:13px;line-height:1.65;margin:7px 0}.ai-card .row{margin:12px 0 0}.ai-card .blue{background:#254bff;color:#fff;border-color:#254bff}`;
  document.head.append(style);

  const target=document.querySelector('#model-note');
  const controls=target?.previousElementSibling;
  if(!target||!controls)return;
  const check=document.createElement('button');
  check.type='button'; check.className='check-ai'; check.textContent='检查本机 AI';
  controls.append(check);
  const strip=document.createElement('div');
  strip.className='demo-strip';
  strip.innerHTML='<b>今天的快捷情境</b><div class="row"><button data-demo="commute">怕冷通勤</button><button data-demo="meeting">客户会面</button><button data-demo="date">蓝色约会</button><button data-demo="trip">旅行走路</button></div>';
  target.insertAdjacentElement('afterend',strip);
  const aiCard=document.createElement('section');
  aiCard.className='ai-card'; aiCard.hidden=true;
  strip.insertAdjacentElement('afterend',aiCard);

  const demos={
    commute:{text:'今天有点疲惫又怕冷，去公司通勤，想穿蓝色。',flags:['疲惫','怕冷'],scene:'通勤',colors:['蓝色'],destination:'上海 · 公司',temp:12,sky:'阴天'},
    meeting:{text:'下午去客户会面，室内为主，想穿得利落舒服。',flags:[],scene:'客户会面',colors:['米白','蓝色'],destination:'上海 · 客户办公室',temp:18,sky:'晴天'},
    date:{text:'晚上去约会，想穿蓝色，走路不多。',flags:[],scene:'约会',colors:['蓝色'],destination:'上海 · 晚餐',temp:16,sky:'晴天'},
    trip:{text:'周末旅行，要走很多路，有点怕冷。',flags:['怕冷'],scene:'休闲',colors:['绿色','米白'],destination:'杭州 · 西湖',temp:11,sky:'雨天'}
  };
  strip.querySelectorAll('[data-demo]').forEach(button=>button.onclick=async()=>{
    const d=demos[button.dataset.demo];
    document.querySelector('#state').value=d.text;
    flags=new Set(d.flags); chosen=[...d.colors];
    document.querySelector('#scene').value=d.scene;
    document.querySelector('#destination').value=d.destination;
    document.querySelector('#temperature').value=d.temp;
    document.querySelector('#sky').value=d.sky;
    liveWeather=null; renderFlags(); renderColors();
    target.textContent='已填入演示条件；正在用衣橱规则生成搭配。';
    await generate();
  });

  check.onclick=async()=>{
    check.disabled=true; target.className='small ai-waiting'; target.textContent='正在检查开发板本机模型…';
    try{
      const status=await api('local-model/status?runtime=llamacpp');
      if(!status.available)throw Error('尚未检测到 Qwen 服务');
      const model=status.selected||status.models[0];
      await api('local-model/config',{runtime:'llamacpp',model});
      target.className='small ai-ready'; target.textContent='● 本机 AI 已连接：'+model+'。你的文字只在开发板本机处理。';
    }catch(error){
      target.className='small ai-waiting'; target.textContent='● 本机 AI 尚未就绪：'+error.message+'；仍可手动选择条件与搭配。';
    }finally{check.disabled=false}
  };

  document.querySelector('#understand').onclick=async()=>{
    const input=document.querySelector('#state').value;
    if(!input.trim())return notice('先写一句今天的需求');
    const button=document.querySelector('#understand');
    button.disabled=true; aiCard.hidden=true;
    target.className='small ai-waiting'; target.textContent='本机 Qwen 正在整理你的需求…';
    try{
      const r=await api('local-model/understand',{text:input});
      const labels=r.feelings.map(x=>x.label);
      const summary=[...labels,r.scene,...r.preferred_colors].filter(Boolean);
      const impact=[];
      if(labels.includes('怕冷'))impact.push('优先保暖层');
      if(labels.includes('疲惫'))impact.push('优先舒适与不紧腰');
      if(r.scene)impact.push('按“'+r.scene+'”筛选');
      if(r.preferred_colors.length)impact.push('优先“'+r.preferred_colors.join('、')+'”配色');
      aiCard.replaceChildren();
      const title=document.createElement('h3'); title.textContent='本机 Qwen 为你整理出这些条件';
      const found=document.createElement('p'); found.textContent=summary.length?'“'+summary.join(' · ')+'”':'没有足够明确的条件，请手动补充。';
      const why=document.createElement('p'); why.textContent=impact.length?'接下来会：'+impact.join('；')+'。':'你确认后，衣伴会按当前手动条件筛选衣橱。';
      const meta=document.createElement('p'); meta.className='small'; meta.textContent='本机 '+r.model+' · '+r.elapsed_ms+' ms · 你的文字没有发送到云端';
      const actions=document.createElement('div'); actions.className='row';
      const confirm=document.createElement('button'); confirm.className='blue'; confirm.textContent='确认并直接搭一套';
      const edit=document.createElement('button'); edit.textContent='我自己修改条件';
      confirm.onclick=async()=>{
        flags=new Set(labels); chosen=[...r.preferred_colors];
        if(r.scene)document.querySelector('#scene').value=r.scene;
        renderFlags(); renderColors(); aiCard.hidden=true;
        target.className='small ai-ready'; target.textContent='● 已采用本机 AI 整理的条件，正在从衣橱为你筛选。';
        await generate(); notice('已按确认条件生成一套搭配');
      };
      edit.onclick=()=>{aiCard.hidden=true;target.className='small';target.textContent='可直接修改感受、场景和配色，再点击“帮我搭一套”。';};
      actions.append(confirm,edit); aiCard.append(title,found,why,meta,actions); aiCard.hidden=false;
      target.className='small ai-ready'; target.textContent='● 本机 Qwen 已完成整理，请确认后自动生成搭配。';
    }catch(error){
      target.className='small ai-waiting'; target.textContent='● 本机 AI 暂不可用：'+error.message+'；仍可手动选择条件。';
    }finally{button.disabled=false}
  };
})();
