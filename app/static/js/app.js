/* ============================================================
   Sorties Caen — Frontend
   ============================================================ */

// ── Design tokens ─────────────────────────────────────────────
const CAT_COLORS = {
  musique:    '#7C5CFB',
  théâtre:    '#E5484D',
  theatre:    '#E5484D',
  humour:     '#F5A524',
  danse:      '#E93D82',
  expo:       '#2F9CF4',
  enfants:    '#30A46C',
  sport:      '#F76808',
  brocante:   '#12A594',
  marché:     '#12A594',
  marche:     '#12A594',
  autre:      '#93A0B8',
};

function catColor(cat) {
  if (!cat) return '#93A0B8';
  return CAT_COLORS[cat.toLowerCase().trim()] ?? '#93A0B8';
}

// ── API ────────────────────────────────────────────────────────
async function api(path) {
  const res = await fetch('/api' + path);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

// ── Dates ──────────────────────────────────────────────────────
const DAYS   = ['Dim','Lun','Mar','Mer','Jeu','Ven','Sam'];
const MONTHS = ['janvier','février','mars','avril','mai','juin',
                'juillet','août','septembre','octobre','novembre','décembre'];

function fmtDate(iso) {
  const d = new Date(iso);
  return `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
}
function fmtDateTime(iso) {
  const d = new Date(iso);
  const h = d.getHours(), m = d.getMinutes();
  return `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]} · ${h}h${String(m).padStart(2,'0')}`;
}
// System timestamps (scraped_at, first_seen) come from the backend as naive
// UTC strings without a timezone suffix. new Date() would read them as LOCAL
// time, adding a ~2h offset in Paris summer time. Append 'Z' so they parse as UTC.
function parseUTC(iso) {
  if (typeof iso === 'string' && !/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso)) {
    iso += 'Z';
  }
  return new Date(iso);
}
function fmtRelative(iso) {
  const s = (Date.now() - parseUTC(iso)) / 1000;
  if (s < 3600)   return `Ajouté il y a ${Math.max(1, Math.round(s/60))} min`;
  if (s < 86400)  return `Ajouté il y a ${Math.round(s/3600)} h`;
  if (s < 172800) return 'Ajouté hier';
  return `Ajouté il y a ${Math.round(s/86400)} j`;
}
function fmtScrapeAge(iso) {
  const s = (Date.now() - parseUTC(iso)) / 1000;
  if (s < 60)    return "Mis à jour à l'instant";
  if (s < 3600)  return `Mis à jour il y a ${Math.round(s/60)} min`;
  if (s < 86400) return `Mis à jour il y a ${Math.round(s/3600)} h`;
  return `Mis à jour il y a ${Math.round(s/86400)} j`;
}
function fmtPrice(p) {
  if (!p) return '';
  const l = p.toLowerCase().trim();
  if (['gratuit','free','0','0€','0 €','entrée libre','libre'].includes(l)) return 'Gratuit';
  return p;
}
function fmtDateOnly(iso) {
  const d = new Date(iso);
  return `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
}
function fmtTimeIfKnown(iso) {
  const d = new Date(iso);
  if (d.getHours() === 0 && d.getMinutes() === 0) return null;
  return `${d.getHours()}h${String(d.getMinutes()).padStart(2,'0')}`;
}
function fmtDateSmart(iso) {
  const t = fmtTimeIfKnown(iso);
  return t ? `${fmtDateOnly(iso)} · ${t}` : fmtDateOnly(iso);
}
function splitTitle(ev) {
  if (ev.artist) return { name: ev.artist, subtitle: ev.title };
  const m = ev.title.match(/^(.+?)\s[–—]\s(.+)$/) || ev.title.match(/^(.+?):\s(.+)$/);
  if (m) return { name: m[1].trim(), subtitle: m[2].trim() };
  return { name: ev.title, subtitle: '' };
}
function bookingProvider(url) {
  if (!url) return '';
  try {
    const host = new URL(url).hostname.replace(/^www\./, '');
    if (host.includes('weezevent'))    return 'Weezevent';
    if (host.includes('ticketmaster')) return 'Ticketmaster';
    if (host.includes('fnac'))         return 'Fnac';
    if (host.includes('digitick'))     return 'Digitick';
    if (host.includes('helloasso'))    return 'HelloAsso';
    if (host.includes('shotgun'))      return 'Shotgun';
    return '';
  } catch { return ''; }
}

// ── SVG icons ─────────────────────────────────────────────────
const ICO_CAL  = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;
const ICO_PIN  = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>`;
const ICO_ARR  = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M7 17 17 7M17 7H7M17 7v10"/></svg>`;

// ── HTML components ────────────────────────────────────────────
function badgeCat(cat) {
  const c = catColor(cat);
  return `<span class="badge-cat" style="--cat-color:${c}">${cat}</span>`;
}

function buildCardA(ev) {
  const color   = catColor(ev.category);
  const price   = fmtPrice(ev.price);
  const { name, subtitle } = splitTitle(ev);
  const dateStr = fmtDateSmart(ev.date);

  const imgPart = ev.image_url
    ? `<img src="${ev.image_url}" alt="" loading="lazy">`
    : `<div class="card-a-fallback" style="background:linear-gradient(160deg,${color}44 0%,${color}11 100%)">
         <span class="card-a-initial" style="color:${color}22">${name.charAt(0).toUpperCase()}</span>
       </div>`;

  return `<div class="card-a" data-id="${ev.id}">
    <div class="card-a-poster">
      ${imgPart}
      <div class="card-a-badges">
        ${ev.category ? badgeCat(ev.category) : ''}
        ${ev.is_new ? '<span class="badge-new">NOUVEAU</span>' : ''}
      </div>
    </div>
    <div class="card-a-body">
      <div class="card-a-name">${name}</div>
      ${subtitle ? `<div class="card-a-subtitle">${subtitle}</div>` : ''}
      <div class="card-a-meta">${ICO_CAL} ${dateStr}</div>
      <div class="card-a-meta">${ICO_PIN} ${ev.venue}</div>
    </div>
    <div class="card-a-footer">
      <span class="card-a-price${price === 'Gratuit' ? ' is-free' : ''}">${price || '—'}</span>
      ${ev.booking_url
        ? `<a class="card-book" href="${ev.booking_url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Billetterie ${ICO_ARR}</a>`
        : ''}
    </div>
  </div>`;
}

function buildCardB(ev) {
  const color   = catColor(ev.category);
  const price   = fmtPrice(ev.price);
  const { name, subtitle } = splitTitle(ev);
  const dateStr = fmtDateSmart(ev.date);

  const imgPart = ev.image_url
    ? `<img src="${ev.image_url}" alt="" loading="lazy">`
    : `<div class="card-b-fallback" style="background:linear-gradient(160deg,${color}44 0%,${color}11 100%)">
         <span class="card-b-initial" style="color:${color}22">${name.charAt(0).toUpperCase()}</span>
       </div>`;

  return `<div class="card-b" data-id="${ev.id}">
    <div class="card-b-poster">
      ${imgPart}
      ${ev.is_new ? '<span class="badge-new card-b-badge-new">NOUVEAU</span>' : ''}
    </div>
    <div class="card-b-body">
      ${ev.category ? `<div class="card-b-eyebrow" style="color:${color}">${ev.category}</div>` : ''}
      <div class="card-b-name">${name}</div>
      ${subtitle ? `<div class="card-b-subtitle">${subtitle}</div>` : ''}
      <div class="card-b-meta">${ICO_CAL} ${dateStr} · ${ICO_PIN} ${ev.venue}</div>
      <div class="card-b-footer">
        <span class="card-b-price${price === 'Gratuit' ? ' is-free' : ''}">${price || ''}</span>
        ${ev.booking_url
          ? `<a class="card-b-book" href="${ev.booking_url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Billetterie ${ICO_ARR}</a>`
          : ''}
      </div>
    </div>
  </div>`;
}

function buildRow(ev) {
  const color = catColor(ev.category);
  const price = fmtPrice(ev.price);
  return `<div class="list-row" data-id="${ev.id}">
    <div class="row-date">
      <span class="row-bar" style="background:${color}"></span>
      <span>${fmtDate(ev.date)}</span>
    </div>
    <div class="row-info">
      <div class="row-title">${ev.title}</div>
      <div class="row-venue">${ev.venue}</div>
    </div>
    <div class="row-badge">${ev.category ? badgeCat(ev.category) : ''}</div>
    <div class="row-right">
      <span class="row-price">${price}</span>
      ${ev.booking_url
        ? `<a class="row-book" href="${ev.booking_url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Billetterie ${ICO_ARR}</a>`
        : ''}
    </div>
  </div>`;
}

// ── State ─────────────────────────────────────────────────────
const state = {
  sort:       'added',   // 'added' | 'date'
  cat:        '',
  venue:      '',
  search:     '',
  newItems:   [],        // cache for load-more
  newShown:   4,
  upPage:     1,
  upParams:   null,
  allPage:    1,
  calYear:    new Date().getFullYear(),
  calMonth:   new Date().getMonth() + 1,
};

// ── Theme ─────────────────────────────────────────────────────
function initTheme() {
  document.documentElement.dataset.theme = localStorage.getItem('theme') || 'dark';
}
document.getElementById('btn-theme').addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('theme', next);
});

// ── Navbar stats ──────────────────────────────────────────────
async function refreshNavbar() {
  try {
    const s = await api('/stats');
    const el = document.getElementById('last-update');
    if (s.last_scrape_at) el.textContent = fmtScrapeAge(s.last_scrape_at);
    const btn = document.getElementById('btn-refresh');
    if (btn) btn.classList.remove('hidden');
  } catch {}
  await refreshBellBadge();
}

// ── Bell dropdown ──────────────────────────────────────────────
let bellOpen = false;

async function refreshBellBadge() {
  try {
    const lastSeen = localStorage.getItem('bellLastSeen');
    const params   = lastSeen ? '?since=' + encodeURIComponent(lastSeen) : '?days=30';
    const items    = await api('/events/new' + params);
    const badge    = document.getElementById('bell-badge');
    if (items.length > 0) {
      badge.textContent = items.length > 99 ? '99+' : items.length;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  } catch {}
}

async function loadBellDropdown() {
  const list = document.getElementById('bell-list');
  list.innerHTML = '<p class="empty-state" style="padding:20px">Chargement…</p>';
  try {
    const items = await api('/events/new?days=30');
    if (items.length === 0) {
      list.innerHTML = '<p class="empty-state" style="padding:20px">Aucune nouveauté récente.</p>';
      return;
    }
    const lastSeen = localStorage.getItem('bellLastSeen');
    list.innerHTML = items.map(ev => {
      const isUnseen = !lastSeen || parseUTC(ev.first_seen) > new Date(lastSeen);
      const color    = catColor(ev.category);
      const price    = fmtPrice(ev.price);
      return `<div class="bell-item${isUnseen ? ' bell-item-new' : ''}" data-id="${ev.id}">
        <span class="bell-item-bar" style="background:${color}"></span>
        <div class="bell-item-info">
          <div class="bell-item-title">${ev.title}</div>
          <div class="bell-item-meta">${ICO_CAL} ${fmtDate(ev.date)} · ${ev.venue}</div>
        </div>
        <div class="bell-item-right">
          ${price ? `<span class="bell-item-price${price === 'Gratuit' ? ' is-free' : ''}">${price}</span>` : ''}
          ${isUnseen ? '<span class="bell-item-dot"></span>' : ''}
        </div>
      </div>`;
    }).join('');
  } catch {
    list.innerHTML = '<p class="empty-state" style="padding:20px">Impossible de charger.</p>';
  }
}

function openBellDropdown() {
  const dropdown = document.getElementById('bell-dropdown');
  const btn      = document.getElementById('btn-bell');
  bellOpen = true;
  dropdown.classList.remove('hidden');
  btn.setAttribute('aria-expanded', 'true');
  loadBellDropdown();
}

function closeBellDropdown() {
  const dropdown = document.getElementById('bell-dropdown');
  const btn      = document.getElementById('btn-bell');
  bellOpen = false;
  dropdown.classList.add('hidden');
  btn.setAttribute('aria-expanded', 'false');
}

function markBellSeen() {
  localStorage.setItem('bellLastSeen', new Date().toISOString());
  document.getElementById('bell-badge').classList.add('hidden');
  closeBellDropdown();
  // Re-render items without the unseen dots
  loadBellDropdown().then(() => openBellDropdown());
}

document.getElementById('btn-bell').addEventListener('click', e => {
  e.stopPropagation();
  bellOpen ? closeBellDropdown() : openBellDropdown();
});
document.getElementById('bell-mark-seen').addEventListener('click', e => {
  e.stopPropagation();
  markBellSeen();
});
document.getElementById('bell-list').addEventListener('click', e => {
  const item = e.target.closest('[data-id]');
  if (item) { closeBellDropdown(); navigate('event/' + item.dataset.id); }
});
document.addEventListener('click', e => {
  if (bellOpen && !e.target.closest('#bell-wrap')) closeBellDropdown();
});

// ── Refresh button ─────────────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms));

document.getElementById('btn-refresh').addEventListener('click', async function() {
  const label = document.getElementById('last-update');
  this.classList.add('spinning');
  this.disabled = true;

  // Baseline: the scrape runs in the background and takes 1-2 min, so we poll
  // /stats until last_scrape_at advances rather than reading it immediately.
  let baseline = null;
  try { baseline = (await api('/stats')).last_scrape_at; } catch {}

  let triggered = false;
  try {
    const res = await fetch('/api/scrape/run', { method: 'POST' });
    triggered = res.ok;
    if (!res.ok && label) label.textContent = 'Mise à jour indisponible';
  } catch {
    if (label) label.textContent = 'Mise à jour indisponible';
  }

  if (triggered) {
    if (label) label.textContent = 'Mise à jour en cours…';
    // Poll for up to ~3 min (40 × 5s) until the scrape timestamp changes.
    for (let i = 0; i < 40; i++) {
      await sleep(5000);
      try {
        const s = await api('/stats');
        if (s.last_scrape_at && s.last_scrape_at !== baseline) break;
      } catch {}
    }
    await refreshNavbar();
    const { page } = getRoute();
    if (page === 'radar') await loadRadar();
    else if (page === 'sorties') await loadAllPage();
  }

  this.classList.remove('spinning');
  this.disabled = false;
});

// ── Venue select ──────────────────────────────────────────────
async function populateVenueSelect() {
  try {
    const venues = await api('/venues');
    const sel = document.getElementById('filter-venue');
    venues.forEach(v => {
      const o = document.createElement('option');
      o.value = v.key;
      o.textContent = `${v.name} (${v.count})`;
      sel.appendChild(o);
    });
  } catch {}
}

// ── Category pills ─────────────────────────────────────────────
async function populateCategoryPills() {
  try {
    const cats = await api('/categories');
    const wrap = document.getElementById('category-pills');
    cats.forEach(c => {
      const btn = document.createElement('button');
      btn.className = 'pill';
      btn.dataset.cat = c.name;
      const col = catColor(c.name);
      btn.innerHTML = `<span style="color:${col}">●</span> ${c.name}`;
      wrap.appendChild(btn);
    });
  } catch {}
}

function applyPillStyles() {
  document.querySelectorAll('#category-pills .pill').forEach(p => {
    const active = p.classList.contains('active');
    const cat = p.dataset.cat;
    if (active && cat) {
      const c = catColor(cat);
      p.style.cssText = `background:${c}28;border-color:${c}55;color:${c}`;
    } else if (active) {
      p.style.cssText = 'background:var(--accent);border-color:transparent;color:white';
    } else {
      p.style.cssText = '';
    }
  });
}

document.getElementById('category-pills').addEventListener('click', e => {
  const btn = e.target.closest('.pill');
  if (!btn) return;
  state.cat = btn.dataset.cat ?? '';
  document.querySelectorAll('#category-pills .pill').forEach(p =>
    p.classList.toggle('active', p === btn)
  );
  applyPillStyles();
  refreshRadar();
});

// ── Filters ────────────────────────────────────────────────────
let searchTimer;
document.getElementById('search-input').addEventListener('input', function() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { state.search = this.value.trim(); refreshRadar(); }, 280);
});
document.getElementById('filter-venue').addEventListener('change', function() {
  state.venue = this.value; refreshRadar();
});
document.getElementById('filter-date').addEventListener('change', function() {
  refreshRadar(); // date filter handled in upcoming params
});

// ── Sort toggle ────────────────────────────────────────────────
document.getElementById('sort-added').addEventListener('click', function() {
  state.sort = 'added';
  this.classList.add('active');
  document.getElementById('sort-date').classList.remove('active');
  renderNewSection();
});
document.getElementById('sort-date').addEventListener('click', function() {
  state.sort = 'date';
  this.classList.add('active');
  document.getElementById('sort-added').classList.remove('active');
  renderNewSection();
});

// ── New banner ─────────────────────────────────────────────────
async function loadNewBanner() {
  try {
    const lastVisit = localStorage.getItem('lastVisit');
    let newEvents;
    if (lastVisit) {
      newEvents = await api('/events/new?since=' + encodeURIComponent(lastVisit));
    } else {
      newEvents = await api('/events/new?days=7');
    }
    if (newEvents.length === 0) return;

    const banner = document.getElementById('new-banner');
    document.getElementById('new-banner-title').textContent =
      `${newEvents.length} nouveau${newEvents.length > 1 ? 'x' : ''} événement${newEvents.length > 1 ? 's' : ''} depuis ta dernière visite`;

    if (lastVisit) {
      const days = Math.round((Date.now() - new Date(lastVisit)) / 86400000);
      const msg = days === 0 ? "Dernier passage aujourd'hui"
                : days === 1 ? "Dernier passage hier"
                : `Dernier passage il y a ${days} jour${days > 1 ? 's' : ''}`;
      document.getElementById('new-banner-sub').textContent =
        msg + ' · les petites salles partent vite, ne traîne pas.';
    }
    banner.classList.remove('hidden');
  } catch {}
}

// ── Nouveautés section ────────────────────────────────────────
async function loadNewEvents() {
  try {
    const params = new URLSearchParams({ days: 30 });
    if (state.cat)    params.set('category', state.cat);
    if (state.venue)  params.set('venue', state.venue);
    if (state.search) params.set('search', state.search);
    const items = await api('/events/new?' + params);
    state.newItems = items;
    state.newShown = 4;
    renderNewSection();
  } catch {
    document.getElementById('new-cards').innerHTML =
      '<p class="empty-state">Impossible de charger.</p>';
  }
}

function renderNewSection() {
  const items = state.sort === 'date'
    ? [...state.newItems].sort((a, b) => new Date(a.date) - new Date(b.date))
    : state.newItems; // already sorted by first_seen desc from API

  const shown = items.slice(0, state.newShown);
  document.getElementById('new-cards').innerHTML = shown.map(buildCardA).join('');
  document.getElementById('new-meta').textContent =
    `triées par ${state.sort === 'added' ? "date d'ajout" : "date de l'événement"} · ${items.length} résultat${items.length !== 1 ? 's' : ''}`;

  const btn = document.getElementById('btn-more-new');
  btn.classList.toggle('hidden', state.newShown >= items.length);
}

document.getElementById('btn-more-new').addEventListener('click', () => {
  state.newShown += 4;
  renderNewSection();
});

// ── Weekend section ────────────────────────────────────────────
async function loadWeekend() {
  const grid  = document.getElementById('weekend-cards');
  const meta  = document.getElementById('weekend-meta');
  const empty = document.getElementById('weekend-empty');
  grid.innerHTML = '';
  try {
    let items = await api('/events/weekend');
    if (state.cat)    items = items.filter(e => e.category?.toLowerCase() === state.cat.toLowerCase());
    if (state.venue)  items = items.filter(e => e.venue_key === state.venue);
    if (state.search) {
      const q = state.search.toLowerCase();
      items = items.filter(e => e.title.toLowerCase().includes(q) || e.venue.toLowerCase().includes(q));
    }
    if (items.length === 0) {
      empty.classList.remove('hidden');
    } else {
      empty.classList.add('hidden');
      grid.innerHTML = items.map(buildCardA).join('');
      // Date range label
      const d0 = new Date(items[0].date), d1 = new Date(items[items.length-1].date);
      meta.textContent = `${DAYS[d0.getDay()]} ${d0.getDate()} — ${DAYS[d1.getDay()]} ${d1.getDate()} ${MONTHS[d1.getMonth()]}`;
    }
  } catch {}
}

// ── Upcoming section ───────────────────────────────────────────
async function loadUpcoming() {
  const wrap = document.getElementById('upcoming-rows');
  wrap.innerHTML = '';
  try {
    const params = new URLSearchParams({ sort: 'date', page: 1, page_size: 20 });
    if (state.cat)    params.set('category', state.cat);
    if (state.venue)  params.set('venue', state.venue);
    if (state.search) params.set('search', state.search);
    const data = await api('/events?' + params);
    const items = data.items ?? [];
    wrap.innerHTML = items.map(buildRow).join('');
    state.upPage = 1;
    state.upParams = params;
    const btn = document.getElementById('btn-more-upcoming');
    btn.classList.toggle('hidden', (data.pages ?? 1) <= 1);
  } catch {}
}

document.getElementById('btn-more-upcoming').addEventListener('click', async function() {
  state.upParams.set('page', ++state.upPage);
  const data = await api('/events?' + state.upParams);
  document.getElementById('upcoming-rows')
    .insertAdjacentHTML('beforeend', (data.items ?? []).map(buildRow).join(''));
  if (state.upPage >= (data.pages ?? 1)) this.classList.add('hidden');
});

function refreshRadar() {
  loadNewEvents();
  loadWeekend();
  loadUpcoming();
}

// ── NOUVEAUTÉS page ────────────────────────────────────────────
const nouvState = { sort: 'added', items: [], shown: 8 };

async function loadNouveautes() {
  const wrap = document.getElementById('nouv-cards');
  wrap.innerHTML = Array(4).fill('<div class="skeleton" style="aspect-ratio:3/4;border-radius:16px"></div>').join('');
  try {
    nouvState.items = await api('/events/new?days=60');
    nouvState.shown = 8;
    renderNouveautes();
  } catch {
    wrap.innerHTML = '<p class="empty-state">Impossible de charger.</p>';
  }
}
function renderNouveautes() {
  const items = nouvState.sort === 'date'
    ? [...nouvState.items].sort((a, b) => new Date(a.date) - new Date(b.date))
    : nouvState.items;
  const shown = items.slice(0, nouvState.shown);
  document.getElementById('nouv-cards').innerHTML = shown.map(buildCardA).join('');
  document.getElementById('nouv-meta').textContent =
    `${items.length} nouveauté${items.length !== 1 ? 's' : ''}`;
  document.getElementById('btn-more-nouv').classList.toggle('hidden', nouvState.shown >= items.length);
}
document.getElementById('nouv-sort-added').addEventListener('click', function() {
  nouvState.sort = 'added';
  this.classList.add('active');
  document.getElementById('nouv-sort-date').classList.remove('active');
  renderNouveautes();
});
document.getElementById('nouv-sort-date').addEventListener('click', function() {
  nouvState.sort = 'date';
  this.classList.add('active');
  document.getElementById('nouv-sort-added').classList.remove('active');
  renderNouveautes();
});
document.getElementById('btn-more-nouv').addEventListener('click', () => {
  nouvState.shown += 8;
  renderNouveautes();
});

// ── RADAR page ─────────────────────────────────────────────────
async function loadRadar() {
  await loadNewBanner();
  await Promise.all([loadNewEvents(), loadWeekend(), loadUpcoming()]);
  // Save visit timestamp for next time (on unload would be ideal but unreliable on mobile)
  localStorage.setItem('lastVisit', new Date().toISOString());
}

// ── CALENDAR page ──────────────────────────────────────────────
const calState = { cat: '', venue: '', activeDate: null, byDay: {} };

function buildCalLegend() {
  const wrap = document.getElementById('cal-legend');
  wrap.innerHTML = '';
  const seen = new Set();
  Object.entries(CAT_COLORS).forEach(([name, color]) => {
    if (seen.has(color)) return;
    seen.add(color);
    const label = name.charAt(0).toUpperCase() + name.slice(1);
    wrap.insertAdjacentHTML('beforeend',
      `<span class="cal-legend-item"><span class="cal-legend-dot" style="background:${color}"></span>${label}</span>`);
  });
}

function populateCalFilters() {
  // Category select
  const catSel = document.getElementById('cal-filter-cat');
  const seen = new Set();
  Object.entries(CAT_COLORS).forEach(([name]) => {
    const norm = name === 'theatre' ? null : name; // skip alias
    if (!norm || seen.has(norm)) return;
    seen.add(norm);
    const o = document.createElement('option');
    o.value = norm;
    o.textContent = norm.charAt(0).toUpperCase() + norm.slice(1);
    catSel.appendChild(o);
  });

  // Venue select — clone options from radar venue select
  const venueSel = document.getElementById('cal-filter-venue');
  document.querySelectorAll('#filter-venue option').forEach(o => {
    venueSel.appendChild(o.cloneNode(true));
  });

  catSel.addEventListener('change', function() {
    calState.cat = this.value;
    closeCalPanel();
    renderCalendar();
  });
  venueSel.addEventListener('change', function() {
    calState.venue = this.value;
    closeCalPanel();
    renderCalendar();
  });
}

function filterCalEvents(evts) {
  let f = evts;
  if (calState.cat)   f = f.filter(e => e.category?.toLowerCase() === calState.cat);
  if (calState.venue) f = f.filter(e => e.venue_key === calState.venue);
  return f;
}

async function renderCalendar() {
  const mm = String(state.calMonth).padStart(2, '0');
  const monthName = MONTHS[state.calMonth - 1];
  document.getElementById('cal-month-label').textContent =
    `${monthName.charAt(0).toUpperCase() + monthName.slice(1)} ${state.calYear}`;

  // Loading indicator
  const grid = document.getElementById('cal-grid');
  grid.style.opacity = '.4';

  let days = [];
  try {
    const params = new URLSearchParams({ month: `${state.calYear}-${mm}` });
    if (calState.venue) params.set('venue', calState.venue);
    if (calState.cat)   params.set('category', calState.cat);
    days = await api('/calendar?' + params);
  } catch {}

  calState.byDay = Object.fromEntries(days.map(d => [d.date, d.events]));
  grid.style.opacity = '';
  grid.innerHTML = '';

  const firstDow = new Date(state.calYear, state.calMonth - 1, 1).getDay();
  const offset   = firstDow === 0 ? 6 : firstDow - 1;
  const dimMonth = new Date(state.calYear, state.calMonth, 0).getDate();
  const prevDim  = new Date(state.calYear, state.calMonth - 1, 0).getDate();
  const today    = new Date().toISOString().slice(0, 10);

  const cells = [];
  for (let i = offset - 1; i >= 0; i--) cells.push({ day: prevDim - i, date: null, other: true });
  for (let d = 1; d <= dimMonth; d++) {
    cells.push({ day: d, date: `${state.calYear}-${mm}-${String(d).padStart(2, '0')}`, other: false });
  }
  const rem = (7 - cells.length % 7) % 7;
  for (let d = 1; d <= rem; d++) cells.push({ day: d, date: null, other: true });

  cells.forEach(({ day, date, other }) => {
    const evts = date ? (calState.byDay[date] ?? []) : [];
    const isActive = date && date === calState.activeDate;
    const cell = document.createElement('div');
    cell.className = [
      'cal-cell',
      other         ? 'other-month' : '',
      date === today ? 'today' : '',
      evts.length   ? 'has-events' : '',
      isActive      ? 'active-day' : '',
    ].filter(Boolean).join(' ');

    const chips = evts.slice(0, 3).map(ev => {
      const c = catColor(ev.category);
      return `<span class="cal-chip" style="background:${c}22;color:${c}">${ev.title}</span>`;
    }).join('') + (evts.length > 3
      ? `<span class="cal-chip cal-chip-more">+${evts.length - 3}</span>` : '');

    cell.innerHTML = `<div class="cal-num">${day}</div>${chips}`;

    if (evts.length && date) {
      cell.addEventListener('click', () => openCalPanel(date, evts));
    }
    grid.appendChild(cell);
  });

  // Mobile list view
  renderCalMobileList();
}

function openCalPanel(date, evts) {
  calState.activeDate = date;

  // Highlight active cell
  document.querySelectorAll('.cal-cell').forEach(c =>
    c.classList.toggle('active-day', c.querySelector('.cal-num')?.textContent == new Date(date + 'T12:00').getDate())
  );

  const panel = document.getElementById('cal-day-panel');
  const title = document.getElementById('cal-day-panel-title');
  const list  = document.getElementById('cal-day-events');

  const d = new Date(date + 'T12:00');
  title.textContent = `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
  list.innerHTML = evts.map(buildRow).join('') || '<p class="empty-state">Aucun événement.</p>';
  panel.classList.remove('hidden');
  document.getElementById('cal-body')?.classList.add('panel-open');
}

function closeCalPanel() {
  calState.activeDate = null;
  document.getElementById('cal-day-panel').classList.add('hidden');
  document.getElementById('cal-body')?.classList.remove('panel-open');
  document.querySelectorAll('.cal-cell.active-day').forEach(c => c.classList.remove('active-day'));
}

document.getElementById('cal-day-panel-close').addEventListener('click', closeCalPanel);

function renderCalMobileList() {
  const wrap = document.getElementById('cal-mobile-list');
  if (!wrap) return;
  const entries = Object.entries(calState.byDay).sort(([a], [b]) => a.localeCompare(b));
  if (entries.length === 0) {
    wrap.innerHTML = '<p class="empty-state">Aucun événement ce mois.</p>';
    return;
  }
  wrap.innerHTML = entries.map(([date, evts]) => {
    const d = new Date(date + 'T12:00');
    const header = `<div class="cal-list-day-header">${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}</div>`;
    return header + evts.map(buildRow).join('');
  }).join('');
}

document.getElementById('cal-prev').addEventListener('click', () => {
  if (--state.calMonth < 1) { state.calMonth = 12; state.calYear--; }
  closeCalPanel();
  renderCalendar();
});
document.getElementById('cal-next').addEventListener('click', () => {
  if (++state.calMonth > 12) { state.calMonth = 1; state.calYear++; }
  closeCalPanel();
  renderCalendar();
});

function initCalendar() {
  buildCalLegend();
  populateCalFilters();
  renderCalendar();
}

// ── ALL SORTIES page ───────────────────────────────────────────
const allState = { cat: '', venue: '', search: '', free: false, dateFrom: '', dateTo: '', sort: 'date' };

function buildAllParams() {
  const params = new URLSearchParams({ sort: allState.sort, page: state.allPage, page_size: 30 });
  if (allState.cat)      params.set('category', allState.cat);
  if (allState.venue)    params.set('venue', allState.venue);
  if (allState.search)   params.set('search', allState.search);
  if (allState.free)     params.set('free', '1');
  if (allState.dateFrom) params.set('date_from', allState.dateFrom);
  if (allState.dateTo)   params.set('date_to', allState.dateTo);
  return params;
}

function allSkeletons(n = 8) {
  return Array(n).fill('<div class="skeleton-row"></div>').join('');
}

async function loadAllPage() {
  state.allPage = 1;
  const wrap  = document.getElementById('all-rows');
  const meta  = document.getElementById('all-meta');
  const empty = document.getElementById('all-empty');
  wrap.innerHTML = allSkeletons();
  empty.classList.add('hidden');
  try {
    const data  = await api('/events?' + buildAllParams());
    const items = data.items ?? [];
    const total = data.total ?? items.length;
    meta.textContent = `${total} événement${total !== 1 ? 's' : ''}`;
    wrap.innerHTML = items.length ? items.map(buildCardB).join('') : '';
    empty.classList.toggle('hidden', items.length > 0);
    const btn = document.getElementById('btn-more-all');
    btn.classList.toggle('hidden', (data.pages ?? 1) <= 1);
  } catch {
    wrap.innerHTML = '';
    empty.textContent = 'Impossible de charger les événements.';
    empty.classList.remove('hidden');
  }
}

async function populateAllFilters() {
  try {
    const [venues, cats] = await Promise.all([api('/venues'), api('/categories')]);
    const vSel = document.getElementById('all-filter-venue');
    venues.forEach(v => {
      const o = document.createElement('option');
      o.value = v.key; o.textContent = `${v.name} (${v.count})`;
      vSel.appendChild(o);
    });
    const pillWrap = document.getElementById('all-cat-pills');
    cats.forEach(c => {
      const btn = document.createElement('button');
      btn.className = 'pill'; btn.dataset.cat = c.name;
      const col = catColor(c.name);
      btn.innerHTML = `<span style="color:${col}">●</span> ${c.name}`;
      pillWrap.appendChild(btn);
    });
  } catch {}
}

function applyAllPillStyles() {
  document.querySelectorAll('#all-cat-pills .pill').forEach(p => {
    const active = p.classList.contains('active');
    const cat = p.dataset.cat;
    if (active && cat) {
      const c = catColor(cat);
      p.style.cssText = `background:${c}28;border-color:${c}55;color:${c}`;
    } else if (active) {
      p.style.cssText = 'background:var(--accent);border-color:transparent;color:white';
    } else {
      p.style.cssText = '';
    }
  });
}

document.getElementById('all-cat-pills').addEventListener('click', e => {
  const btn = e.target.closest('.pill');
  if (!btn) return;
  allState.cat = btn.dataset.cat ?? '';
  document.querySelectorAll('#all-cat-pills .pill').forEach(p => p.classList.toggle('active', p === btn));
  applyAllPillStyles();
  loadAllPage();
});

let allSearchTimer;
document.getElementById('all-search').addEventListener('input', function() {
  clearTimeout(allSearchTimer);
  allSearchTimer = setTimeout(() => { allState.search = this.value.trim(); loadAllPage(); }, 280);
});
document.getElementById('all-filter-venue').addEventListener('change', function() {
  allState.venue = this.value; loadAllPage();
});
document.getElementById('all-sort').addEventListener('change', function() {
  allState.sort = this.value; loadAllPage();
});
document.getElementById('all-filter-free').addEventListener('change', function() {
  allState.free = this.checked; loadAllPage();
});
document.getElementById('all-date-from').addEventListener('change', function() {
  allState.dateFrom = this.value; loadAllPage();
});
document.getElementById('all-date-to').addEventListener('change', function() {
  allState.dateTo = this.value; loadAllPage();
});

document.getElementById('btn-more-all').addEventListener('click', async function() {
  state.allPage++;
  const data = await api('/events?' + buildAllParams());
  document.getElementById('all-rows')
    .insertAdjacentHTML('beforeend', (data.items ?? []).map(buildCardB).join(''));
  if (state.allPage >= (data.pages ?? 1)) this.classList.add('hidden');
});

// ── EVENT DETAIL page ──────────────────────────────────────────
function generateIcs(ev) {
  const d = new Date(ev.date);
  const pad = n => String(n).padStart(2, '0');
  const fmt = d => `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}T${pad(d.getHours())}${pad(d.getMinutes())}00`;
  const end = new Date(d.getTime() + 2 * 3600 * 1000);
  const esc = s => (s || '').replace(/\\/g,'\\\\').replace(/;/g,'\\;').replace(/,/g,'\\,').replace(/\n/g,'\\n');
  const uid = `${ev.id}-sorties-caen@caen.fr`;
  const lines = [
    'BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Sorties Caen//FR',
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${fmt(new Date())}`,
    `DTSTART:${fmt(d)}`,
    `DTEND:${fmt(end)}`,
    `SUMMARY:${esc(ev.title)}`,
    `LOCATION:${esc(ev.venue)}`,
    ev.description ? `DESCRIPTION:${esc(ev.description)}` : null,
    ev.event_url   ? `URL:${ev.event_url}` : (ev.booking_url ? `URL:${ev.booking_url}` : null),
    'END:VEVENT','END:VCALENDAR'
  ].filter(Boolean).join('\r\n');

  const blob = new Blob([lines], { type: 'text/calendar' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${ev.title.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 40)}.ics`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}

async function loadEvent(id) {
  const wrap = document.getElementById('event-detail');
  wrap.innerHTML = `
    <div class="detail-layout">
      <div><div class="skeleton" style="aspect-ratio:3/4;border-radius:14px;width:100%"></div></div>
      <div style="display:flex;flex-direction:column;gap:14px;padding-top:8px">
        <div class="skeleton" style="width:90px;height:24px;border-radius:99px"></div>
        <div class="skeleton" style="width:75%;height:40px"></div>
        <div class="skeleton" style="width:55%;height:20px"></div>
        <div class="skeleton" style="width:100%;height:110px;border-radius:12px"></div>
        <div class="skeleton" style="width:100%;height:80px"></div>
        <div class="skeleton" style="width:160px;height:46px;border-radius:11px"></div>
      </div>
    </div>`;
  try {
    const ev       = await api(`/events/${id}`);
    const color    = catColor(ev.category);
    const price    = fmtPrice(ev.price);
    const { name, subtitle } = splitTitle(ev);
    const dateOnly = fmtDateOnly(ev.date);
    const timeStr  = fmtTimeIfKnown(ev.date);
    const provider = bookingProvider(ev.booking_url);
    const provStr  = provider ? ` · billetterie ${provider}` : '';

    const posterHtml = ev.image_url
      ? `<img src="${ev.image_url}" alt="${name}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block">`
      : `<div class="detail-poster-fallback" style="background:linear-gradient(160deg,${color}55 0%,${color}18 100%)">
           <span class="detail-poster-initial">${name.charAt(0).toUpperCase()}</span>
         </div>`;

    const infoCells = [
      { label: 'DATE',      value: dateOnly },
      ...(timeStr             ? [{ label: 'HEURE',     value: timeStr }] : []),
      ...(ev.duration        ? [{ label: 'DURÉE',      value: ev.duration }] : []),
      { label: 'LIEU',      value: ev.venue },
      ...(price              ? [{ label: 'PRIX',       value: `<span class="${price === 'Gratuit' ? 'is-free' : ''}">${price}</span>` }] : []),
      ...(ev.placement       ? [{ label: 'PLACEMENT',  value: ev.placement }] : []),
    ];
    const infoGridHtml = infoCells.map(c =>
      `<div class="info-cell"><span class="info-label">${c.label}</span><span class="info-value">${c.value}</span></div>`
    ).join('');

    const practicalHtml = [
      ev.address    ? `<div class="detail-practical"><span class="detail-practical-label">Adresse</span><span>${ev.address}</span></div>` : '',
      ev.doors_open ? `<div class="detail-practical"><span class="detail-practical-label">Ouverture</span><span>${ev.doors_open}</span></div>` : '',
      ev.access_info? `<div class="detail-practical"><span class="detail-practical-label">Accès</span><span>${ev.access_info}</span></div>` : '',
    ].filter(Boolean).join('');

    wrap.innerHTML = `
    <div class="detail-layout">
      <div class="detail-col-left">
        <div class="detail-poster">${posterHtml}</div>
        ${ev.booking_url
          ? `<a class="btn-cta detail-action-btn" href="${ev.booking_url}" target="_blank" rel="noopener">Réserver des billets ${ICO_ARR}</a>`
          : ''}
        <button class="btn-cta btn-cta-secondary detail-action-btn" id="btn-ics">
          ${ICO_CAL} Ajouter à mon agenda
        </button>
        <div class="detail-source">
          Source : <strong>${ev.venue}</strong>${provStr}
          <span class="detail-added">${fmtRelative(ev.first_seen)}</span>
        </div>
      </div>
      <div class="detail-col-right">
        <div class="detail-badges">
          ${ev.category ? badgeCat(ev.category) : ''}
          ${ev.is_new ? '<span class="badge-new">NOUVEAU</span>' : ''}
        </div>
        <h1 class="detail-name">${name}</h1>
        ${subtitle ? `<p class="detail-subtitle-text">${subtitle}</p>` : ''}
        <div class="detail-info-grid">${infoGridHtml}</div>
        ${ev.description ? `<div class="detail-section"><h3>À propos</h3><p>${ev.description}</p></div>` : ''}
        ${practicalHtml ? `<div class="detail-section"><h3>Infos pratiques</h3>${practicalHtml}</div>` : ''}
      </div>
    </div>`;
    document.getElementById('btn-ics').addEventListener('click', () => generateIcs(ev));
  } catch {
    wrap.innerHTML = '<p class="empty-state">Événement introuvable ou supprimé.</p>';
  }
}

document.getElementById('btn-back').addEventListener('click', () => history.back());

// ── Mobile hamburger ───────────────────────────────────────────
const hamburger = document.getElementById('btn-hamburger');
const mobileNav = document.getElementById('mobile-nav-overlay');

function openMobileNav() {
  mobileNav.classList.remove('hidden');
  mobileNav.setAttribute('aria-hidden', 'false');
  hamburger.setAttribute('aria-expanded', 'true');
  hamburger.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeMobileNav() {
  mobileNav.classList.add('hidden');
  mobileNav.setAttribute('aria-hidden', 'true');
  hamburger.setAttribute('aria-expanded', 'false');
  hamburger.classList.remove('open');
  document.body.style.overflow = '';
}

hamburger.addEventListener('click', () =>
  mobileNav.classList.contains('hidden') ? openMobileNav() : closeMobileNav()
);
mobileNav.addEventListener('click', e => {
  if (e.target.closest('.mobile-nav-link') || e.target === mobileNav) closeMobileNav();
});

// ── Router ─────────────────────────────────────────────────────
const PAGES = ['radar','nouveautes','calendrier','sorties','event'];
let  prevPage = null;

function getRoute() {
  const hash = location.hash.replace(/^#\/?/, '');
  const [page, ...rest] = hash.split('/');
  return { page: PAGES.includes(page) ? page : 'radar', param: rest[0] ?? null };
}
function navigate(path) { location.hash = '#/' + path; }
function setActiveNav(page) {
  document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(el =>
    el.classList.toggle('active', el.dataset.route === page)
  );
}

// Delegated click: card or row → detail
document.addEventListener('click', e => {
  const el = e.target.closest('[data-id]');
  if (el && !e.target.closest('a')) navigate('event/' + el.dataset.id);
});

async function route() {
  closeMobileNav();
  const { page, param } = getRoute();
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  setActiveNav(page);

  if (page === 'radar') {
    document.getElementById('page-radar').classList.remove('hidden');
    if (prevPage !== 'radar') await loadRadar();

  } else if (page === 'calendrier') {
    document.getElementById('page-calendrier').classList.remove('hidden');
    if (prevPage !== 'calendrier') initCalendar();

  } else if (page === 'nouveautes') {
    document.getElementById('page-nouveautes').classList.remove('hidden');
    if (prevPage !== 'nouveautes') await loadNouveautes();

  } else if (page === 'sorties') {
    document.getElementById('page-sorties').classList.remove('hidden');
    if (prevPage !== 'sorties') await loadAllPage();

  } else if (page === 'event') {
    document.getElementById('page-event').classList.remove('hidden');
    await loadEvent(param);
  }

  prevPage = page;
}

window.addEventListener('hashchange', route);

// ── Init ────────────────────────────────────────────────────────
(async function init() {
  initTheme();
  await Promise.all([refreshNavbar(), populateVenueSelect(), populateCategoryPills(), populateAllFilters()]);
  // Activate "Tout" pill
  const allPill = document.querySelector('#category-pills .pill[data-cat=""]');
  if (allPill) { allPill.classList.add('active'); applyPillStyles(); }
  if (!location.hash || location.hash === '#' || location.hash === '#/') {
    location.hash = '#/radar';
  }
  await route();
})();
