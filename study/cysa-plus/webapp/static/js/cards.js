/* Spaced repetition (SM-2) with progress kept on the device.
 *
 * Grades follow the usual four buttons: 0 Again, 3 Hard, 4 Good, 5 Easy.
 * A card graded Again returns later in the same session rather than being
 * scheduled out to tomorrow.
 */
var Cards = (function () {
  var KEY = 'cysa.srs.v1';
  var DAY = 86400000;
  var state = load();

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || { cards: {}, log: {} }; }
    catch (e) { return { cards: {}, log: {} }; }
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode */ }
  }

  function today() { return new Date().toISOString().slice(0, 10); }

  function of(id) {
    return state.cards[id] || { ef: 2.5, reps: 0, interval: 0, due: 0 };
  }

  function grade(id, g) {
    var c = of(id);
    if (g < 3) {
      c.reps = 0;
      c.interval = 0;
      c.due = Date.now();              // comes back this session
    } else {
      c.reps += 1;
      if (c.reps === 1) c.interval = 1;
      else if (c.reps === 2) c.interval = 6;
      else c.interval = Math.round(c.interval * c.ef);
      c.ef = Math.max(1.3, c.ef + (0.1 - (5 - g) * (0.08 + (5 - g) * 0.02)));
      c.due = Date.now() + c.interval * DAY;
    }
    state.cards[id] = c;
    var d = today();
    state.log[d] = (state.log[d] || 0) + 1;
    save();
    return c;
  }

  return {
    grade: grade,
    of: of,
    doneToday: function () { return state.log[today()] || 0; },

    /* Cards ready to study: never-seen first, then overdue. */
    queue: function (all) {
      var now = Date.now(), fresh = [], due = [];
      all.forEach(function (card) {
        var c = state.cards[card.id];
        if (!c) fresh.push(card);
        else if (c.due <= now) due.push(card);
      });
      due.sort(function (a, b) { return of(a.id).due - of(b.id).due; });
      return fresh.concat(due);
    },

    counts: function (all) {
      var now = Date.now(), fresh = 0, due = 0;
      all.forEach(function (card) {
        var c = state.cards[card.id];
        if (!c) fresh++;
        else if (c.due <= now) due++;
      });
      return { fresh: fresh, due: due };
    },

    reset: function (all) {
      all.forEach(function (card) { delete state.cards[card.id]; });
      save();
    }
  };
})();
