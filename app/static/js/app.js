/* ============================================================
   Sorties Caen — Frontend
   ============================================================ */

// ── Design tokens ─────────────────────────────────────────────
const CAT_COLORS = {
  musique:  '#7C5CFB',
  théâtre:  '#E5484D',
  theatre:  '#E5484D',
  humour:   '#F5A524',
  danse:    '#E93D82',
  expo:     '#2F9CF4',
  enfants:  '#30A46C',
  sport:    '#F76808',
  brocante: '#12A594',
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
function fmtRelative(iso) {
  const s = (Date.now() - new Date(iso)) / 1000;
  if (s < 3600)   return `Ajouté il y a ${Math.round(s/60)} min`;
  if (s < 86400)  return `Ajouté il y a ${Math.round(s/3600)} h`;
  if (s < 172800) return 'Ajouté hier';
  return `Ajouté il y a ${Math.round(s/86400)} j`;
}
function fmtScrapeAge(iso) {
  const s = (Date.now() - new Date(iso)) / 1000;
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

// ── SVG icons ─────────────────────────────────────────────────
const ICO_CAL  = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;
const ICO_PIN  = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>`;
const ICO_ARR  = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M7 17 17 7M17 7H7M17 7v10"/></svg>`;

// ── HTML components ────────────────────────────────────────────
function badgeCat(cat) {
  const c = catColor(cat);
  return `<span class="badge-cat" style="--cat-color:${c}">${cat}</span>`;
}

function buildCard(ev) {
  const color = catColor(ev.category);
  const price = fmtPrice(ev.price);
  const isNew = ev.is_new;

  const imgPart = ev.image_url
    ? `<img src="${ev.image_url}" alt="" loading="lazy" /><div class="card-img-overlay"></div>`
    : `<div class="card-img-fallback" style="background:linear-gradient(135deg,${color}55 0%,${color}11 100%)"></div>`;

  return `<div class="card" data-id="${ev.id}">
    <div class="card-visual">
      ${imgPart}
      <div class="card-top-badges">
        ${ev.category ? badgeCat(ev.category) : ''}
        ${isNew ? '<span class="badge-new">NOUVEAU</span>' : ''}
      </div>
    </div>
    <div class="card-body">
      <span class="card-added">${fmtRelative(ev.first_seen)}</span>
      <h3 class="card-title">${ev.title}</h3>
      <div class="card-meta">${ICO_CAL} ${fmtDateTime(ev.date)}</div>
      <div class="card-meta">${ICO_PIN} ${ev.venue}</div>
    </div>
    <div class="card-footer">
      <span class="card-price${price === 'Gratuit' ? ' is-free' : ''}">${price || '—'}</span>
      ${ev.booking_url
        ? `<a class="card-book" href="${ev.booking_url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Billetterie ${ICO_ARR}</a>`
        : ''}
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
    const badge = document.getElementById('bell-badge');
    if (s.count_new_7d > 0) {
      badge.textContent = s.count_new_7d;
      badge.classList.remove('hidden');
    }
  } catch {}
}
document.getElementById('btn-bell').addEventListener('click', () => navigate('radar'));

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
  document.getElementById('new-cards').innerHTML = shown.map(buildCard).join('');
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
      grid.innerHTML = items.map(buildCard).join('');
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

// ── RADAR page ─────────────────────────────────────────────────
async function loadRadar() {
  await loadNewBanner();
  await Promise.all([loadNewEvents(), loadWeekend(), loadUpcoming()]);
  // Save visit timestamp for next time (on unload would be ideal but unreliable on mobile)
  localStorage.setItem('lastVisit', new Date().toISOString());
}

// ── CALENDAR page ──────────────────────────────────────────────
function buildCalLegend() {
  const wrap = document.getElementById('cal-legend');
  wrap.innerHTML = '';
  // Deduplicate (théâtre/theatre)
  const seen = new Set();
  Object.entries(CAT_COLORS).forEach(([name, color]) => {
    if (seen.has(color)) return;
    seen.add(color);
    const label = name.charAt(0).toUpperCase() + name.slice(1);
    wrap.insertAdjacentHTML('beforeend',
      `<span class="cal-legend-item"><span class="cal-legend-dot" style="background:${color}"></span>${label}</span>`);
  });
}

async function renderCalendar() {
  const mm = String(state.calMonth).padStart(2, '0');
  const monthName = MONTHS[state.calMonth-1];
  document.getElementById('cal-month-label').textContent =
    `${monthName.charAt(0).toUpperCase() + monthName.slice(1)} ${state.calYear}`;

  let days = [];
  try { days = await api(`/calendar?month=${state.calYear}-${mm}`); } catch {}
  const byDay = Object.fromEntries(days.map(d => [d.date, d.events]));

  const grid = document.getElementById('cal-grid');
  grid.innerHTML = '';

  const firstDow = new Date(state.calYear, state.calMonth-1, 1).getDay();
  const offset   = firstDow === 0 ? 6 : firstDow - 1;
  const dimMonth = new Date(state.calYear, state.calMonth, 0).getDate();
  const prevDim  = new Date(state.calYear, state.calMonth-1, 0).getDate();
  const today    = new Date().toISOString().slice(0,10);

  const cells = [];
  for (let i = offset-1; i >= 0; i--) cells.push({ day: prevDim-i, date: null, other: true });
  for (let d = 1; d <= dimMonth; d++) {
    cells.push({ day: d, date: `${state.calYear}-${mm}-${String(d).padStart(2,'0')}`, other: false });
  }
  const rem = (7 - cells.length % 7) % 7;
  for (let d = 1; d <= rem; d++) cells.push({ day: d, date: null, other: true });

  cells.forEach(({ day, date, other }) => {
    const evts = date ? (byDay[date] ?? []) : [];
    const cell = document.createElement('div');
    cell.className = ['cal-cell',
      other      ? 'other-month' : '',
      date === today ? 'today' : '',
      evts.length    ? 'has-events' : '',
    ].filter(Boolean).join(' ');

    const chips = evts.slice(0,3).map(ev => {
      const c = catColor(ev.category);
      return `<span class="cal-chip" style="background:${c}22;color:${c}">${ev.title}</span>`;
    }).join('') + (evts.length > 3 ? `<span class="cal-chip muted">+${evts.length-3}</span>` : '');

    cell.innerHTML = `<div class="cal-num">${day}</div>${chips}`;
    if (evts.length && date) {
      cell.addEventListener('click', () => {
        navigate('sorties');
        setTimeout(() => loadAllPage({ date_from: date, date_to: date }), 60);
      });
    }
    grid.appendChild(cell);
  });
}

document.getElementById('cal-prev').addEventListener('click', () => {
  if (--state.calMonth < 1) { state.calMonth = 12; state.calYear--; }
  renderCalendar();
});
document.getElementById('cal-next').addEventListener('click', () => {
  if (++state.calMonth > 12) { state.calMonth = 1; state.calYear++; }
  renderCalendar();
});

function initCalendar() {
  buildCalLegend();
  renderCalendar();
}

// ── ALL SORTIES page ───────────────────────────────────────────
function buildAllParams(overrides = {}) {
  const params = new URLSearchParams({ sort: 'date', page: state.allPage, page_size: 30 });
  if (state.cat)    params.set('category', state.cat);
  if (state.venue)  params.set('venue', state.venue);
  if (state.search) params.set('search', state.search);
  Object.entries(overrides).forEach(([k,v]) => params.set(k, v));
  return params;
}

async function loadAllPage(overrides = {}) {
  state.allPage = 1;
  const wrap = document.getElementById('all-rows');
  const meta = document.getElementById('all-meta');
  wrap.innerHTML = '';
  try {
    const data = await api('/events?' + buildAllParams(overrides));
    const items = data.items ?? [];
    const total = data.total ?? items.length;
    meta.textContent = `${total} événement${total !== 1 ? 's' : ''}`;
    wrap.innerHTML = items.map(buildRow).join('');
    const btn = document.getElementById('btn-more-all');
    btn.classList.toggle('hidden', (data.pages ?? 1) <= 1);
  } catch {
    wrap.innerHTML = '<p class="empty-state">Impossible de charger.</p>';
  }
}

document.getElementById('btn-more-all').addEventListener('click', async function() {
  state.allPage++;
  const data = await api('/events?' + buildAllParams());
  document.getElementById('all-rows')
    .insertAdjacentHTML('beforeend', (data.items ?? []).map(buildRow).join(''));
  if (state.allPage >= (data.pages ?? 1)) this.classList.add('hidden');
});

// ── EVENT DETAIL page ──────────────────────────────────────────
async function loadEvent(id) {
  const wrap = document.getElementById('event-detail');
  wrap.innerHTML = '<p class="empty-state">Chargement…</p>';
  try {
    const ev = await api(`/events/${id}`);
    const color = catColor(ev.category);
    const price = fmtPrice(ev.price);
    wrap.innerHTML = `
    <div class="detail-card">
      ${ev.image_url
        ? `<img class="detail-img" src="${ev.image_url}" alt="${ev.title}">`
        : `<div class="detail-img-fallback" style="background:linear-gradient(135deg,${color}44,${color}11)"></div>`}
      <div class="detail-body">
        <div class="detail-badges">
          ${ev.category ? badgeCat(ev.category) : ''}
          ${ev.is_new ? '<span class="badge-new">NOUVEAU</span>' : ''}
        </div>
        <h1 class="detail-title">${ev.title}</h1>
        <div class="detail-metas">
          <div class="detail-meta">${ICO_CAL} <strong>${fmtDateTime(ev.date)}</strong></div>
          <div class="detail-meta">${ICO_PIN} ${ev.venue}</div>
          ${price ? `<div class="detail-meta">🎟 <strong>${price}</strong></div>` : ''}
        </div>
        ${ev.description ? `<p class="detail-desc">${ev.description}</p>` : ''}
        ${ev.booking_url
          ? `<a class="btn-cta" href="${ev.booking_url}" target="_blank" rel="noopener">Réserver ${ICO_ARR}</a>`
          : ''}
      </div>
    </div>`;
  } catch {
    wrap.innerHTML = '<p class="empty-state">Événement introuvable.</p>';
  }
}

document.getElementById('btn-back').addEventListener('click', () => history.back());

// ── Router ─────────────────────────────────────────────────────
const PAGES = ['radar','calendrier','sorties','event'];
let  prevPage = null;

function getRoute() {
  const hash = location.hash.replace(/^#\/?/, '');
  const [page, ...rest] = hash.split('/');
  return { page: PAGES.includes(page) ? page : 'radar', param: rest[0] ?? null };
}
function navigate(path) { location.hash = '#/' + path; }
function setActiveNav(page) {
  document.querySelectorAll('.nav-link').forEach(el =>
    el.classList.toggle('active', el.dataset.route === page)
  );
}

// Delegated click: card or row → detail
document.addEventListener('click', e => {
  const el = e.target.closest('[data-id]');
  if (el && !e.target.closest('a')) navigate('event/' + el.dataset.id);
});

async function route() {
  const { page, param } = getRoute();
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  setActiveNav(page);

  if (page === 'radar') {
    document.getElementById('page-radar').classList.remove('hidden');
    if (prevPage !== 'radar') await loadRadar();

  } else if (page === 'calendrier') {
    document.getElementById('page-calendrier').classList.remove('hidden');
    if (prevPage !== 'calendrier') initCalendar();

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
  await Promise.all([refreshNavbar(), populateVenueSelect(), populateCategoryPills()]);
  // Activate "Tout" pill
  const allPill = document.querySelector('#category-pills .pill[data-cat=""]');
  if (allPill) { allPill.classList.add('active'); applyPillStyles(); }
  if (!location.hash || location.hash === '#' || location.hash === '#/') {
    location.hash = '#/radar';
  }
  await route();
})();
