/* Wiring: content loading, navigation, read-aloud, and the card drill. */
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var data = null, current = null, deckCards = [], session = [], card = null;
  var PREFS = 'cysa.prefs.v1';
  var prefs = read(PREFS, { voice: '', rate: 1, gap: 3, section: null, deck: 'All' });

  function read(key, fallback) {
    try { return Object.assign({}, fallback, JSON.parse(localStorage.getItem(key)) || {}); }
    catch (e) { return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private mode */ }
  }

  /* ---------------------------------------------------------------- nav */

  function buildNav() {
    ['study', 'project'].forEach(function (group) {
      var host = $(group === 'study' ? 'navStudy' : 'navProject');
      host.innerHTML = '';
      data.sections.filter(function (s) { return s.group === group; })
        .forEach(function (s) {
          var a = document.createElement('a');
          a.href = '#' + s.id;
          a.dataset.id = s.id;
          a.innerHTML = (s.weight ? '<span class="pct">' + s.weight + '%</span>' : '') +
            s.title + (s.weight ? '<span class="w" style="width:' + (s.weight * 2.4) + '%"></span>' : '');
          host.appendChild(a);
        });
    });
  }

  function show(id) {
    var s = data.sections.filter(function (x) { return x.id === id; })[0];
    if (!s) s = data.sections[0];
    current = s;
    prefs.section = s.id; write(PREFS, prefs);

    var head = '<div class="sec-head"><h2>' + s.title + '</h2>' +
      (TTS.supported()
        ? '<button class="listen" id="listen" type="button">&#9654; Listen</button>'
        : '') +
      '<span class="sec-meta">' +
      (s.weight ? s.weight + '% of the exam &middot; ' : '') +
      '~' + s.minutes + ' min read-aloud</span></div>';
    $('doc').innerHTML = head + s.html;
    $('crumb').textContent = s.title;
    window.scrollTo(0, 0);

    Array.prototype.forEach.call(document.querySelectorAll('.rail a'), function (a) {
      a.classList.toggle('is-on', a.dataset.id === s.id);
    });
    var b = $('listen');
    if (b) b.addEventListener('click', function () { listen(s); });
    TTS.stop(); hidePlayer();
  }

  function drawer(open) {
    $('rail').classList.toggle('open', open);
    $('scrim').classList.toggle('on', open);
    $('menu').setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  /* ------------------------------------------------------------- listen */

  function showPlayer() { $('player').hidden = false; }
  function hidePlayer() { $('player').hidden = true; $('nowTxt').textContent = ''; $('pos').textContent = ''; }

  function listen(section) {
    if (TTS.speaking()) { TTS.stop(); hidePlayer(); return; }
    showPlayer();
    $('pp').innerHTML = '&#10074;&#10074;';
    TTS.speak(section.speech, {
      onChunk: function (text, i, n) {
        $('nowTxt').textContent = text;
        $('pos').textContent = i + 1 + ' / ' + n;
      },
      onDone: hidePlayer
    });
  }

  /* -------------------------------------------------------------- cards */

  function decks() {
    var names = ['All'];
    data.cards.forEach(function (c) {
      if (names.indexOf(c.domain) < 0) names.push(c.domain);
    });
    return names;
  }

  function pickDeck(name) {
    prefs.deck = name; write(PREFS, prefs);
    deckCards = name === 'All' ? data.cards
      : data.cards.filter(function (c) { return c.domain === name; });
    session = Cards.queue(deckCards);
    next();
  }

  function refreshStats() {
    var n = Cards.counts(deckCards);
    $('dueN').textContent = n.due;
    $('newN').textContent = n.fresh;
    $('doneN').textContent = Cards.doneToday();
  }

  function next() {
    refreshStats();
    TTS.stop(); hidePlayer();
    card = session.shift() || null;
    var empty = !card;
    $('cardBox').hidden = empty;
    $('showA').hidden = empty;
    $('gradeRow').hidden = true;
    $('deckDone').hidden = !empty;
    if (empty) return;
    $('cardDomain').textContent = card.domain;
    $('cardQ').innerHTML = card.q;
    $('cardA').innerHTML = card.a;
    $('cardA').hidden = true;
  }

  function reveal() {
    if (!card) return;
    $('cardA').hidden = false;
    $('showA').hidden = true;
    $('gradeRow').hidden = false;
  }

  /* --------------------------------------------------------------- prefs */

  function fillVoices() {
    var list = TTS.voices(), sel = $('voicePick');
    sel.innerHTML = '';
    if (!TTS.supported() || !list.length) {
      sel.innerHTML = '<option>No voices available</option>';
      $('voiceHint').textContent = TTS.supported()
        ? 'No speech voices installed. On Android: Settings → Accessibility → Text-to-speech.'
        : 'This browser has no speech engine.';
      return;
    }
    list.forEach(function (v) {
      var o = document.createElement('option');
      o.value = v.name;
      o.textContent = v.name + (v.localService ? '  (on device)' : '  (network)');
      if (v.name === prefs.voice) o.selected = true;
      sel.appendChild(o);
    });
    $('voiceHint').textContent =
      'Voices marked "on device" keep working with no connection. Android installs '
      + 'more under Settings → Accessibility → Text-to-speech.';
    if (prefs.voice) TTS.setVoice(prefs.voice);
  }

  /* ---------------------------------------------------------------- boot */

  function view(name) {
    $('read').hidden = name !== 'read';
    $('cards').hidden = name !== 'cards';
    Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (t) {
      var on = t.dataset.view === name;
      t.classList.toggle('is-on', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    TTS.stop(); hidePlayer();
    if (name === 'cards') { refreshStats(); if (!card) next(); }
  }

  function wire() {
    $('menu').addEventListener('click', function () {
      drawer(!$('rail').classList.contains('open'));
    });
    $('scrim').addEventListener('click', function () { drawer(false); });
    document.querySelector('.rail').addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (!a) return;
      e.preventDefault();
      show(a.dataset.id);
      if (window.innerWidth <= 880) drawer(false);
    });
    Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (t) {
      t.addEventListener('click', function () { view(t.dataset.view); });
    });

    $('pp').addEventListener('click', function () {
      if (TTS.paused()) { TTS.resume(); $('pp').innerHTML = '&#10074;&#10074;'; }
      else { TTS.pause(); $('pp').innerHTML = '&#9654;'; }
    });
    $('stop').addEventListener('click', function () { TTS.stop(); hidePlayer(); });

    $('showA').addEventListener('click', reveal);
    $('gradeRow').addEventListener('click', function (e) {
      var b = e.target.closest('.g');
      if (!b || !card) return;
      var graded = card;
      Cards.grade(graded.id, +b.dataset.g);
      if (+b.dataset.g < 3) session.push(graded);
      next();
    });
    $('sayCard').addEventListener('click', function () {
      if (!card) return;
      if (TTS.speaking()) { TTS.stop(); hidePlayer(); return; }
      showPlayer();
      $('pp').innerHTML = '&#10074;&#10074;';
      TTS.drill(card.qs, card.as, prefs.gap, {
        onChunk: function (t, i, n) {
          $('nowTxt').textContent = t === '.' ? '…' : t;
          $('pos').textContent = i + 1 + ' / ' + n;
        },
        onDone: function () { hidePlayer(); reveal(); }
      });
    });
    $('deckPick').addEventListener('change', function () { pickDeck(this.value); });
    $('cram').addEventListener('click', function () {
      session = deckCards.slice().sort(function () { return Math.random() - 0.5; });
      next();
    });
    $('resetDeck').addEventListener('click', function () {
      if (!confirm('Reset scheduling for ' + deckCards.length + ' cards in this deck?')) return;
      Cards.reset(deckCards);
      pickDeck(prefs.deck);
    });

    $('prefs').addEventListener('click', function () { fillVoices(); $('prefsBox').showModal(); });
    $('voicePick').addEventListener('change', function () {
      prefs.voice = this.value; TTS.setVoice(this.value); write(PREFS, prefs);
    });
    $('rate').addEventListener('input', function () {
      prefs.rate = +this.value; TTS.setRate(prefs.rate);
      $('rateOut').innerHTML = prefs.rate.toFixed(1) + '&times;'; write(PREFS, prefs);
    });
    $('gap').addEventListener('input', function () {
      prefs.gap = +this.value; $('gapOut').textContent = prefs.gap + 's'; write(PREFS, prefs);
    });

    document.addEventListener('keydown', function (e) {
      if (e.target.matches('input,select,textarea')) return;
      if ($('cards').hidden) return;
      if (e.key === ' ') { e.preventDefault(); $('gradeRow').hidden ? reveal() : null; }
      var map = { '1': 0, '2': 3, '3': 4, '4': 5 };
      if (map[e.key] !== undefined && !$('gradeRow').hidden && card) {
        Cards.grade(card.id, map[e.key]);
        if (map[e.key] < 3) session.push(card);
        next();
      }
    });
    window.addEventListener('beforeunload', function () { TTS.stop(); });
  }

  fetch('content.json').then(function (r) { return r.json(); }).then(function (json) {
    data = json;
    buildNav();
    wire();

    var deckSel = $('deckPick');
    decks().forEach(function (name) {
      var o = document.createElement('option');
      o.value = name; o.textContent = name;
      if (name === prefs.deck) o.selected = true;
      deckSel.appendChild(o);
    });

    TTS.setRate(prefs.rate);
    if (prefs.voice) TTS.setVoice(prefs.voice);
    $('rate').value = prefs.rate;
    $('rateOut').innerHTML = prefs.rate.toFixed(1) + '×';
    $('gap').value = prefs.gap;
    $('gapOut').textContent = prefs.gap + 's';
    TTS.onVoices(fillVoices);

    show(location.hash.slice(1) || prefs.section || data.sections[0].id);
    pickDeck(prefs.deck);
    view('read');
  }).catch(function (err) {
    $('doc').innerHTML = '<p>Could not load the study content. If you opened this '
      + 'file directly from disk, run it through the local server instead '
      + '(<code>python3 app.py</code>) — browsers block fetch on file:// URLs.</p>';
    console.error(err);
  });

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('sw.js').then(function () {
        $('storeInfo').textContent = 'Saved for offline use';
      }).catch(function () {
        $('storeInfo').textContent = 'Offline caching unavailable';
      });
    });
  }
})();
