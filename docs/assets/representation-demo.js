(() => {
  'use strict';
  for (const film of document.querySelectorAll('.projection-film')) {
    const movie = film.querySelector('video');
    if (!movie) continue;
    const chapters = Array.from(film.querySelectorAll('[data-projection-time]'));
    function markChapter() {
      const current = chapters.reduce((active, button) => Number(button.dataset.projectionTime) <= movie.currentTime + .05 ? button : active, chapters[0]);
      for (const button of chapters) {
        if (button === current) button.setAttribute('aria-current', 'true');
        else button.removeAttribute('aria-current');
      }
    }
    for (const button of chapters) {
      button.addEventListener('click', () => {
        movie.currentTime = Number(button.dataset.projectionTime);
        movie.play().catch(() => { movie.pause(); });
        movie.scrollIntoView({block: 'center', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
        markChapter();
      });
    }
    movie.addEventListener('timeupdate', markChapter);
    markChapter();
  }
  const cabinetInput = document.getElementById('cabinet-opacity');
  if (cabinetInput) {
    const picture = document.getElementById('cabinet-opacity-image');
    const framePath = value => `assets/projection-cabinet/opacity/cabinet-${String(value).padStart(3, '0')}.webp`;
    const loaded = new Map();
    function preload(value) {
      if (value < 0 || value > 100 || loaded.has(value)) return;
      const frame = new Image();
      frame.src = framePath(value);
      loaded.set(value, frame);
    }
    function updateCabinet() {
      const value = Number(cabinetInput.value);
      picture.src = framePath(value);
      picture.alt = `The same Gaussian cabinet rendered with ${value} percent peak opacity per blob, from the fixed camera view.`;
      document.getElementById('cabinet-opacity-value').textContent = `${value}%`;
      document.getElementById('cabinet-opacity-caption').textContent = `${value}% per blob · your setting`;
      document.getElementById('cabinet-opacity-description').textContent = value === 0
        ? 'At 0%, the blobs contribute no color. Only the white background remains.'
        : value <= 15
        ? `At ${value}%, the faint marks let more of the rear surfaces and white background show through.`
        : value < 70
        ? `At ${value}%, overlapping marks build up stronger color; some rear surfaces can still show through.`
        : `At ${value}%, the strong front marks hide much more of what is behind them.`;
      for (const button of document.querySelectorAll('[data-cabinet-opacity]')) {
        button.setAttribute('aria-pressed', String(Number(button.dataset.cabinetOpacity) === value));
      }
      preload(value - 5);
      preload(value + 5);
    }
    cabinetInput.addEventListener('input', updateCabinet);
    for (const button of document.querySelectorAll('[data-cabinet-opacity]')) {
      button.addEventListener('click', () => {
        cabinetInput.value = button.dataset.cabinetOpacity;
        updateCabinet();
      });
    }
    updateCabinet();
  }
  const input = document.getElementById('front-opacity');
  if (!input) return;
  const blue = [91, 141, 184], gold = [219, 181, 85], white = [255, 255, 255];
  const percent = value => `${Number((value * 100).toFixed(1))}%`;
  function update() {
    const front = Number(input.value) / 100;
    const remaining = 1 - front;
    const back = remaining * .8;
    const background = remaining * .2;
    const rgb = blue.map((c, i) => Math.round(front * c + back * gold[i] + background * white[i]));
    document.getElementById('opacity-value').textContent = percent(front);
    const frontMark = document.getElementById('opacity-front-splat');
    if (frontMark) frontMark.setAttribute('opacity', String(front));
    document.getElementById('blended-pixel').style.background = `rgb(${rgb.join(',')})`;
    const description = `${percent(front)} blue + ${percent(back)} gold + ${percent(background)} white background.`;
    document.getElementById('blend-description').textContent = description;
    document.getElementById('blended-pixel').setAttribute('aria-label', `Calculated pixel: ${description}`);
    document.getElementById('weight-front').style.width = percent(front);
    document.getElementById('weight-back').style.width = percent(back);
    document.getElementById('weight-background').style.width = percent(background);
    document.getElementById('blend-calculation').textContent = `Blue uses ${percent(front)} of the pixel’s weight. Gold gets 80% of the remaining ${percent(remaining)}: ${percent(back)}. The background gets the last ${percent(background)}.`;
  }
  input.addEventListener('input', update);
  for (const button of document.querySelectorAll('[data-opacity]')) {
    button.addEventListener('click', () => { input.value = button.dataset.opacity; update(); });
  }
  update();
})();
