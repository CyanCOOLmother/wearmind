/* Keep the editorial visual style, but make the first screen a single decision flow. */
(()=>{
  const $=selector=>document.querySelector(selector);
  const left=$('main > section:first-child');
  if(!left)return;
  const style=document.createElement('style');
  style.textContent=`
    .flow-kicker{font-size:11px;letter-spacing:2px;color:#254bff;margin:0 0 12px;font-weight:700}
    .flow-helper{font-size:14px;line-height:1.6;color:#575b62;margin:0 0 16px;max-width:34em}
    .prompt-shell{background:#fff;border:1px solid #d7d7d1;border-radius:22px;padding:8px;box-shadow:0 14px 38px #2c3e7510}
    .prompt-shell textarea{border:0;height:112px;padding:14px;background:transparent}.prompt-shell textarea:focus{outline:0}
    .quick-intents{display:flex;flex-wrap:wrap;gap:7px;margin:13px 0 4px}.quick-intents button{font-size:12px;padding:8px 12px;background:#fff;border-color:#deded8}.quick-intents button:hover{border-color:#254bff;color:#254bff}
    .condition-line{display:flex;align-items:center;gap:10px;margin:20px 0 4px}.condition-line b{font-size:12px;white-space:nowrap}.condition-line span{font-size:12px;color:#74777b}
    .decision-row{display:grid;grid-template-columns:1fr auto;gap:9px;align-items:center;margin:12px 0 6px}.decision-row select{height:48px;border-radius:15px}.decision-row button{height:48px;white-space:nowrap;padding:0 15px}
    .primary-copy{margin:13px 0 4px;font-size:12px;text-align:center;color:#676b6f}.flow-more{margin:18px 0 0;border-top:1px solid #ddd;padding-top:16px}.flow-more summary{font-size:13px;font-weight:600}.flow-more .small{margin-top:10px}
    .closet-drawer{margin-top:16px;border:1px solid #dedcd5;border-radius:16px;padding:0 15px;background:#fbfaf6}.closet-drawer summary{padding:15px 0;font-size:13px;font-weight:600;cursor:pointer}.closet-drawer .upload{margin:0 0 14px;padding:16px;border-radius:15px}.closet-drawer .wardrobe-start{margin:0 0 14px;border:0;border-top:1px solid #dedcd5;border-radius:0;padding:16px 0;background:transparent}.closet-drawer .wardrobe-start h3{font-size:14px}.closet-drawer .wardrobe-start p{margin:5px 0 12px}
    .wardrobe-start .need-chips,.wardrobe-start #needs-note{display:none}.demo-strip{border-top:0!important;margin:14px 0 0!important;padding:0!important}.demo-strip b{font-size:11px!important;color:#777}.demo-strip .row{margin:8px 0!important}.demo-strip button{padding:7px 10px!important}.ai-card{margin:13px 0!important}
    .right h2{max-width:13em}.empty{min-height:270px;display:grid;place-content:center}.wide{border-radius:16px}.wide:after{content:' · 从已有衣服开始';font-size:12px;font-weight:400;opacity:.82}.progress-note{font-size:12px;color:#656961;text-align:center;margin:0 0 15px}.progress-note strong{color:#254bff}
    main>section>details:last-of-type{display:none}@media(max-width:850px){.decision-row{grid-template-columns:1fr}.decision-row button{width:100%}.right{margin-top:10px}.prompt-shell textarea{height:96px}}
  `;
  document.head.append(style);

  const heading=left.querySelector('h1');
  const state=$('#state');
  heading.insertAdjacentHTML('beforebegin','<p class="flow-kicker">TODAY · YOUR REAL LIFE</p>');
  heading.insertAdjacentHTML('afterend','<p class="flow-helper">不用整理完整衣柜。说一句今天的状态，衣伴会先理解你的需要，再优先用已有衣服搭一套。</p>');
  state.placeholder='例如：今天有点累、怕冷，下午见客户，晚上接娃，想穿蓝色。';
  const shell=document.createElement('div'); shell.className='prompt-shell';
  state.parentNode.insertBefore(shell,state); shell.append(state);
  const intents=document.createElement('div'); intents.className='quick-intents';
  intents.innerHTML='<button type="button" data-text="今天有点怕冷，要去公司通勤。">怕冷上班</button><button type="button" data-text="下午见客户，想得体但不要太累。">见客户</button><button type="button" data-text="要接送孩子，也要上班，想穿方便活动的。">带娃上班</button><button type="button" data-text="晚上约会，想穿得温柔一点。">约会出片</button>';
  shell.insertAdjacentElement('afterend',intents);
  intents.querySelectorAll('button').forEach(button=>button.onclick=()=>{state.value=button.dataset.text;state.focus();});

  const flags=$('#flags');
  const flagLine=document.createElement('div');flagLine.className='condition-line';flagLine.innerHTML='<b>今天身体感觉</b><span>可不选，选了会影响搭配</span>';
  flags.parentNode.insertBefore(flagLine,flags);
  const sceneRow=$('#scene').parentElement;
  sceneRow.classList.add('decision-row');
  const generate=$('#generate');
  generate.insertAdjacentHTML('afterend','<p class="primary-copy">不会自动购物；先给你一套可穿的，再判断是否真的缺。</p>');

  // Put colour, weather and upload flows behind a calm disclosure, without removing them.
  const originalMore=[...left.querySelectorAll('details')].find(node=>node.querySelector('#destination'));
  if(originalMore){
    originalMore.classList.add('flow-more');
    originalMore.querySelector('summary').textContent='补充条件：目的地、天气、配色与衣橱方式';
    const colorLabel=[...left.querySelectorAll('label')].find(label=>label.textContent.trim().startsWith('想要的配色'));
    if(colorLabel){
      originalMore.append(colorLabel,$('#colors'),$('#color-note'));
    }
  }

  // The wardrobe setup is useful, but it should never block the first recommendation.
  const upload=$('.upload');
  const wardrobeStart=$('.wardrobe-start');
  if(upload){
    const drawer=document.createElement('details');drawer.className='closet-drawer';
    drawer.innerHTML='<summary>衣柜与旧衣 · 有空再慢慢补充</summary>';
    generate.parentElement.insertBefore(drawer,generate.nextElementSibling?.nextElementSibling||null);
    drawer.append(upload);
    if(wardrobeStart){
      const chips=wardrobeStart.querySelector('#need-chips');const note=wardrobeStart.querySelector('#needs-note');
      if(chips&&note){
        const fit=document.createElement('section');fit.className='fit-needs';
        fit.innerHTML='<div class="condition-line"><b>穿衣限制</b><span>衣伴会优先避开不舒服的选择</span></div>';
        flags.insertAdjacentElement('afterend',fit);fit.append(chips,note);
      }
      drawer.append(wardrobeStart);
    }
  }
  const resultIntro=$('.right .canvas');
  if(resultIntro)resultIntro.insertAdjacentHTML('beforebegin','<p class="progress-note"><strong>01</strong> 告诉衣伴今天的状态　·　<strong>02</strong> 直接得到一套</p>');
  const roadmap=[...document.querySelectorAll('body > details')].find(node=>node.textContent.includes('开发进度'));
  if(roadmap)roadmap.remove();
  const footer=document.querySelector('footer');
  if(footer)footer.textContent='衣伴 · 先理解你，再使用已有衣服。衣柜与身体感受只保存在当前设备。';
})();
