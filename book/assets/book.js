(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const menu = $('menu-toggle');
  const sidebar = $('sidebar');
  const mobile = matchMedia('(max-width: 800px)');
  let contentsOpen = !mobile.matches;
  function setContents(open) {
    contentsOpen = open;
    document.body.classList.toggle('contents-open', mobile.matches && open);
    document.body.classList.toggle('contents-hidden', !mobile.matches && !open);
    sidebar.inert = !open;
    menu.setAttribute('aria-expanded', String(open));
    $('sidebar-backdrop').hidden = !mobile.matches || !open;
  }
  menu.addEventListener('click', () => setContents(!contentsOpen));
  $('sidebar-backdrop').addEventListener('click', () => { setContents(false); menu.focus(); });
  mobile.addEventListener('change', () => setContents(!mobile.matches));
  setContents(contentsOpen);
  sidebar.addEventListener('click', event => {
    if (mobile.matches && event.target.closest('a')) { setContents(false); menu.focus(); }
  });

  const searchPanel = $('book-search');
  const searchInput = $('search-input');
  let searchIndex;
  let queryVersion = 0;
  function toggleSearch(open) {
    searchPanel.hidden = !open;
    $('search-toggle').setAttribute('aria-expanded', String(open));
    if (open) { searchPanel.scrollIntoView({block:'start', behavior:'instant'}); searchInput.focus(); }
    else $('search-toggle').focus();
  }
  $('search-toggle').addEventListener('click', () => toggleSearch(searchPanel.hidden));
  $('search-close').addEventListener('click', () => toggleSearch(false));
  searchInput.addEventListener('input', async () => {
    const version = ++queryVersion;
    const query = searchInput.value.trim().toLowerCase();
    $('search-results').replaceChildren();
    if (!query) { $('search-status').textContent = ''; return; }
    try {
      if (!searchIndex) {
        const response = await fetch('search-index.json');
        if (!response.ok) throw new Error('Search unavailable');
        searchIndex = await response.json();
      }
      if (version !== queryVersion) return;
      const words = query.split(/\s+/);
      const results = searchIndex.filter(item => words.every(word => (item.title+' '+item.text).toLowerCase().includes(word)));
      $('search-status').textContent = results.length ? `${results.length} ${results.length === 1 ? 'section' : 'sections'} found` : 'No matching sections. Try “link”, “joint”, or “tree”.';
      for (const result of results) {
        const li = document.createElement('li'), a = document.createElement('a'), p = document.createElement('p');
        const currentPage = location.pathname.split('/').pop() || 'index.html';
        a.href = result.url.split('#')[0] === currentPage ? '#'+result.url.split('#')[1] : result.url;
        a.textContent = result.title;
        const match = result.text.toLowerCase().indexOf(words[0]);
        const start = Math.max(0, match-55);
        p.textContent = (start ? '…' : '') + result.text.slice(start,start+200) + (start+200 < result.text.length ? '…' : '');
        li.append(a,p); $('search-results').append(li);
      }
    } catch { if (version === queryVersion) $('search-status').textContent = 'Search could not load. You can still use the contents on the left.'; }
  });
  $('search-results').addEventListener('click', event => {
    if (event.target.closest('a')) { searchPanel.hidden = true; $('search-toggle').setAttribute('aria-expanded','false'); }
  });
  document.addEventListener('keydown', event => {
    const editing = event.target.matches('input, textarea, select, [contenteditable="true"]');
    if (event.key === '/' && !editing) { event.preventDefault(); toggleSearch(true); }
    if (event.key === 'Escape') {
      if (!searchPanel.hidden) toggleSearch(false);
      if (mobile.matches && contentsOpen) { setContents(false); menu.focus(); }
    }
    if (event.key === 'Tab' && mobile.matches && contentsOpen) {
      const items = [...sidebar.querySelectorAll('a[href],button')];
      const first = items[0], last = items.at(-1);
      if (event.shiftKey && (document.activeElement === first || !sidebar.contains(document.activeElement))) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && (document.activeElement === last || !sidebar.contains(document.activeElement))) { event.preventDefault(); first.focus(); }
    }
  });
  $('print').addEventListener('click', () => window.print());

  // Keep detailed figures readable without leaving the chapter.
  const figureLinks = document.querySelectorAll('a[data-enlarge]');
  if (figureLinks.length) {
    const dialog = document.createElement('dialog');
    dialog.className = 'figure-dialog';
    dialog.setAttribute('aria-label', 'Enlarged figure');
    const bar = document.createElement('div');
    bar.className = 'figure-dialog-bar';
    const close = document.createElement('button');
    close.type = 'button'; close.className = 'text-button'; close.textContent = 'Close ×';
    const image = document.createElement('img'), caption = document.createElement('p');
    bar.append(close); dialog.append(bar, image, caption); document.body.append(dialog);
    let figureTrigger;
    for (const link of figureLinks) link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      figureTrigger = link;
      const original = link.querySelector('img');
      image.src = link.href; image.alt = original.alt;
      caption.textContent = link.closest('figure').querySelector('figcaption')?.textContent || '';
      dialog.showModal(); dialog.scrollTop = 0;
    });
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      const rect = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
    });
    dialog.addEventListener('close', () => figureTrigger?.focus({preventScroll:true}));
  }

  const sections = [...document.querySelectorAll('article [id][data-title], #chapter-start')];
  const links = [...document.querySelectorAll('.chapter-list a[href]')];
  let queued = false;
  function updateSection() {
    const active = sections.filter(section => section.getBoundingClientRect().top <= 150).at(-1) || sections[0];
    for (const link of links) {
      const url = new URL(link.href);
      const samePage = (url.pathname.split('/').pop() || 'index.html') === (location.pathname.split('/').pop() || 'index.html');
      const current = samePage && url.hash === '#'+active.id;
      if (current) link.setAttribute('aria-current','location'); else link.removeAttribute('aria-current');
    }
    queued = false;
  }
  addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(updateSection); } }, {passive:true});
  updateSection();
  // Open a long contents list near the current chapter, without collapsing it.
  const currentChapter = links.find(link => {
    const url = new URL(link.href);
    return url.hash === '#chapter-start' && (url.pathname.split('/').pop() || 'index.html') === (location.pathname.split('/').pop() || 'index.html');
  });
  if (currentChapter && currentChapter.getBoundingClientRect().bottom > sidebar.getBoundingClientRect().bottom - 40) {
    sidebar.scrollTop += currentChapter.getBoundingClientRect().top - sidebar.getBoundingClientRect().top - 30;
  }
})();
