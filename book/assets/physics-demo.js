(() => {
  'use strict';
  const chosen = document.getElementById('prescribed-box');
  const simulated = document.getElementById('simulated-box');
  if (!chosen || !simulated) return;
  const heightControl = document.getElementById('table-height');
  const gravityControl = document.getElementById('gravity-enabled');
  const heightOutput = document.getElementById('table-height-value');
  const observation = document.getElementById('physics-observation');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const NS = 'http://www.w3.org/2000/svg';
  const START = 1.6, END = .4, DT = 1 / 240;
  const HOLD = .75, CYCLE = 3.5;
  let tableHeight = .4, gravity = 9.81;
  let y = START, velocity = 0, elapsed = 0, accumulated = 0, lastTime;
  let animationFrame = null;

  function element(tag, attributes, parent, text) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    if (text) node.textContent = text;
    parent.append(node);
    return node;
  }
  const pixelY = height => 320 - height * 145;

  function makeScene(svg) {
    element('rect', {width:420, height:350, fill:'#fefdfb'}, svg);
    element('line', {x1:40, x2:380, y1:320, y2:320, stroke:'#e1ddd3', 'stroke-width':2}, svg);
    const legs = element('g', {stroke:'#b7b8ad', 'stroke-width':8}, svg);
    const leftLeg = element('line', {x1:83, x2:83, y1:270, y2:319}, legs);
    const rightLeg = element('line', {x1:331, x2:331, y1:270, y2:319}, legs);
    const table = element('g', {}, svg);
    element('polygon', {points:'55,0 345,0 365,-15 75,-15', fill:'#dce5df', stroke:'#9db3a7', 'stroke-width':1.4}, table);
    element('path', {d:'M55 0H345V10H55Z', fill:'#a8beb2'}, table);
    element('path', {d:'M345 0L365 -15V-5L345 10Z', fill:'#91a99b'}, table);
    // The ghost outline marks the starting position.
    element('rect', {x:181, y:pixelY(START)-52, width:58, height:52, fill:'none', stroke:'#c9c3b7', 'stroke-width':1.5, 'stroke-dasharray':'5 5'}, svg);
    const box = element('g', {}, svg);
    element('path', {d:'M181 -52L195 -63H253L239 -52Z', fill:'#ebd7a2', stroke:'#b99446', 'stroke-width':1}, box);
    element('path', {d:'M239 -52L253 -63V-11L239 0Z', fill:'#bb9140', stroke:'#a47d33', 'stroke-width':1}, box);
    element('rect', {x:181, y:-52, width:58, height:52, fill:'#d9b765', stroke:'#b99446', 'stroke-width':1}, box);
    return {svg, box, table, leftLeg, rightLeg};
  }
  const scenes = [makeScene(chosen), makeScene(simulated)];

  function prescribedPosition(time) {
    return START - (START-END)*Math.min(Math.max(time, 0)/.85, 1);
  }

  function step(dt) {
    // Semi-implicit Euler for a vertical point mass with a rigid box shape.
    // y is the box's bottom face. Contact is perfectly inelastic: project
    // onto the tabletop and cancel downward velocity, with no bounce.
    if (y <= tableHeight && velocity <= 0) {
      y = tableHeight; velocity = 0; return;
    }
    velocity -= gravity*dt;
    y += velocity*dt;
    if (y < tableHeight) { y = tableHeight; velocity = 0; }
  }

  function draw() {
    const leftY = prescribedPosition(elapsed-HOLD);
    for (const [index, scene] of scenes.entries()) {
      const boxHeight = index ? y : leftY;
      scene.table.setAttribute('transform', `translate(0 ${pixelY(tableHeight)})`);
      scene.box.setAttribute('transform', `translate(0 ${pixelY(boxHeight)})`);
      scene.leftLeg.setAttribute('y1', pixelY(tableHeight)+9);
      scene.rightLeg.setAttribute('y1', pixelY(tableHeight)+9);
      scene.svg.dataset.boxHeight = boxHeight.toFixed(5);
      scene.svg.dataset.tableHeight = tableHeight.toFixed(2);
    }
    simulated.dataset.speed = velocity.toFixed(5);
    simulated.dataset.gravity = gravity.toFixed(2);
  }

  function reducedPose() {
    y = START; velocity = 0;
    for (let i=0; i<240; i++) step(DT);
    elapsed = HOLD+1;
    draw();
  }

  function restart() {
    tableHeight = Number(heightControl.value)/100;
    gravity = gravityControl.checked ? 9.81 : 0;
    heightOutput.textContent = `${heightControl.value} cm`;
    if (!gravity) {
      observation.textContent = 'Gravity is off: the left box keeps its saved movement; the right box stays where released.';
    } else if (tableHeight > END+.001) {
      observation.textContent = 'The table is higher: the left box follows its old path through the tabletop; the right box stops on the new surface.';
    } else if (tableHeight < END-.001) {
      observation.textContent = 'The table is lower: the left box stops above it; the right box falls farther and lands on it.';
    } else {
      observation.textContent = 'Both boxes reach the table. Raise the table to see the difference.';
    }
    chosen.setAttribute('aria-label', `A box follows saved positions from 160 cm to 40 cm. The tabletop is at ${heightControl.value} cm; its height does not change the saved path.`);
    simulated.setAttribute('aria-label', gravity ? `A box released from rest falls under gravity and stops on a tabletop at ${heightControl.value} cm.` : 'With gravity off, the box stays at its starting height of 160 centimeters.');
    y = START; velocity = 0; elapsed = 0; accumulated = 0; lastTime = undefined;
    if (reducedMotion.matches) reducedPose(); else draw();
  }

  function animate(timestamp) {
    animationFrame = null;
    if (document.hidden || reducedMotion.matches) return;
    if (lastTime !== undefined) accumulated += Math.min((timestamp-lastTime)/1000, .1);
    lastTime = timestamp;
    while (accumulated >= DT) {
      elapsed += DT;
      if (elapsed >= CYCLE) { elapsed = 0; y = START; velocity = 0; }
      if (elapsed >= HOLD) step(DT);
      accumulated -= DT;
    }
    draw();
    animationFrame = requestAnimationFrame(animate);
  }
  function resume() {
    if (animationFrame !== null) cancelAnimationFrame(animationFrame);
    animationFrame = null; lastTime = undefined; accumulated = 0;
    if (!document.hidden && !reducedMotion.matches) animationFrame = requestAnimationFrame(animate);
  }
  heightControl.addEventListener('input', restart);
  gravityControl.addEventListener('change', restart);
  reducedMotion.addEventListener('change', () => { restart(); resume(); });
  document.addEventListener('visibilitychange', resume);
  restart(); resume();
})();
