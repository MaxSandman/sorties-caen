/* ============================================================
   Sorties Caen -- Frontend JS
   ============================================================ */

const VENUE_COLOURS = {
  theatre_ouest:    '#f97316',
  zenith:           '#3b82f6',
  cargo:            '#ec4899',
  bbc:              '#f59e0b',
  palais_sports:    '#10b981',
  caen_evenements:  '#8b5cf6',
};

const VENUE_ICONS = {
  theatre_ouest:   '\u2605',  // \u2605
  zenith:          '\u25B6',  // \u25B6
  cargo:           '\u266B',  // \u266B
  bbc:             '\u266A',  // \u266A
  palais_sports:   '\u26BD',  // \u26BD
  caen_evenements: '\u2605',  // \u2605
};

const DAYS_FR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
const MONTHS_FR = [
  'Janvier','F\u00E9vrier','Mars','Avril','Mai','Juin',
  'Juillet','Ao\u00FBt','Septembre','Octobre','Novembre','D\u00E9cembre'
];

// ---- State ----
let state = {
  currentYear:  new Date().getFullYear(),
  currentMonth: new Date().getMonth() + 1,  // 1-based
  selectedDay:  null,
  activeVenue:  '',
  allEvents:    [],
  newEvents:    [],
};

// ---- API helpers ----
async function apiFetch(path, opts) {
  opts = opts || {};
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error('API error ' + res.status);
  if (opts.method === 'POST') return {};
  return res.json();
}

// ---- Colour helpers ----
function venueColour(venueKey) {
  return VENUE_COLOURS[venueKey] || '#6366f1';
}

function venueIcon(venueKey) {
  return VENUE_ICONS[venueKey] || '\u2605';
}

// ---- Date formatting ----
function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
}

// ---- XSS safety ----
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ---- Render "Derni\u00E8res sorties" ----
function renderNewEvents(events) {
  const container = document.getElementById('new-events-list');
  const countEl   = document.getElementById('new-count');

  if (events.length === 0) {
    countEl.style.display = 'none';
    container.innerHTML = '<p class="empty-state">Aucune nouvelle sortie ces 7 derniers jours.</p>';
    return;
  }

  countEl.textContent  = events.length;
  countEl.style.display = '';

  container.innerHTML = events.map(function(ev) {
    const colour = venueColour(ev.venue_key);
    const icon   = venueIcon(ev.venue_key);
    const book   = ev.booking_url
      ? '<a class="card-book" href="' + escHtml(ev.booking_url) + '" target="_blank" rel="noopener" onclick="event.stopPropagation()">R\u00E9server &rarr;</a>'
      : '';
    return (
      '<div class="new-event-card" data-venue="' + ev.venue_key + '" style="--venue-colour:' + colour + '" onclick="openModal(' + ev.id + ')">'
      + '<div style="position:absolute;top:0;left:0;right:0;height:3px;background:' + colour + ';border-radius:10px 10px 0 0"></div>'
      + '<div class="card-venue" style="color:' + colour + '">' + icon + ' ' + escHtml(ev.venue) + '</div>'
      + '<div class="card-title">' + escHtml(ev.title) + '</div>'
      + '<div class="card-date">' + formatDate(ev.date) + '</div>'
      + book
      + '</div>'
    );
  }).join('');
}

// ---- Build calendar grid ----
function buildCalendar(year, month, events) {
  const grid = document.getElementById('calendar');
  document.getElementById('calendar-title').textContent =
    MONTHS_FR[month - 1] + ' ' + year;

  // Group events by day
  const byDay = {};
  events.forEach(function(ev) {
    const d = new Date(ev.date);
    if (d.getFullYear() === year && d.getMonth() + 1 === month) {
      const key = d.getDate();
      if (!byDay[key]) byDay[key] = [];
      byDay[key].push(ev);
    }
  });

  // First weekday of month (Mon=0)
  const firstDay = new Date(year, month - 1, 1);
  let startOffset = firstDay.getDay() - 1;
  if (startOffset < 0) startOffset = 6;

  const daysInMonth = new Date(year, month, 0).getDate();
  const daysInPrev  = new Date(year, month - 1, 0).getDate();
  const today       = new Date();
  const isThisMonth = today.getFullYear() === year && today.getMonth() + 1 === month;

  let html = DAYS_FR.map(function(d) {
    return '<div class="cal-header">' + d + '</div>';
  }).join('');

  // Previous month overflow
  for (let i = startOffset - 1; i >= 0; i--) {
    html += '<div class="cal-day other-month"><div class="day-num">' + (daysInPrev - i) + '</div></div>';
  }

  // Current month
  for (let day = 1; day <= daysInMonth; day++) {
    const dayEvents = byDay[day] || [];
    const isToday   = isThisMonth && today.getDate() === day;
    const isSel     = state.selectedDay === day;
    const hasEv     = dayEvents.length > 0;

    const dots = dayEvents.slice(0, 6).map(function(ev) {
      return '<div class="day-dot" style="background:' + venueColour(ev.venue_key) + '" title="' + escHtml(ev.title) + '"></div>';
    }).join('');

    const countBadge = dayEvents.length > 6
      ? '<span class="day-events-count">+' + dayEvents.length + '</span>'
      : '';

    const classes = 'cal-day'
      + (hasEv ? ' has-events' : '')
      + (isToday ? ' today' : '')
      + (isSel ? ' selected' : '');

    html += '<div class="' + classes + '" data-day="' + day + '"'
      + (hasEv ? ' onclick="selectDay(' + day + ')"' : '')
      + '>'
      + '<div class="day-num">' + day + '</div>'
      + '<div class="day-dots">' + dots + '</div>'
      + countBadge
      + '</div>';
  }

  // Next month overflow
  const totalCells = startOffset + daysInMonth;
  const remaining  = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= remaining; i++) {
    html += '<div class="cal-day other-month"><div class="day-num">' + i + '</div></div>';
  }

  grid.innerHTML = html;
}

// ---- Render events list ----
function renderEventsList(events, title) {
  document.getElementById('events-list-title').textContent = title;
  const container = document.getElementById('events-list');

  if (events.length === 0) {
    container.innerHTML = '<p class="empty-state">Aucun \u00E9v\u00E9nement pour cette p\u00E9riode.</p>';
    return;
  }

  container.innerHTML = events.map(function(ev) {
    const colour = venueColour(ev.venue_key);
    const icon   = venueIcon(ev.venue_key);
    const imgEl  = ev.image_url
      ? '<img class="event-row-img" src="' + escHtml(ev.image_url) + '" alt="" onerror="this.style.display=\'none\'">'
      : '<div class="event-row-img-placeholder">' + icon + '</div>';
    const newBadge = ev.is_new ? '<span class="badge-new">NOUVEAU</span>' : '';
    const timeStr  = ev.time ? ' \u00E0 ' + ev.time : '';

    return (
      '<div class="event-row" data-venue="' + ev.venue_key + '" onclick="openModal(' + ev.id + ')">'
      + '<div class="event-row-color" style="background:' + colour + '"></div>'
      + imgEl
      + '<div class="event-row-info">'
      + '<div class="event-row-title">' + escHtml(ev.title) + '</div>'
      + '<div class="event-row-meta">' + formatDate(ev.date) + timeStr + '</div>'
      + '<div class="event-row-venue" style="color:' + colour + '">' + icon + ' ' + escHtml(ev.venue) + '</div>'
      + '</div>'
      + '<div class="event-row-actions">' + newBadge + '</div>'
      + '</div>'
    );
  }).join('');
}

// ---- Select a day ----
function selectDay(day) {
  state.selectedDay = day;

  const filtered = state.allEvents.filter(function(ev) {
    const d = new Date(ev.date);
    return (
      d.getFullYear() === state.currentYear &&
      d.getMonth() + 1 === state.currentMonth &&
      d.getDate() === day &&
      (!state.activeVenue || ev.venue_key === state.activeVenue)
    );
  });

  const dayLabel = day + ' ' + MONTHS_FR[state.currentMonth - 1] + ' ' + state.currentYear;
  renderEventsList(filtered, '\u00C9v\u00E9nements du ' + dayLabel);
  buildCalendar(state.currentYear, state.currentMonth, getFilteredEvents());
}

// ---- Filter helpers ----
function getFilteredEvents() {
  return state.allEvents.filter(function(ev) {
    return !state.activeVenue || ev.venue_key === state.activeVenue;
  });
}

function getMonthEvents() {
  return getFilteredEvents().filter(function(ev) {
    const d = new Date(ev.date);
    return d.getFullYear() === state.currentYear && d.getMonth() + 1 === state.currentMonth;
  });
}

// ---- Modal ----
function openModal(eventId) {
  const ev = state.allEvents.find(function(e) { return e.id === eventId; });
  if (!ev) return;

  const colour  = venueColour(ev.venue_key);
  const icon    = venueIcon(ev.venue_key);
  const timeStr = ev.time ? ' \u00E0 ' + ev.time : '';
  const imgHtml = ev.image_url
    ? '<img class="modal-img" src="' + escHtml(ev.image_url) + '" alt="">'
    : '';
  const descHtml = ev.description
    ? '<p class="modal-desc">' + escHtml(ev.description) + '</p>'
    : '';
  const bookHtml = ev.booking_url
    ? '<a class="modal-book" href="' + escHtml(ev.booking_url) + '" target="_blank" rel="noopener">&#127903; R\u00E9server des billets</a>'
    : '';

  document.getElementById('modal-body').innerHTML = (
    imgHtml
    + '<div class="modal-venue-tag" style="background:' + colour + '">' + icon + ' ' + escHtml(ev.venue) + '</div>'
    + '<h2 class="modal-title">' + escHtml(ev.title) + '</h2>'
    + '<p class="modal-date">&#128197; ' + formatDate(ev.date) + timeStr + '</p>'
    + (ev.price    ? '<p class="modal-date">Prix&nbsp;: ' + escHtml(ev.price)    + '</p>' : '')
    + (ev.category ? '<p class="modal-date">Cat\u00E9gorie&nbsp;: ' + escHtml(ev.category) + '</p>' : '')
    + descHtml
    + bookHtml
  );
  document.getElementById('modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
}

// ---- Navigate months ----
async function goToMonth(year, month) {
  if (month < 1)  { month = 12; year--; }
  if (month > 12) { month = 1;  year++; }
  state.currentYear  = year;
  state.currentMonth = month;
  state.selectedDay  = null;
  await loadEvents();
}

// ---- Load & refresh ----
async function loadEvents() {
  try {
    const year  = state.currentYear;
    const month = state.currentMonth;
    let url = '/api/events?year=' + year + '&month=' + month;
    if (state.activeVenue) url += '&venue_key=' + encodeURIComponent(state.activeVenue);

    state.allEvents = await apiFetch(url);
    buildCalendar(year, month, getFilteredEvents());
    renderEventsList(getMonthEvents(), MONTHS_FR[month - 1] + ' ' + year);
  } catch (e) {
    console.error(e);
  }
}

async function loadNewEvents() {
  try {
    state.newEvents = await apiFetch('/api/events/new?days=7');
    renderNewEvents(state.newEvents);
  } catch (e) {
    console.error(e);
  }
}

async function loadVenueFilters() {
  try {
    const venues    = await apiFetch('/api/venues');
    const container = document.getElementById('venue-filters');

    venues.forEach(function(v) {
      const btn    = document.createElement('button');
      btn.className      = 'filter-btn';
      btn.dataset.venue  = v.key;
      const colour = venueColour(v.key);
      const icon   = venueIcon(v.key);
      btn.innerHTML = icon + ' ' + escHtml(v.name) + ' <small>(' + v.count + ')</small>';
      btn.onclick   = function() { setVenueFilter(v.key); };
      container.appendChild(btn);
    });
  } catch (e) {
    console.error(e);
  }
}

function setVenueFilter(venueKey) {
  state.activeVenue = venueKey;
  state.selectedDay = null;

  document.querySelectorAll('.filter-btn').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.venue === venueKey);
  });

  buildCalendar(state.currentYear, state.currentMonth, getFilteredEvents());
  renderEventsList(getMonthEvents(), MONTHS_FR[state.currentMonth - 1] + ' ' + state.currentYear);
}

// ---- Manual scrape ----
async function triggerScrape() {
  const btn    = document.getElementById('btn-scrape');
  const status = document.getElementById('scrape-status');
  btn.disabled     = true;
  btn.textContent  = 'En cours\u2026';
  status.textContent = 'R\u00E9cup\u00E9ration des donn\u00E9es\u2026';

  try {
    await apiFetch('/api/scrape', { method: 'POST' });
    status.textContent = 'Mise \u00E0 jour lanc\u00E9e, rechargement dans 20s\u2026';
    setTimeout(async function() {
      await Promise.all([loadEvents(), loadNewEvents(), loadVenueFilters()]);
      status.textContent = 'Mis \u00E0 jour !';
      setTimeout(function() { status.textContent = ''; }, 3000);
    }, 20000);
  } catch (e) {
    status.textContent = 'Erreur lors de la mise \u00E0 jour';
  } finally {
    btn.disabled    = false;
    btn.textContent = '\u8635 Mettre \u00E0 jour';
  }
}

// ---- Init ----
async function init() {
  document.getElementById('btn-prev').onclick = function() {
    goToMonth(state.currentYear, state.currentMonth - 1);
  };
  document.getElementById('btn-next').onclick = function() {
    goToMonth(state.currentYear, state.currentMonth + 1);
  };

  document.getElementById('modal-close').onclick   = closeModal;
  document.getElementById('modal-overlay').onclick = closeModal;
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
  });

  document.getElementById('btn-scrape').onclick = triggerScrape;

  document.querySelector('.filter-btn[data-venue=""]').onclick = function() {
    setVenueFilter('');
  };

  await Promise.all([loadVenueFilters(), loadNewEvents(), loadEvents()]);
}

document.addEventListener('DOMContentLoaded', init);
