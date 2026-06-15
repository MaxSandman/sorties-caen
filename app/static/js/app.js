/* ============================================================
   Sorties Caen — Frontend JS
   ============================================================ */

// ── Design tokens : catégories ────────────────────────────────
const CAT_COLORS = {
  musique:   '#7C5CFB',
  théâtre:   '#E5484D',
  theatre:   '#E5484D',
  humour:    '#F5A524',
  danse:     '#E93D82',
  expo:      '#2F9CF4',
  enfants:   '#30A46C',
  sport:     '#F76808',
  brocante:  '#12A594',
};

function catColor(cat) {
  if (!cat) return '#93A0B8';
  return CAT_COLORS[cat.toLowerCase().trim()] ?? '#93A0B8';
}

// ── API helpers ───────────────────────────────────────────────
async function api(path) {
  const res = await fetch('/api' + path);
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json();
}

// ── Date formatters ───────────────────────────────────────────
const DAYS_FR   = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
const MONTHS_FR = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
const MONTHS_FR_LONG = MONTHS_FR;

function fmtDate(iso) {
  const d = new Date(iso);
  return `${DAYS_FR[d.getDay()]} ${d.getDate()} ${MONTHS_FR[d.getMonth()]}`;
}
function fmtDateFull(iso) {
  const d = new Date(iso);
  return `${DAYS_FR[d.getDay()]} ${d.getDate()} ${MONTHS_FR[d.getMonth()]} · ${fmtTime(iso)}`;
}
function fmtTime(iso) {
  const d = new Date(iso);
  const h = d.getHours(), m = d.getMinutes();
  return `${h}h${m.toString().padStart(2,'0')}`;
}
function fmtRelative(iso) {
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 3600)   return `Ajouté il y a ${Math.round(diff/60)} min`;
  if (diff < 86400)  return `Ajouté il y a ${Math.round(diff/3600)} h`;
  if (diff < 172800) return 'Ajouté hier';
  return `Ajouté il y a ${Math.round(diff/86400)} j`;
}
function fmtRelativeShort(iso) {
  // For stats "Mis à jour il y a X"
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60)    return 'Mis à jour à l\'instant';
  if (diff < 3600)  return `Mis à jour il y a ${Math.round(diff/60)} min`;
  if (diff < 86400) return `Mis à jour il y a ${Math.round(diff/3600)} h`;
  return `Mis à jour il y a ${Math.round(diff/86400)} j`;
}
function fmtPrice(price) {
  if (!price) return '';
  const low = price.toLowerCase().trim();
  if (['gratuit','free','0','0€','0 €','entrée libre','libre'].includes(low)) return 'Gratuit';
  return price;
}

// ── HTML helpers ──────────────────────────────────────────────
function badgeCat(cat) {
  const color = catColor(cat);
  return `<span class="badge-cat" style="--cat-color:${color}">${cat ?? ''}</span>`;
}
function badgeNew() {
  return `<span class="badge-new">Nouveau</span>`;
}
function iconCal() {
  return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;
}
function iconPin() {
  return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>`;
}
function iconArrow() {
  return `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M7 17 17 7M17 7H7M17 7v10"/></svg>`;
}

// ── Card builder ──────────────────────────────────────────────
function buildCard(ev) {
  const color = catColor(ev.category);
  const price = fmtPrice(ev.price);
  const hasImg = !!ev.image_url;
  const imgHtml = hasImg
    ? `<img src="${ev.image_url}" alt="" loading="lazy" />`
    : '';
  const added = fmtRelative(ev.first_seen);

  return `
  <div class="card" data-id="${ev.id}">
    <div class="card-img${hasImg ? '' : ' no-img'}" style="--cat-color:${color}">
      ${imgHtml}
      <div class="card-img-gradient"></div>
      <div class="card-badges">
        ${ev.category ? badgeCat(ev.category) : ''}
        ${ev.is_new ? badgeNew() : ''}
      </div>
    </div>
    <div class="card-body">
      <span class="card-added">${added}</span>
      <div class="card-title">${ev.title}</div>
      <div class="card-date">${iconCal()} ${fmtDateFull(ev.date)}</div>
      <div class="card-venue">${iconPin()} ${ev.venue}</div>
    </div>
    <div class="card-footer">
      <span class="card-price${price === 'Gratuit' ? ' free' : ''}">${price}</span>
      ${ev.booking_url ? `<a class="card-book" href="${ev.booking_url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Billetterie ${iconArrow()}</a>` : ''}
    </div>
  </div>`;
}

// ── List row builder ──────────────────────────────────────────
function buildRow(ev) {
  const color = catColor(ev.category);
  const price = fmtPrice(ev.price);
  return `
  <div class="list-row" data-id="${ev.id}">
    <div class="list-row-date">
      <span class="list-row-bar" style="background:${color}"></span>
      ${fmtDate(ev.date)}<br><small>${ev.time || fmtTime(ev.date)}</small>
    </div>
    <div class="list-row-info">
      <div class="list-row-title">${ev.title}</div>
      <div class="list-row-venue">${ev.venue}</div>
    </div>
    <div class="list-row-badge">${ev.category ? badgeCat(ev.category) : ''}</div>
    <div class="list-row-right">
      <span class="list-row-price">${price}</span>
      ${ev.booking_url ? `<a class="list-row-link" href="${ev.booking_url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Billetterie ${iconArrow()}</a>` : ''}
    </div>
  </div>`;
}

// ── Router ────────────────────────────────────────────────────
const PAGES = ['radar', 'calendrier', 'sorties', 'event'];

function getRoute() {
  const hash = location.hash.replace('#/', '');
  if (!hash) return { page: 'radar', param: null };
  const [page, ...rest] = hash.split('/');
  return { page: PAGES.includes(page) ? page : 'radar', param: rest[0] ?? null };
}

function navigate(path) {
  location.hash = '#/' + path;
}

function setActiveNav(page) {
  document.querySelectorAll('.nav-link').forEach(el => {
    el.classList.toggle('active', el.dataset.route === page);
  });
}

// ── Delegated card/row click → event detail ───────────────────
document.addEventListener('click', e => {
  const card = e.target.closest('[data-id]');
  if (card && !e.target.closest('a')) {
    navigate('event/' + card.dataset.id);
  }
});

// ── State ─────────────────────────────────────────────────────
let currentSort  = 'added';
let currentCat   = '';
let currentVenue = '';
let currentDate  = '';
let searchQuery  = '';
let calYear, calMonth;
let newPageSize  = 8;
let upcomingPage = 1;
let allPage      = 1;
let lastVisit    = localStorage.getItem('lastVisit');
let newCount     = 0;

// ── Navbar: theme + last update + bell ───────────────────────
function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.dataset.theme = saved;
}
document.getElementById('btn-theme').addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('theme', next);
});

async function loadStats() {
  try {
    const s = await api('/stats');
    newCount = s.count_new_7d;
    const el = document.getElementById('last-update');
    el.textContent = s.last_scrape_at ? fmtRelativeShort(s.last_scrape_at) : '';
    const badge = document.getElementById('bell-badge');
    if (newCount > 0) {
      badge.textContent = newCount;
      badge.classList.remove('hidden');
    }
  } catch {}
}

document.getElementById('btn-bell').addEventListener('click', () => navigate('radar'));
document.getElementById('btn-ntfy').classList.remove('hidden'); // assume ntfy configured

// ── Venues → select ──────────────────────────────────────────
async function loadVenues() {
  try {
    const venues = await api('/venues');
    const sel = document.getElementById('filter-venue');
    venues.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.key;
      opt.textContent = `${v.name} (${v.count})`;
      sel.appendChild(opt);
    });
  } catch {}
}

// ── Category pills ───────────────────────────────────────────
async function loadCategoryPills() {
  try {
    const cats = await api('/categories');
    const wrap = document.getElementById('category-pills');
    cats.forEach(c => {
      const color = catColor(c.name);
      const btn = document.createElement('button');
      btn.className = 'pill';
      btn.dataset.cat = c.name;
      btn.innerHTML = `<span style="color:${color}">●</span> ${c.name}`;
      btn.style.setProperty('--cat-color', color);
      wrap.appendChild(btn);
    });
    wrap.addEventListener('click', e => {
      const btn = e.target.closest('.pill');
      if (!btn) return;
      currentCat = btn.dataset.cat;
      wrap.querySelectorAll('.pill').forEach(p => {
        p.classList.toggle('active', p === btn);
        if (p === btn && p.dataset.cat) {
          p.style.background = color_mix(catColor(p.dataset.cat));
          p.style.borderColor = 'transparent';
          p.style.color = 'white';
        } else {
          p.style.background = '';
          p.style.borderColor = '';
          p.style.color = '';
        }
      });
      refreshRadar();
    });
  } catch {}
}

function color_mix(hex) {
  // Returns a semi-transparent version for active pill bg
  return hex + '33';
}

// ── Pill active style helper ──────────────────────────────────
function styleActivePill(wrap) {
  wrap.querySelectorAll('.pill').forEach(p => {
    const active = p.classList.contains('active');
    if (active && p.dataset.cat) {
      const c = catColor(p.dataset.cat);
      p.style.background = c + '33';
      p.style.borderColor = c + '55';
      p.style.color = c;
    } else if (active) {
      p.style.background = 'var(--accent)';
      p.style.borderColor = 'transparent';
      p.style.color = 'white';
    } else {
      p.style.background = '';
      p.style.borderColor = '';
      p.style.color = '';
    }
  });
}

// ── RADAR ─────────────────────────────────────────────────────
async function loadRadar() {
  await Promise.all([loadNewSection(), loadWeekendSection(), loadUpcomingSection()]);
  // Save last visit
  localStorage.setItem('lastVisit', new Date().toISOString());
}

async function loadNewSection() {
  const cards = document.getElementById('new-cards');
  const meta  = document.getElementById('new-meta');
  cards.innerHTML = '';
  try {
    const sort = currentSort === 'added' ? 'added' : 'date';
    const params = new URLSearchParams({ days: 30, sort });
    if (currentCat)   params.set('category', currentCat);
    if (currentVenue) params.set('venue', currentVenue);
    if (searchQuery)  params.set('search', searchQuery);

    const data = await api('/events?sort=added&days=30&' + params.toString());
    // data is PaginatedEvents
    const items = data.items ?? data;
    const shown = items.slice(0, newPageSize);

    meta.textContent = `triées par ${currentSort === 'added' ? "date d'ajout" : "date de l'événement"} · ${items.length} résultat${items.length > 1 ? 's' : ''}`;
    cards.innerHTML = shown.map(buildCard).join('');

    const btnMore = document.getElementById('btn-more-new');
    if (items.length > newPageSize) {
      btnMore.classList.remove('hidden');
      btnMore._items = items;
    } else {
      btnMore.classList.add('hidden');
    }
  } catch (err) {
    cards.innerHTML = '<p class="empty-state">Impossible de charger les événements.</p>';
  }
}

async function loadWeekendSection() {
  const cards = document.getElementById('weekend-cards');
  const meta  = document.getElementById('weekend-meta');
  const empty = document.getElementById('weekend-empty');
  cards.innerHTML = '';
  try {
    const items = await api('/events/weekend');
    let filtered = items;
    if (currentCat)   filtered = filtered.filter(e => e.category?.toLowerCase() === currentCat.toLowerCase());
    if (currentVenue) filtered = filtered.filter(e => e.venue_key === currentVenue);
    if (searchQuery)  filtered = filtered.filter(e =>
      e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.venue.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Build date label e.g. "Ven 28 — Dim 30 mars"
    if (items.length > 0) {
      const d0 = new Date(items[0].date), d1 = new Date(items[items.length-1].date);
      meta.textContent = `${DAYS_FR[d0.getDay()]} ${d0.getDate()} — ${DAYS_FR[d1.getDay()]} ${d1.getDate()} ${MONTHS_FR[d1.getMonth()]}`;
    }
    if (filtered.length === 0) {
      empty.classList.remove('hidden');
    } else {
      empty.classList.add('hidden');
      cards.innerHTML = filtered.map(buildCard).join('');
    }
  } catch {}
}

async function loadUpcomingSection() {
  const rows = document.getElementById('upcoming-rows');
  rows.innerHTML = '';
  try {
    const params = new URLSearchParams({ sort: 'date', page: 1, page_size: 20 });
    if (currentCat)   params.set('category', currentCat);
    if (currentVenue) params.set('venue', currentVenue);
    if (searchQuery)  params.set('search', searchQuery);

    const data = await api('/events?' + params.toString());
    const items = data.items ?? data;
    rows.innerHTML = items.map(buildRow).join('');

    const btnMore = document.getElementById('btn-more-upcoming');
    if ((data.pages ?? 1) > 1) {
      btnMore.classList.remove('hidden');
      btnMore._page = 1;
      btnMore._params = params;
    } else {
      btnMore.classList.add('hidden');
    }
  } catch {}
}

function refreshRadar() {
  loadNewSection();
  loadWeekendSection();
  loadUpcomingSection();
}

// ── Sort toggle ───────────────────────────────────────────────
document.getElementById('sort-added').addEventListener('click', function() {
  currentSort = 'added';
  this.classList.add('active');
  document.getElementById('sort-date').classList.remove('active');
  loadNewSection();
});
document.getElementById('sort-date').addEventListener('click', function() {
  currentSort = 'date';
  this.classList.add('active');
  document.getElementById('sort-added').classList.remove('active');
  loadNewSection();
});

// ── More buttons ──────────────────────────────────────────────
document.getElementById('btn-more-new').addEventListener('click', function() {
  const items = this._items || [];
  newPageSize += 8;
  const shown = items.slice(0, newPageSize);
  document.getElementById('new-cards').innerHTML = shown.map(buildCard).join('');
  if (newPageSize >= items.length) this.classList.add('hidden');
});

document.getElementById('btn-more-upcoming').addEventListener('click', async function() {
  const params = this._params;
  params.set('page', ++this._page);
  const data = await api('/events?' + params.toString());
  const items = data.items ?? data;
  document.getElementById('upcoming-rows').insertAdjacentHTML('beforeend', items.map(buildRow).join(''));
  if (this._page >= (data.pages ?? 1)) this.classList.add('hidden');
});

document.getElementById('btn-more-all').addEventListener('click', async function() {
  allPage++;
  const params = buildAllParams();
  params.set('page', allPage);
  const data = await api('/events?' + params.toString());
  const items = data.items ?? data;
  document.getElementById('all-rows').insertAdjacentHTML('beforeend', items.map(buildRow).join(''));
  if (allPage >= (data.pages ?? 1)) this.classList.add('hidden');
});

// ── Filters ───────────────────────────────────────────────────
let searchTimer;
document.getElementById('search-input').addEventListener('input', function() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    searchQuery = this.value.trim();
    refreshRadar();
    if (document.getElementById('page-sorties').classList.contains('page') &&
        !document.getElementById('page-sorties').classList.contains('hidden')) {
      loadAllPage();
    }
  }, 280);
});

document.getElementById('filter-venue').addEventListener('change', function() {
  currentVenue = this.value;
  refreshRadar();
});

document.getElementById('filter-date').addEventListener('change', function() {
  currentDate = this.value;
  refreshRadar();
});

// ── New banner ────────────────────────────────────────────────
async function loadNewBanner() {
  try {
    const s = await api('/stats');
    const count = s.count_new_7d;
    if (count <= 0) return;
    const banner = document.getElementById('new-banner');
    const title  = document.getElementById('new-banner-title');
    const sub    = document.getElementById('new-banner-sub');
    title.textContent = `${count} nouveaux événement${count > 1 ? 's' : ''} depuis ta dernière visite`;
    if (lastVisit) {
      const diff = Math.round((Date.now() - new Date(lastVisit)) / 86400000);
      sub.textContent = diff === 0 ? "Dernier passage aujourd'hui · les petites salles partent vite, ne traîne pas."
                      : diff === 1 ? "Dernier passage hier · les petites salles partent vite, ne traîne pas."
                      : `Dernier passage il y a ${diff} jours · les petites salles partent vite, ne traîne pas.`;
    }
    banner.classList.remove('hidden');
  } catch {}
}

// ── CALENDAR ─────────────────────────────────────────────────
function initCalendar() {
  const now = new Date();
  calYear  = now.getFullYear();
  calMonth = now.getMonth() + 1;
  renderCalendar();
  buildCalLegend();
}

async function renderCalendar() {
  const label = document.getElementById('cal-month-label');
  const mm = String(calMonth).padStart(2, '0');
  label.textContent = `${MONTHS_FR_LONG[calMonth-1].charAt(0).toUpperCase() + MONTHS_FR_LONG[calMonth-1].slice(1)} ${calYear}`;

  let days = [];
  try {
    days = await api(`/calendar?month=${calYear}-${mm}`);
  } catch {}

  // Build day map
  const byDay = {};
  days.forEach(d => { byDay[d.date] = d.events; });

  const grid = document.getElementById('cal-grid');
  grid.innerHTML = '';

  // First day of month (Monday=0)
  const first = new Date(calYear, calMonth-1, 1).getDay();
  const startOffset = (first === 0 ? 6 : first - 1); // Mon-based
  const daysInMonth = new Date(calYear, calMonth, 0).getDate();
  const prevDays    = new Date(calYear, calMonth-1, 0).getDate();

  const today = new Date().toISOString().slice(0,10);
  let cells = [];

  // Prev month padding
  for (let i = startOffset - 1; i >= 0; i--) {
    cells.push({ day: prevDays - i, dateStr: null, other: true });
  }
  // Current month
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${calYear}-${mm}-${String(d).padStart(2,'0')}`;
    cells.push({ day: d, dateStr, other: false });
  }
  // Next month padding
  const remaining = 7 - (cells.length % 7);
  if (remaining < 7) {
    for (let d = 1; d <= remaining; d++) cells.push({ day: d, dateStr: null, other: true });
  }

  cells.forEach(({ day, dateStr, other }) => {
    const evts = dateStr ? (byDay[dateStr] || []) : [];
    const isToday = dateStr === today;
    const div = document.createElement('div');
    div.className = 'cal-cell' +
      (other ? ' other-month' : '') +
      (isToday ? ' today' : '') +
      (evts.length ? ' has-events' : '');

    let chips = evts.slice(0, 3).map(ev => {
      const c = catColor(ev.category);
      return `<span class="cal-event-chip" style="background:${c}22;color:${c}">${ev.title}</span>`;
    }).join('');
    if (evts.length > 3) chips += `<span class="cal-event-chip" style="color:var(--text-muted)">+${evts.length-3}</span>`;

    div.innerHTML = `<div class="cal-day-num">${day}</div>${chips}`;

    if (evts.length && dateStr) {
      div.addEventListener('click', () => {
        navigate('sorties');
        setTimeout(() => {
          loadAllPage({ date_from: dateStr, date_to: dateStr });
        }, 50);
      });
    }
    grid.appendChild(div);
  });
}

function buildCalLegend() {
  const wrap = document.getElementById('cal-legend');
  Object.entries(CAT_COLORS).slice(0, 8).forEach(([name, color]) => {
    const item = document.createElement('span');
    item.className = 'cal-legend-item';
    item.innerHTML = `<span class="cal-legend-dot" style="background:${color}"></span>${name.charAt(0).toUpperCase()+name.slice(1)}`;
    wrap.appendChild(item);
  });
}

document.getElementById('cal-prev').addEventListener('click', () => {
  calMonth--;
  if (calMonth < 1) { calMonth = 12; calYear--; }
  renderCalendar();
});
document.getElementById('cal-next').addEventListener('click', () => {
  calMonth++;
  if (calMonth > 12) { calMonth = 1; calYear++; }
  renderCalendar();
});

// ── ALL SORTIES ───────────────────────────────────────────────
function buildAllParams(overrides = {}) {
  const params = new URLSearchParams({ sort: 'date', page: allPage, page_size: 30 });
  if (currentCat)   params.set('category', currentCat);
  if (currentVenue) params.set('venue', currentVenue);
  if (searchQuery)  params.set('search', searchQuery);
  Object.entries(overrides).forEach(([k,v]) => params.set(k, v));
  return params;
}

async function loadAllPage(overrides = {}) {
  allPage = 1;
  const rows = document.getElementById('all-rows');
  const meta = document.getElementById('all-meta');
  rows.innerHTML = '';
  try {
    const params = buildAllParams(overrides);
    const data = await api('/events?' + params.toString());
    const items = data.items ?? data;
    meta.textContent = `${data.total ?? items.length} événement${(data.total ?? items.length) > 1 ? 's' : ''}`;
    rows.innerHTML = items.map(buildRow).join('');
    const btn = document.getElementById('btn-more-all');
    if ((data.pages ?? 1) > 1) btn.classList.remove('hidden');
    else btn.classList.add('hidden');
  } catch {
    rows.innerHTML = '<p class="empty-state">Impossible de charger.</p>';
  }
}

// ── EVENT DETAIL ─────────────────────────────────────────────
async function loadEventDetail(id) {
  const wrap = document.getElementById('event-detail');
  wrap.innerHTML = '<p class="empty-state">Chargement…</p>';
  try {
    const ev = await api(`/events/${id}`);
    const color = catColor(ev.category);
    const price = fmtPrice(ev.price);
    wrap.innerHTML = `
    <div class="event-detail-card">
      ${ev.image_url ? `<img class="event-detail-img" src="${ev.image_url}" alt="${ev.title}" />` : `<div style="height:120px;background:linear-gradient(135deg,${color}33,${color}11)"></div>`}
      <div class="event-detail-body">
        <div class="event-detail-badges">
          ${ev.category ? badgeCat(ev.category) : ''}
          ${ev.is_new ? badgeNew() : ''}
        </div>
        <h1 class="event-detail-title">${ev.title}</h1>
        <div class="event-detail-meta">
          <div class="event-detail-meta-row">${iconCal()} <strong>${fmtDateFull(ev.date)}</strong></div>
          <div class="event-detail-meta-row">${iconPin()} ${ev.venue}</div>
          ${price ? `<div class="event-detail-meta-row">🎟 <strong>${price}</strong></div>` : ''}
        </div>
        ${ev.description ? `<p class="event-detail-desc">${ev.description}</p>` : ''}
        ${ev.booking_url ? `<a class="event-detail-cta" href="${ev.booking_url}" target="_blank" rel="noopener">Réserver ${iconArrow()}</a>` : ''}
      </div>
    </div>`;
  } catch {
    wrap.innerHTML = '<p class="empty-state">Événement introuvable.</p>';
  }
}

document.getElementById('btn-back').addEventListener('click', () => history.back());

// ── Router ────────────────────────────────────────────────────
let prevPage = null;

async function route() {
  const { page, param } = getRoute();

  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  setActiveNav(page);

  if (page === 'radar') {
    document.getElementById('page-radar').classList.remove('hidden');
    if (prevPage !== 'radar') {
      await loadNewBanner();
      await loadRadar();
      const pillWrap = document.getElementById('category-pills');
      styleActivePill(pillWrap);
    }

  } else if (page === 'calendrier') {
    document.getElementById('page-calendrier').classList.remove('hidden');
    if (prevPage !== 'calendrier') initCalendar();

  } else if (page === 'sorties') {
    document.getElementById('page-sorties').classList.remove('hidden');
    if (prevPage !== 'sorties') loadAllPage();

  } else if (page === 'event') {
    document.getElementById('page-event').classList.remove('hidden');
    loadEventDetail(param);
  }

  prevPage = page;
}

window.addEventListener('hashchange', route);

// ── Bootstrap ─────────────────────────────────────────────────
(async function init() {
  initTheme();
  await Promise.all([loadStats(), loadVenues(), loadCategoryPills()]);
  if (!location.hash || location.hash === '#') location.hash = '#/radar';
  route();
})();
