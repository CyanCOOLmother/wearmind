/* Lightweight wardrobe setup: every item is user-confirmed, never auto-recognised. */
(()=>{
  const presets=[
    {name:'米白针织衫',category:'上装',color_name:'米白',tags:['舒适','通勤','保暖','不卡腰']},
    {name:'浅蓝衬衫',category:'上装',color_name:'蓝色',tags:['通勤','客户会面','透气','抗皱']},
    {name:'黑色直筒裤',category:'下装',color_name:'黑色',tags:['舒适','通勤','客户会面','不卡腰']},
    {name:'牛仔裤',category:'下装',color_name:'蓝色',tags:['休闲','好活动']},
    {name:'薄外套',category:'外套',color_name:'米白',tags:['通勤','空调房','抗皱']},
    {name:'连衣裙',category:'上装',color_name:'粉色',tags:['约会','温柔风','舒适']},
    {name:'平底小白鞋',category:'鞋履',color_name:'白色',tags:['舒适','通勤','好活动']}
  ];
  const needs=['遮手臂','不卡腰','好活动','耐脏','抗皱','空调房','显高'];
  window.wearmindNeeds=window.wearmindNeeds||[];

  const style=document.createElement('style');
  style.textContent=`.wardrobe-start{margin:18px 0;padding:18px;border:1px solid #d3c9bb;border-radius:18px;background:#fffaf1}.wardrobe-start h3{margin:0 0 6px;font-size:17px}.wardrobe-start p{font-size:13px;line-height:1.6}.wardrobe-start button{margin-right:8px}.need-chips{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.need-chips button[aria-pressed=true]{background:#254bff;color:#fff;border-color:#254bff}.wardrobe-dialog{border:0;border-radius:20px;max-width:520px;padding:22px;box-shadow:0 16px 60px #0005}.wardrobe-dialog::backdrop{background:#12152788}.preset-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0}.preset-grid label{padding:10px;border:1px solid #ddd4c7;border-radius:12px;font-size:14px}.preset-grid input{margin-right:8px}.wardrobe-dialog .row{margin-top:14px}`;
  document.head.append(style);

  const upload=document.querySelector('.upload');
  if(!upload)return;
  const box=document.createElement('section');
  box.className='wardrobe-start';
  box.innerHTML='<h3>先从你真的有的衣服开始</h3><p>不用一件件拍照。先勾选常穿基础款，衣伴只把你确认拥有的单品放进衣柜；以后再补实物图和细节。</p><button type="button" class="blue" id="quick-closet">30 秒起步衣柜</button><button type="button" id="restyle-old">把旧衣重新穿起来</button><div class="need-chips" id="need-chips"></div><p class="small" id="needs-note">可选你的真实限制：会优先影响之后的筛选。</p>';
  upload.insertAdjacentElement('afterend',box);

  const chips=box.querySelector('#need-chips');
  const renderNeeds=()=>{
    chips.replaceChildren();
    needs.forEach(need=>{
      const b=document.createElement('button'); b.type='button'; b.textContent=need;
      b.setAttribute('aria-pressed',window.wearmindNeeds.includes(need));
      b.onclick=()=>{
        window.wearmindNeeds=window.wearmindNeeds.includes(need)
          ?window.wearmindNeeds.filter(x=>x!==need)
          :[...window.wearmindNeeds,need];
        box.querySelector('#needs-note').textContent=window.wearmindNeeds.length
          ?'已纳入：'+window.wearmindNeeds.join('、')+'。点击“帮我搭一套”即可生效。'
          :'可选你的真实限制：会优先影响之后的筛选。';
        renderNeeds();
      };
      chips.append(b);
    });
  };
  renderNeeds();

  const dialog=document.createElement('dialog');
  dialog.className='wardrobe-dialog';
  dialog.innerHTML='<h2>30 秒建立起步衣柜</h2><p>只选择你现实中确实拥有的衣服。它们不是图片识别结果，可以随时增删。</p><form method="dialog" id="quick-form"><div class="preset-grid"></div><div class="row"><button value="cancel">先不加</button><button class="blue" value="confirm">确认加入衣柜</button></div></form>';
  document.body.append(dialog);
  const grid=dialog.querySelector('.preset-grid');
  presets.forEach((item,index)=>{
    const label=document.createElement('label');
    label.innerHTML='<input type="checkbox" value="'+index+'">'+item.name;
    grid.append(label);
  });
  box.querySelector('#quick-closet').onclick=()=>dialog.showModal();
  dialog.querySelector('#quick-form').addEventListener('submit',async event=>{
    if(event.submitter?.value!=='confirm')return;
    event.preventDefault();
    const selected=[...grid.querySelectorAll('input:checked')].map(input=>presets[Number(input.value)]);
    if(!selected.length){notice('至少选一件你真实拥有的衣服');return;}
    const confirm=event.submitter; confirm.disabled=true;
    try{
      const existing=await api('wardrobe'); const names=new Set(existing.map(item=>item.name));
      for(const item of selected)if(!names.has(item.name))await api('wardrobe',item);
      dialog.close(); notice('已加入 '+selected.length+' 件确认拥有的衣服；现在可以直接搭一套。');
    }catch(error){notice(error.message)}finally{confirm.disabled=false}
  });

  const restyle=document.createElement('dialog');
  restyle.className='wardrobe-dialog';
  restyle.innerHTML='<h2>把旧衣重新穿起来</h2><p>选一件舍不得丢的衣服，衣伴会围绕它搭另一套，而不是让你购买新衣。</p><label>旧衣 <select id="old-item"></select></label><label>想穿去哪里 <select id="old-scene"><option>通勤</option><option>客户会面</option><option>休闲</option><option>约会</option></select></label><div class="row"><button value="cancel">返回</button><button class="blue" id="restyle-go">围绕它搭配</button></div>';
  document.body.append(restyle);
  box.querySelector('#restyle-old').onclick=async()=>{
    try{
      const wardrobe=await api('wardrobe'); const select=restyle.querySelector('#old-item'); select.replaceChildren();
      wardrobe.forEach(item=>{const option=document.createElement('option');option.value=item.id;option.textContent=item.name+' · '+item.category;select.append(option)});
      if(!wardrobe.length)return notice('衣柜还没有衣服，先用“30 秒起步衣柜”加几件。');
      restyle.showModal();
    }catch(error){notice(error.message)}
  };
  restyle.querySelector('#restyle-go').onclick=async()=>{
    const button=restyle.querySelector('#restyle-go'); button.disabled=true;
    try{
      const itemId=restyle.querySelector('#old-item').value;
      const scene=restyle.querySelector('#old-scene').value;
      const item=await api('wardrobe').then(list=>list.find(x=>x.id===itemId));
      if(!item)throw Error('这件衣服不存在，请重新选择');
      document.querySelector('#scene').value=scene;
      document.querySelector('#state').value='想把「'+item.name+'」重新搭配，穿去'+scene+'。';
      window.restyledItem=item.name; restyle.close();
      all=await api('wardrobe'); ctx=context();
      result=await api('recommend',{...ctx,only_uploaded:false,locked_ids:[itemId]}); draw();
      notice('已围绕「'+item.name+'」重组一套；优先使用已有衣服。');
    }catch(error){notice(error.message)}finally{button.disabled=false}
  };
})();
