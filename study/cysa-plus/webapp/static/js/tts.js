/* Read-aloud built on the browser's own speech engine.
 *
 * On Android this is the device's TTS service (usually Google's), which is
 * a far better voice than anything we could ship, needs no audio files, and
 * works with the network off once the voice data is installed.
 *
 * Two engine quirks are handled here:
 *  - getVoices() is empty until the voiceschanged event on most browsers.
 *  - Desktop Chrome stops speaking after ~15s unless nudged; long text is
 *    also unreliable, so everything is queued as short utterances.
 */
var TTS = (function () {
  var synth = window.speechSynthesis;
  var queue = [], at = 0, live = null, keepalive = null;
  var onChunk = null, onDone = null;
  var prefs = { voice: '', rate: 1 };
  var ANDROID = /Android/i.test(navigator.userAgent);

  function supported() { return !!synth && 'SpeechSynthesisUtterance' in window; }

  function voices() {
    if (!supported()) return [];
    return synth.getVoices().filter(function (v) { return /^en/i.test(v.lang); });
  }

  function onVoices(cb) {
    if (!supported()) return;
    if (synth.getVoices().length) { cb(); return; }
    synth.addEventListener('voiceschanged', cb, { once: true });
    // Safari sometimes never fires the event; poll briefly as a fallback.
    var tries = 0;
    var t = setInterval(function () {
      if (synth.getVoices().length || ++tries > 20) { clearInterval(t); cb(); }
    }, 250);
  }

  function pickVoice() {
    var all = voices();
    if (!all.length) return null;
    for (var i = 0; i < all.length; i++) {
      if (all[i].name === prefs.voice) return all[i];
    }
    for (var j = 0; j < all.length; j++) {
      if (all[j].localService) return all[j];   // prefer on-device: works offline
    }
    return all[0];
  }

  function nudge() {
    // The pause/resume workaround fixes desktop Chrome but can glitch audio
    // on Android, where it isn't needed.
    if (ANDROID) return;
    clearInterval(keepalive);
    keepalive = setInterval(function () {
      if (synth.speaking && !synth.paused) { synth.pause(); synth.resume(); }
      else if (!synth.speaking) { clearInterval(keepalive); }
    }, 9000);
  }

  function step() {
    if (at >= queue.length) { finish(); return; }
    var text = queue[at];
    var u = new SpeechSynthesisUtterance(text);
    var v = pickVoice();
    if (v) { u.voice = v; u.lang = v.lang; }
    u.rate = prefs.rate;
    u.onend = function () { at++; step(); };
    u.onerror = function (e) {
      if (e && e.error === 'interrupted') return;   // stop() was called
      at++; step();
    };
    live = u;                    // hold a reference; Chrome GCs otherwise
    if (onChunk) onChunk(text, at, queue.length);
    synth.speak(u);
  }

  function finish() {
    clearInterval(keepalive);
    live = null; queue = []; at = 0;
    if (onDone) onDone();
  }

  return {
    supported: supported,
    voices: voices,
    onVoices: onVoices,
    setVoice: function (name) { prefs.voice = name; },
    setRate: function (r) { prefs.rate = r; },
    rate: function () { return prefs.rate; },

    speak: function (chunks, opts) {
      if (!supported()) return false;
      this.stop();
      opts = opts || {};
      queue = Array.isArray(chunks) ? chunks.slice() : [String(chunks)];
      at = 0; onChunk = opts.onChunk; onDone = opts.onDone;
      nudge();
      step();
      return true;
    },

    /* Speak a question, hold a beat, then the answer. */
    drill: function (q, a, gapSeconds, opts) {
      var chunks = [q];
      var beats = Math.max(0, Math.round(gapSeconds / 2));
      for (var i = 0; i < beats; i++) chunks.push('.');
      chunks.push(a);
      return this.speak(chunks, opts);
    },

    pause: function () { if (synth.speaking && !synth.paused) synth.pause(); },
    resume: function () { if (synth.paused) synth.resume(); },
    paused: function () { return !!synth && synth.paused; },
    speaking: function () { return !!synth && (synth.speaking || synth.pending); },
    stop: function () {
      clearInterval(keepalive);
      onDone = null; queue = []; at = 0; live = null;
      if (supported()) synth.cancel();
    }
  };
})();
