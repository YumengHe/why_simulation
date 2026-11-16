(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('cabinet-video')) return;
  const ns = 'http://www.w3.org/2000/svg';
  const color = { ink:'#3d423f', line:'#d4d0c6', muted:'#777269', paper:'#fefdfb', teal:'#86aca7', tealDark:'#6b9690', tealLight:'#c5d9d4', blue:'#719cbd', blueLight:'#d6e4ee', blueDark:'#4e7d9d', gold:'#dcb65c', goldLight:'#f5e9c8', accent:'#9a7422' };
  function add(parent, tag, attrs = {}, text) {
    const element = document.createElementNS(ns, tag);
    for (const [key,value] of Object.entries(attrs)) element.setAttribute(key,String(value));
    if (text !== undefined) element.textContent = text;
    parent.append(element); return element;
  }
  function line(svg,x1,y1,x2,y2,stroke=color.line,width=1.5,attrs={}) { return add(svg,'line',{x1,y1,x2,y2,stroke,'stroke-width':width,...attrs}); }
  function text(svg,x,y,value,attrs={}) { return add(svg,'text',{x,y,...attrs},value); }
  function polygon(svg,points,fill,stroke=color.line,attrs={}) { return add(svg,'polygon',{points:points.map(p=>p.join(',')).join(' '),fill,stroke,'stroke-linejoin':'round','stroke-width':1.4,...attrs}); }
  function arrow(svg,x1,y1,x2,y2,stroke) {
    line(svg,x1,y1,x2,y2,stroke,1.5);
    const angle = Math.atan2(y2-y1,x2-x1), length=7;
    polygon(svg,[[x2,y2],[x2-length*Math.cos(angle-.5),y2-length*Math.sin(angle-.5)],[x2-length*Math.cos(angle+.5),y2-length*Math.sin(angle+.5)]],stroke,stroke);
  }
  function drawSlide() {
    const cm = Number($('drawer-distance').value), svg = $('slide-scene');
    svg.replaceChildren();
    const offset = cm / 50 * 110;
    add(svg,'rect',{x:30,y:53,width:180,height:128,fill:color.tealLight,stroke:color.tealDark,'stroke-width':2});
    add(svg,'rect',{x:41,y:66,width:158,height:102,fill:color.paper,stroke:color.line});
    add(svg,'rect',{x:48,y:79,width:146,height:74,fill:'none',stroke:color.blue,'stroke-dasharray':'4 4'});
    add(svg,'rect',{x:48+offset,y:79,width:146,height:74,fill:color.blueLight,stroke:color.blueDark,'stroke-width':2});
    add(svg,'rect',{x:188+offset,y:75,width:12,height:82,fill:color.blue,stroke:color.blueDark,'stroke-width':1.5});
    line(svg,207+offset,103,207+offset,129,color.blueDark,4,{'stroke-linecap':'round'});
    line(svg,195,174,195,209,color.line,1,{'stroke-dasharray':'3 3'});
    line(svg,195+offset,174,195+offset,209,color.line,1);
    if (offset>3) arrow(svg,195,199,195+offset,199,color.blueDark);
    text(svg,30,30,'Side view');
    text(svg,45,218,'Fixed body');
    $('drawer-value').value = `${cm} cm`;
    $('drawer-distance').setAttribute('aria-valuetext',`${cm} centimeters`);
    svg.setAttribute('aria-label',`Side view: drawer is ${cm} centimeters open; cabinet body stays fixed.`);
  }
  function drawHinge() {
    const degrees = Number($('door-angle').value), svg = $('hinge-scene');
    svg.replaceChildren();
    const angle=degrees*Math.PI/180, cx=75,cy=65,length=150;
    add(svg,'rect',{x:61,y:51,width:195,height:14,fill:color.tealLight,stroke:color.tealDark});
    line(svg,cx,cy,cx+length,cy,color.line,2,{'stroke-dasharray':'5 4'});
    if(degrees>0) {
      const r=53, endX=cx+r*Math.cos(angle),endY=cy+r*Math.sin(angle);
      add(svg,'path',{d:`M${cx} ${cy} L${cx+r} ${cy} A${r} ${r} 0 0 1 ${endX} ${endY} Z`,fill:color.goldLight,stroke:'none'});
      add(svg,'path',{d:`M${cx+r} ${cy} A${r} ${r} 0 0 1 ${endX} ${endY}`,fill:'none',stroke:color.accent,'stroke-width':1.5});
    }
    const ex=cx+length*Math.cos(angle),ey=cy+length*Math.sin(angle), dx=4*Math.sin(angle),dy=-4*Math.cos(angle);
    polygon(svg,[[cx+dx,cy+dy],[ex+dx,ey+dy],[ex-dx,ey-dy],[cx-dx,cy-dy]],color.gold,color.accent,{'stroke-width':1.5});
    add(svg,'circle',{cx,cy,r:5.5,fill:color.ink,stroke:color.paper,'stroke-width':1.5});
    line(svg,cx-8,cy-3,43,45,color.muted,1);
    text(svg,18,38,'Hinge');
    text(svg,290,30,'Top view',{'text-anchor':'end'});
    text(svg,266,82,'0°');
    $('door-value').value = `${degrees}°`;
    $('door-angle').setAttribute('aria-valuetext',`${degrees} degrees`);
    svg.setAttribute('aria-label',`Top view: door is ${degrees} degrees open about the fixed hinge.`);
  }
  $('drawer-distance').addEventListener('input',drawSlide);
  $('door-angle').addEventListener('input',drawHinge);
  drawSlide(); drawHinge();

  const state = {part:'drawer', position:.3};
  let frame = 0, playing = false;
  const descriptions = {
    body:'Stays fixed in this example. The door and drawer connect to it.',
    drawer:'Slides relative to the body. The latch comes along because it is attached to the drawer.',
    door:'Rotates around its hinge on the body. The drawer and latch stay in place.',
    latch:'Turns relative to the drawer. It also travels with the drawer whenever the drawer slides.'
  };
  function drawCabinet() {
    const svg=$('tree-cabinet'); svg.replaceChildren();
    const scale=86, ox=77, base=266;
    const p=(u,v,z)=>[ox+scale*(u+.65*v),base-scale*(z-.32*v)];
    const opening=state.part==='drawer' ? state.position*.95 : .3;
    const angle=(state.part==='door' ? state.position*75 : 20)*Math.PI/180;
    function face(points,fill,part,stroke=color.tealDark) {
      return polygon(svg,points.map(v=>p(...v)),fill,state.part===part ? color.accent : stroke,{'stroke-width':state.part===part ? 2.4 : 1.2});
    }
    add(svg,'ellipse',{cx:202,cy:284,rx:124,ry:9,fill:'#e8e5de',opacity:.45});
    face([[0,0,0],[0,-.7,0],[0,-.7,2.4],[0,0,2.4]],color.tealDark,'body');
    face([[0,0,2.4],[0,-.7,2.4],[2.4,-.7,2.4],[2.4,0,2.4]],color.tealLight,'body');
    face([[0,0,0],[2.4,0,0],[2.4,0,2.4],[0,0,2.4]],color.teal,'body');
    face([[.13,.01,.14],[2.27,.01,.14],[2.27,.01,1.5],[.13,.01,1.5]],'#dce8e2','body');
    face([[.13,.01,1.65],[2.27,.01,1.65],[2.27,.01,2.18],[.13,.01,2.18]],'#dce8e2','body');
    const du=2.1*Math.cos(angle), dv=2.1*Math.sin(angle);
    face([[.14,.03,.15],[.14+du,dv+.03,.15],[.14+du,dv+.03,1.49],[.14,.03,1.49]],color.gold,'door',color.accent);
    const handle=p(.14+du*.91,.03+dv*.91,.8);
    line(svg,handle[0],handle[1]-7,handle[0],handle[1]+7,color.accent,3,{'stroke-linecap':'round'});
    for(const z of [.42,1.22]) { const hp=p(.14,.03,z);add(svg,'rect',{x:hp[0]-2,y:hp[1]-5,width:4,height:10,rx:1,fill:color.accent}); }
    face([[.14,opening-.6,2.17],[2.26,opening-.6,2.17],[2.26,opening,2.17],[.14,opening,2.17]],color.blueLight,'drawer',color.blueDark);
    face([[2.26,opening-.6,1.65],[2.26,opening,1.65],[2.26,opening,2.17],[2.26,opening-.6,2.17]],color.blueDark,'drawer',color.blueDark);
    face([[.14,opening,1.65],[2.26,opening,1.65],[2.26,opening,2.17],[.14,opening,2.17]],color.blue,'drawer',color.blueDark);
    const lp=p(1.19,opening+.02,1.9), la=(state.part==='latch' ? state.position*90 : 0)*Math.PI/180;
    add(svg,'circle',{cx:lp[0],cy:lp[1],r:10,fill:color.paper,stroke:state.part==='latch'?color.accent:color.blueDark,'stroke-width':2});
    line(svg,lp[0]-12*Math.cos(la),lp[1]-12*Math.sin(la),lp[0]+12*Math.cos(la),lp[1]+12*Math.sin(la),state.part==='latch'?color.accent:color.ink,4,{'stroke-linecap':'round'});
    line(svg,...p(.2,0,0),...p(.2,0,-.12),color.tealDark,5);
    line(svg,...p(2.2,0,0),...p(2.2,0,-.12),color.tealDark,5);
  }
  function updateTree() {
    drawCabinet();
    document.querySelectorAll('.tree-node').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.part===state.part)));
    document.querySelectorAll('.tree-edge').forEach(edge=>edge.classList.toggle('is-selected',edge.dataset.edge===state.part));
    const strong=document.createElement('strong'); strong.textContent=state.part[0].toUpperCase()+state.part.slice(1)+'. ';
    $('part-description').replaceChildren(strong,document.createTextNode(descriptions[state.part]));
    $('play-part').disabled=state.part==='body';
    $('play-part').textContent=state.part==='body'?'Body stays fixed':playing?'Pause motion':`Play ${state.part} motion`;
    $('part-position').disabled=state.part==='body';
    $('part-position').value=String(Math.round(state.position*100));
    $('part-position').setAttribute('aria-valuetext',`${Math.round(state.position*100)} percent of the illustrated motion`);
  }
  function stop() { cancelAnimationFrame(frame); frame=0;playing=false; }
  document.querySelectorAll('.tree-node').forEach(button=>button.addEventListener('click',()=>{stop();state.part=button.dataset.part;state.position=.3;updateTree();}));
  $('part-position').addEventListener('input',()=>{stop();state.position=Number($('part-position').value)/100;updateTree();});
  $('reset-part').addEventListener('click',()=>{stop();state.position=0;updateTree();});
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  $('play-part').addEventListener('click',()=>{
    if(playing) {stop();updateTree();return;}
    if(reduced.matches) {state.position=state.position<.5?1:0;updateTree();return;}
    playing=true;
    const start=performance.now(), initial=state.position;
    updateTree();
    function tick(now) {
      const t=Math.min((now-start)/3600,1);
      state.position=t<.5 ? initial+(1-initial)*(1-Math.cos(2*Math.PI*t))/2 : (1+Math.cos(2*Math.PI*(t-.5)))/2;
      drawCabinet();
      $('part-position').value=String(Math.round(state.position*100));
      if(t<1) frame=requestAnimationFrame(tick); else {stop();updateTree();}
    }
    frame=requestAnimationFrame(tick);
  });
  updateTree();

  const video=$('cabinet-video');
  let videoVisible=video.getBoundingClientRect().bottom>0 && video.getBoundingClientRect().top<innerHeight;
  function updatePlayback() {
    if(videoVisible && !document.hidden && !reduced.matches) video.play().catch(()=>{});
    else video.pause();
  }
  reduced.addEventListener('change',()=>{updatePlayback();if(reduced.matches){stop();updateTree();}});
  document.addEventListener('visibilitychange',()=>{updatePlayback();if(document.hidden){stop();updateTree();}});
  if('IntersectionObserver' in window) {
    new IntersectionObserver(entries=>{videoVisible=entries[0].isIntersecting;updatePlayback();},{threshold:.1}).observe(video);
    new IntersectionObserver(entries=>{if(!entries[0].isIntersecting && playing){stop();updateTree();}},{threshold:.1}).observe($('tree-demo'));
  }
  updatePlayback();
})();
