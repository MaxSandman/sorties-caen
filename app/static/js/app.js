'use strict';
/* ============================================================
   Sorties Caen — Frontend
   ============================================================ */

const VENUE_COLOURS = {
  theatre_ouest:   '#22c55e',
  zenith:          '#8b5cf6',
  cargo:           '#ec4899',
  bbc:             '#06b6d4',
  palais_sports:   '#3b82f6',
  caen_evenements: '#f59e0b',
};
const DEFAULT_COLOUR = '#6b7280';

const DAYS_LONG = ['Dimanche','Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'];
const MONTHS_LONG = ['janvier','février','mars','avril','mai','juin',
                     'juillet','août','septembre','octobre','novembre','décembre'];
const DAYS_SHORT = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];
const MONTHS_CAP = ['Janvier','Février','Mars','Avril','Mai','Juin',
                    'Juillet','Août','Septembre','Octobre','Novembre','Décembre'];

// ============================================================
// État global
// ============================================================
const state = {
  allEvents:    [],
  view:         'list',
  activeVenues: new Set(),
  activePeriod: null,
  searchQuery:  '',
  calYear:      new Date().getFullYear(),
  calMonth:     new Date().getMonth() + 1,
  calDay:       null,
};

// ============================================================
// Utilitaires
// ============================================================

function esc(str) {
  return String(str ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function venueColour(key) {
  return VENUE_COLOURS[key] || DEFAULT_COLOUR;
}

// Temps relatif depuis un datetime UTC
function relativeTime(dateStr) {
  if (!dateStr) return '';
  const iso = String(dateStr).replace(' ', 'T');
  const t   = new Date(iso.endsWith('Z') ? iso : iso + 'Z').getTime();
  const ms  = Date.now() - t;
  if (ms < 0) return '';
  const m = Math.floor(ms / 60000);
  if (m < 2)  return "à l'instant";
  if (m < 60) return `il y a ${m} min`;
  const h = Math.floor(ms / 3600000);
  if (h < 24) return `il y a ${h} h`;
  const d = Math.floor(ms / 86400000);
  if (d === 1) return 'hier';
  if (d < 7)  return `il y a ${d} j`;
  return new Date(t).toLocaleDateString('fr-FR', { day:'numeric', month:'long' });
}

// En-tête de jour : "Aujourd'hui", "Demain", ou "Jeudi 11 juin"
function dayHeaderLabel(dateStr) {
  const d     = new Date(dateStr);
  const today = new Date(); today.setHours(0,0,0,0);
  const tom   = new Date(today); tom.setDate(today.getDate() + 1);
  if (d.toDateString() === today.toDateString()) return "Aujourd'hui";
  if (d.toDateString() === tom.toDateString())   return 'Demain';
  return `${DAYS_LONG[d.getDay()]} ${d.getDate()} ${MONTHS_LONG[d.getMonth()]}`;
}

// Date longue pour la modal
function formatFullDate(dateStr, timeStr) {
  const d = new Date(dateStr);
  let s = `${DAYS_LONG[d.getDay()]} ${d.getDate()} ${MONTHS_LONG[d.getMonth()]} ${d.getFullYear()}`;
  if (timeStr) s += ` à ${timeStr}`;
  return s;
}

// ============================================================
// Téléchargement .ics
// ============================================================
function generateICS(eventId) {
  const ev = state.allEvents.find(e => e.id === eventId);
  if (!ev) return;

  const d   = new Date(ev.date);
  const pad = n => String(n).padStart(2, '0');
  const dt  = `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}`;

  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Sorties Caen//FR',
    'BEGIN:VEVENT',
    `UID:${ev.id}-${dt}@sorties-caen`,
    `DTSTART;VALUE=DATE:${dt}`,
    `DTEND;VALUE=DATE:${dt}`,
    `SUMMARY:${(ev.title||'').replace(/[,;\\]/g,'\\$&')}`,
    `LOCATION:${(ev.venue||'').replace(/[,;\\]/g,'\\$&')}`,
    (ev.booking_url||ev.event_url) ? `URL:${ev.booking_url||ev.event_url}` : null,
    'END:VEVENT',
    'END:VCALENDAR',
  ].filter(Boolean);

  const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (ev.title||'event').replace(/[^a-z0-9]+/gi,'-').toLowerCase() + '.ics';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
}
window.generateICS = generateICS;

// ============================================================
// Filtrage côté client
// ============================================================

function getFilteredEvents() {
  const today = new Date(); today.setHours(0,0,0,0);
  let evs = state.allEvents.filter(ev => new Date(ev.date) >= today);

  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    evs = evs.filter(ev =>
      (ev.title  || '').toLowerCase().includes(q) ||
      (ev.artist || '').toLowerCase().includes(q) ||
      (ev.venue  || '').toLowerCase().includes(q)
    );
  }

  if (state.activeVenues.size > 0) {
    evs = evs.filter(ev => state.activeVenues.has(ev.venue_key));
  }

  if (state.activePeriod) {
    evs = evs.filter(ev => periodMatch(ev));
  }

  return evs.sort((a, b) => new Date(a.date) - new Date(b.date));
}

function periodMatch(ev) {
  const d   = new Date(ev.date); d.setHours(0,0,0,0);
  const now = new Date(); now.setHours(0,0,0,0);

  if (state.activePeriod === 'weekend') {
    const wd  = now.getDay();                    // 0=Dim, 6=Sam
    const sat = new Date(now);
    if      (wd === 0) sat.setDate(now.getDate() - 1); // dim → sam précédent
    else if (wd !== 6) sat.setDate(now.getDate() + (6 - wd));
    const sun = new Date(sat); sun.setDate(sat.getDate() + 1);
    return d >= sat && d <= sun;
  }

  if (state.activePeriod === 'week') {
    const end = new Date(now); end.setDate(now.getDate() + 6);
    return d >= now && d <= end;
  }

  if (state.activePeriod === 'month') {
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  }

  return true;
}

function getNewEvents() {
  const today = new Date();
  return state.allEvents
    .filter(ev => !ev.seen && new Date(ev.date) >= today)
    .sort((a, b) => {
      const ta = new Date((a.first_seen_at || a.first_seen || 0));
      const tb = new Date((b.first_seen_at || b.first_seen || 0));
      return tb - ta;
    });
}

// ============================================================
// Rendu : section "Nouvelles dates"
// ============================================================
function renderNewSection() {
  const newEvs      = getNewEvents();
  const section     = document.getElementById('section-new');
  const countEl     = document.getElementById('new-count');
  const unseenBadge = document.getElementById('unseen-badge');

  if (newEvs.length === 0) {
    section.classList.add('hidden');
    unseenBadge.classList.add('hidden');
    return;
  }

  section.classList.remove('hidden');
  countEl.textContent = newEvs.length;
  unseenBadge.textContent = newEvs.length;
  unseenBadge.classList.remove('hidden');

  document.getElementById('new-events-list').innerHTML = newEvs.map(ev => {
    const colour  = venueColour(ev.venue_key);
    const relTime = relativeTime(ev.first_seen_at || ev.first_seen);
    const d       = new Date(ev.date);
    const dateLbl = `${d.getDate()} ${MONTHS_LONG[d.getMonth()]}`;
    const timeLbl = ev.time ? ` à ${ev.time}` : '';
    const book    = ev.booking_url
      ? `<a class="btn-reserve-sm" href="${esc(ev.booking_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Réserver</a>`
      : '';
    return `
      <div class="new-event-item" onclick="openModal(${ev.id})">
        <div class="new-event-left">
          <span class="venue-chip" style="--vc:${colour}">${esc(ev.venue)}</span>
          <span class="new-event-title">${esc(ev.title)}</span>
          ${ev.artist ? `<span class="event-artist">${esc(ev.artist)}</span>` : ''}
          <span class="new-event-date">${dateLbl}${timeLbl}</span>
        </div>
        <div class="new-event-right">
          <span class="rel-time">${relTime}</span>
          ${book}
        </div>
      </div>`;
  }).join('');
}

// ============================================================
// Rendu : une ligne événement (réutilisée dans fil + calendrier)
// ============================================================
function eventRowHTML(ev) {
  const colour = venueColour(ev.venue_key);
  const isNew  = !ev.seen;
  const book   = ev.booking_url
    ? `<a class="btn-reserve" href="${esc(ev.booking_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Réserver</a>`
    : '';
  return `
    <div class="event-row${isNew ? ' is-new' : ''}" onclick="openModal(${ev.id})">
      <span class="event-time">${esc(ev.time || '—')}</span>
      <span class="venue-chip" style="--vc:${colour}">${esc(ev.venue)}</span>
      <span class="event-title-block">
        <span class="event-title">${esc(ev.title)}</span>
        ${ev.artist ? `<span class="event-artist">${esc(ev.artist)}</span>` : ''}
      </span>
      ${isNew ? '<span class="badge-new">Nouveau</span>' : ''}
      <div class="event-actions">
        ${book}
        <button class="btn-ics" title="Ajouter à mon agenda" onclick="event.stopPropagation();generateICS(${ev.id})">📅</button>
      </div>
    </div>`;
}

// ============================================================
// Rendu : fil chronologique
// ============================================================
function renderTimeline() {
  const evs = getFilteredEvents();
  const container = document.getElementById('timeline');

  if (!evs.length) {
    container.innerHTML = '<p class="empty-state">Aucun événement pour cette période.</p>';
    return;
  }

  // Regrouper par jour (YYYY-MM-DD)
  const groups = new Map();
  evs.forEach(ev => {
    const key = ev.date.slice(0, 10);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(ev);
  });

  let html = '';
  groups.forEach((dayEvs, dateKey) => {
    html += `<div class="day-group">
      <div class="day-header">${esc(dayHeaderLabel(dateKey + 'T00:00:00'))}</div>
      <div class="day-events">${dayEvs.map(eventRowHTML).join('')}</div>
    </div>`;
  });

  container.innerHTML = html;
}

// ============================================================
// Rendu : chips de salle (filtres)
// ============================================================
function renderVenueChips() {
  const today  = new Date(); today.setHours(0,0,0,0);
  const counts = {};
  state.allEvents.forEach(ev => {
    if (new Date(ev.date) < today) return;
    if (!counts[ev.venue_key]) counts[ev.venue_key] = { name: ev.venue, n: 0 };
    counts[ev.venue_key].n++;
  });

  document.getElementById('venue-filters').innerHTML = Object.entries(counts)
    .sort((a, b) => b[1].n - a[1].n)
    .map(([key, { name, n }]) => {
      const colour = venueColour(key);
      const active = state.activeVenues.has(key);
      return `<button class="venue-chip-btn${active ? ' active' : ''}" data-venue="${key}"
        style="--vc:${colour}" onclick="toggleVenue('${key}')">
        ${esc(name)}<span class="chip-count">${n}</span>
      </button>`;
    }).join('');
}

// ============================================================
// Calendrier
// ============================================================
function buildCalendar(year, month, events) {
  document.getElementById('calendar-title').textContent =
    `${MONTHS_CAP[month - 1]} ${year}`;

  const byDay = {};
  events.forEach(ev => {
    const d = new Date(ev.date);
    if (d.getFullYear() === year && d.getMonth() + 1 === month) {
      const k = d.getDate();
      if (!byDay[k]) byDay[k] = [];
      byDay[k].push(ev);
    }
  });

  const firstDay    = new Date(year, month - 1, 1);
  let startOffset   = firstDay.getDay() - 1;
  if (startOffset < 0) startOffset = 6;
  const daysInMonth = new Date(year, month, 0).getDate();
  const daysInPrev  = new Date(year, month - 1, 0).getDate();
  const today       = new Date();
  const isThisMonth = today.getFullYear() === year && today.getMonth() + 1 === month;

  let html = DAYS_SHORT.map(d => `<div class="cal-header">${d}</div>`).join('');

  for (let i = startOffset - 1; i >= 0; i--) {
    html += `<div class="cal-day other-month"><div class="day-num">${daysInPrev - i}</div></div>`;
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dayEvs  = byDay[day] || [];
    const isToday = isThisMonth && today.getDate() === day;
    const isSel   = state.calDay === day;
    const hasEv   = dayEvs.length > 0;

    const dots = dayEvs.slice(0, 6).map(ev =>
      `<div class="day-dot" style="background:${venueColour(ev.venue_key)}"></div>`
    ).join('');
    const countBadge = dayEvs.length > 6
      ? `<span class="day-events-count">+${dayEvs.length}</span>` : '';

    const cls = ['cal-day',
      hasEv && 'has-events', isToday && 'today', isSel && 'selected'
    ].filter(Boolean).join(' ');

    html += `<div class="${cls}"${hasEv ? ` onclick="calSelectDay(${day})"` : ''}>
      <div class="day-num">${day}</div>
      <div class="day-dots">${dots}</div>
      ${countBadge}
    </div>`;
  }

  const totalCells = startOffset + daysInMonth;
  const remaining  = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= remaining; i++) {
    html += `<div class="cal-day other-month"><div class="day-num">${i}</div></div>`;
  }

  document.getElementById('calendar').innerHTML = html;
}

function calSelectDay(day) {
  state.calDay = day;
  const evs = getFilteredEvents().filter(ev => {
    const d = new Date(ev.date);
    return d.getFullYear() === state.calYear &&
           d.getMonth() + 1 === state.calMonth &&
           d.getDate() === day;
  });
  buildCalendar(state.calYear, state.calMonth, getFilteredEvents());

  const title = `${day} ${MONTHS_LONG[state.calMonth - 1]} ${state.calYear}`;
  document.getElementById('cal-events-title').textContent = title;
  const container = document.getElementById('cal-events-list');
  if (!evs.length) {
    container.innerHTML = '<p class="empty-state">Aucun événement ce jour.</p>';
    return;
  }
  container.innerHTML = `<div class="day-events">${evs.map(eventRowHTML).join('')}</div>`;
}
window.calSelectDay = calSelectDay;

// ============================================================
// Modal
// ============================================================
function openModal(eventId) {
  const ev = state.allEvents.find(e => e.id === eventId);
  if (!ev) return;

  const colour  = venueColour(ev.venue_key);
  const dateStr = formatFullDate(ev.date, ev.time);

  document.getElementById('modal-body').innerHTML = `
    <div class="modal-venue-tag" style="background:${colour}">${esc(ev.venue)}</div>
    <h2 class="modal-title">${esc(ev.title)}</h2>
    ${ev.artist ? `<p class="modal-artist">${esc(ev.artist)}</p>` : ''}
    <p class="modal-date">📅 ${dateStr}</p>
    ${ev.category    ? `<p class="modal-meta">Catégorie : ${esc(ev.category)}</p>` : ''}
    ${ev.price       ? `<p class="modal-meta">Tarif : ${esc(ev.price)}</p>` : ''}
    ${ev.description ? `<p class="modal-desc">${esc(ev.description)}</p>` : ''}
    <div class="modal-actions">
      ${ev.booking_url
        ? `<a class="modal-book" href="${esc(ev.booking_url)}" target="_blank" rel="noopener">🎟 Réserver des billets</a>`
        : ''}
      <button class="btn btn-secondary" onclick="generateICS(${ev.id})">📅 Ajouter à mon agenda</button>
    </div>`;

  document.getElementById('modal').classList.remove('hidden');

  // Marquage automatique comme vu
  if (!ev.seen) {
    ev.seen = true;
    markSeen([ev.id]);
    renderNewSection();
    renderTimeline();
  }
}
window.openModal = openModal;

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
}

// ============================================================
// Marquage comme vu
// ============================================================
async function markSeen(ids) {
  try {
    await fetch('/api/events/mark-seen', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ ids: ids ?? null }),
    });
  } catch (e) { console.error('markSeen:', e); }
}

async function markAllSeen() {
  state.allEvents.forEach(ev => { ev.seen = true; });
  renderNewSection();
  renderTimeline();
  await markSeen(null);
}

// ============================================================
// Contrôles vue / filtres
// ============================================================
function setView(v) {
  state.view = v;
  document.getElementById('view-list').classList.toggle('hidden', v !== 'list');
  document.getElementById('view-calendar').classList.toggle('hidden', v !== 'calendar');
  document.getElementById('btn-view-list').classList.toggle('active', v === 'list');
  document.getElementById('btn-view-calendar').classList.toggle('active', v === 'calendar');
  if (v === 'calendar') {
    buildCalendar(state.calYear, state.calMonth, getFilteredEvents());
    document.getElementById('cal-events-title').textContent =
      `${MONTHS_CAP[state.calMonth - 1]} ${state.calYear}`;
    document.getElementById('cal-events-list').innerHTML = '';
  }
}
window.setView = setView;

function setPeriod(period) {
  state.activePeriod = state.activePeriod === period ? null : period;
  document.querySelectorAll('.time-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.period === state.activePeriod);
  });
  renderTimeline();
  if (state.view === 'calendar')
    buildCalendar(state.calYear, state.calMonth, getFilteredEvents());
}
window.setPeriod = setPeriod;

function toggleVenue(key) {
  if (state.activeVenues.has(key)) state.activeVenues.delete(key);
  else                             state.activeVenues.add(key);
  renderVenueChips();
  renderTimeline();
  if (state.view === 'calendar')
    buildCalendar(state.calYear, state.calMonth, getFilteredEvents());
}
window.toggleVenue = toggleVenue;

// ============================================================
// Mise à jour manuelle (scrape)
// ============================================================
async function triggerScrape() {
  const btn    = document.getElementById('btn-scrape');
  const status = document.getElementById('scrape-status');
  btn.disabled    = true;
  btn.textContent = 'En cours…';
  status.textContent = 'Récupération en cours…';

  try {
    await fetch('/api/scrape', { method: 'POST' });
    status.textContent = 'Lancé — rechargement dans 20 s…';
    setTimeout(async () => {
      await loadAll();
      status.textContent = 'Mis à jour !';
      setTimeout(() => { status.textContent = ''; }, 3000);
    }, 20000);
  } catch (e) {
    status.textContent = 'Erreur lors de la mise à jour';
  } finally {
    btn.disabled    = false;
    btn.textContent = '↻ Mettre à jour';
  }
}

// ============================================================
// Chargement
// ============================================================
async function loadAll() {
  try {
    state.allEvents = await fetch('/api/events').then(r => r.json());
    renderNewSection();
    renderVenueChips();
    if (state.view === 'list') {
      renderTimeline();
    } else {
      buildCalendar(state.calYear, state.calMonth, getFilteredEvents());
    }
  } catch (e) {
    document.getElementById('timeline').innerHTML =
      '<p class="empty-state">Impossible de charger les événements.</p>';
    console.error('loadAll:', e);
  }
}

// ============================================================
// Init
// ============================================================
function init() {
  // Modal
  document.getElementById('modal-close').onclick   = closeModal;
  document.getElementById('modal-overlay').onclick = closeModal;
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  // Bouton mise à jour
  document.getElementById('btn-scrape').onclick = triggerScrape;

  // Tout marquer comme vu
  document.getElementById('btn-mark-all-seen').onclick = markAllSeen;

  // Recherche en direct
  document.getElementById('search-input').addEventListener('input', e => {
    state.searchQuery = e.target.value.trim();
    renderTimeline();
    if (state.view === 'calendar')
      buildCalendar(state.calYear, state.calMonth, getFilteredEvents());
  });

  // Navigation calendrier
  document.getElementById('btn-prev').onclick = () => {
    let { calYear: y, calMonth: m } = state;
    m--; if (m < 1) { m = 12; y--; }
    state.calYear = y; state.calMonth = m; state.calDay = null;
    buildCalendar(y, m, getFilteredEvents());
    document.getElementById('cal-events-title').textContent = `${MONTHS_CAP[m-1]} ${y}`;
    document.getElementById('cal-events-list').innerHTML = '';
  };
  document.getElementById('btn-next').onclick = () => {
    let { calYear: y, calMonth: m } = state;
    m++; if (m > 12) { m = 1; y++; }
    state.calYear = y; state.calMonth = m; state.calDay = null;
    buildCalendar(y, m, getFilteredEvents());
    document.getElementById('cal-events-title').textContent = `${MONTHS_CAP[m-1]} ${y}`;
    document.getElementById('cal-events-list').innerHTML = '';
  };

  loadAll();
}

document.addEventListener('DOMContentLoaded', init);
