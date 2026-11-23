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
    const offset = cm / 76 * 110;
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
    drawer:'Slides relative to the body. Its fixed handle moves with the drawer.',
    door:'Rotates around its hinge on the body. Its fixed handle moves with the door; the drawer stays in place.'
  };
  let cabinetGeometry = null;
  const dot = (a,b) => a.reduce((v,x,i)=>v+x*b[i],0);
  const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const normalize = a => { const n=Math.hypot(...a); return a.map(x=>x/n); };
  function drawCabinet() {
    if (!cabinetGeometry) return;
    const canvas=$('tree-cabinet'), ctx=canvas.getContext('2d'), w=canvas.width,h=canvas.height;
    const pixels=ctx.createImageData(w,h), depths=new Float32Array(w*h).fill(-Infinity);
    for(let i=0;i<w*h;i++) pixels.data.set([254,253,251,255],4*i);
    const eye=normalize([3,-6,2.6]), right=normalize(cross([0,0,1],eye)), up=cross(eye,right), light=normalize([-3,-5,7]);
    const opening=state.part==='drawer'?state.position*cabinetGeometry.drawer_limit:.24;
    const angle=-(state.part==='door'?state.position*90:24)*Math.PI/180;
    const hinge=cabinetGeometry.door_hinge, c=Math.cos(angle), sn=Math.sin(angle);
    const pose=(p,group)=>{
      if(group==='drawer')return [p[0],p[1]-opening,p[2]];
      if(group==='door'){const x=p[0]-hinge[0],y=p[1]-hinge[1];return [hinge[0]+c*x-sn*y,hinge[1]+sn*x+c*y,p[2]];}
      return p;
    };
    cabinetGeometry.triangles.forEach((triangle,i)=>{
      const tri=triangle.map(p=>pose(p,cabinetGeometry.groups[i]));
      const normal=normalize(cross(tri[1].map((x,k)=>x-tri[0][k]),tri[2].map((x,k)=>x-tri[0][k])));
      if(dot(normal,eye)<=0)return;
      const xy=tri.map(p=>{const q=[p[0],p[1]+.2,p[2]];return [w/2+250*dot(q,right),h/2-250*dot(q,up)];});
      const z=tri.map(p=>dot(p,eye)),[a,b,d]=xy;
      const den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1]);
      if(Math.abs(den)<1e-8)return;
      const x0=Math.max(0,Math.floor(Math.min(...xy.map(p=>p[0])))), x1=Math.min(w-1,Math.ceil(Math.max(...xy.map(p=>p[0]))));
      const y0=Math.max(0,Math.floor(Math.min(...xy.map(p=>p[1])))), y1=Math.min(h-1,Math.ceil(Math.max(...xy.map(p=>p[1]))));
      const shade=.65+.35*Math.max(0,dot(normal,light)), col=cabinetGeometry.colors[i].map(v=>v*shade);
      for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
        const wa=((b[1]-d[1])*(x+.5-d[0])+(d[0]-b[0])*(y+.5-d[1]))/den;
        const wb=((d[1]-a[1])*(x+.5-d[0])+(a[0]-d[0])*(y+.5-d[1]))/den,wc=1-wa-wb;
        if(wa<0||wb<0||wc<0)continue;
        const depth=wa*z[0]+wb*z[1]+wc*z[2], j=y*w+x;
        if(depth<=depths[j])continue;
        depths[j]=depth;pixels.data.set([...col,255],4*j);
      }
    });
    ctx.putImageData(pixels,0,0);
    canvas.setAttribute('aria-label',`Shared cabinet: drawer ${Math.round(opening*100)} cm open; door ${Math.round(-angle*180/Math.PI)} degrees open. Both handles are fixed.`);
  }
  fetch('assets/cabinet-model/geometry.json').then(response=>{if(!response.ok)throw new Error('Cabinet geometry unavailable');return response.json();}).then(model=>{cabinetGeometry=model;drawCabinet();}).catch(()=>{
    const ctx=$('tree-cabinet').getContext('2d');ctx.font='24px sans-serif';ctx.fillText('Cabinet preview could not load. Please reload.',20,150);
  });
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
