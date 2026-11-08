// ~10 s on the TV: 3 s idle, 3.5 s of moves along the picks, 3.5 s along the app shelf (one move every 300 ms).
// Writes window.__bench; read it with JSON.stringify(window.__bench).
(function () {
  var F = window.FreeMyTV, frames = [], last = 0, t0 = Date.now(), phase = 'idle', moves = 0;
  window.__bench = {state: 'running'};
  function goTo(zone) {
    for (var g = 0; g < 4 && F.state.zone !== zone; g++) {
      if (zone === 'cards') F.move(0, F.state.zone === 'top' ? 1 : -1);
      else F.move(0, 1);
    }
  }
  function frame(ts) {
    if (last) frames.push([phase, ts - last]);
    last = ts;
    if (Date.now() - t0 < 10000) window.requestAnimationFrame(frame); else done();
  }
  window.requestAnimationFrame(frame);
  var dir = 1, timer = null, lat = {cards: [], shelf: []};
  function wiggle() {
    var t = performance.now(), ph = phase;
    F.move(dir, 0);
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { lat[ph] && lat[ph].push(Math.round(performance.now() - t)); }); });
    moves++;
    if (moves % 4 === 0) dir = -dir;
  }
  setTimeout(function () { goTo('cards'); phase = 'cards'; moves = 0; dir = 1; timer = setInterval(wiggle, 300); }, 3000);
  setTimeout(function () { clearInterval(timer); goTo('shelf'); phase = 'shelf'; moves = 0; dir = 1; timer = setInterval(wiggle, 300); }, 6500);
  setTimeout(function () { clearInterval(timer); }, 9900);
  function stats(name) {
    var sum = 0, worst = 0, slow = 0, n = 0;
    for (var i = 0; i < frames.length; i++) {
      if (frames[i][0] !== name) continue;
      var d = frames[i][1];
      n++; sum += d; if (d > worst) worst = d; if (d > 25) slow++;
    }
    return n ? {fps: Math.round(1000 * n / sum), worstMs: Math.round(worst), slow: slow} : null;
  }
  function med(a) { a = a.slice().sort(function (x, y) { return x - y; }); return a.length ? a[Math.floor(a.length / 2)] + 'ms' : null; }
  function done() {
    var m = window.performance && window.performance.memory;
    window.__bench = {cls: document.documentElement.className, cards: document.getElementById('cards').children.length,
      idle: stats('idle'), latPicks: med(lat.cards), latApps: med(lat.shelf), picks: stats('cards'), apps: stats('shelf'), jsMB: m ? Math.round(m.usedJSHeapSize / 1048576) : null};
  }
})();
