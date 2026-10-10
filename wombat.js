(function () {
  var card = document.getElementById('wombat-card');
  var roam = document.getElementById('wombat-roam');
  if (!card || !roam) return;
  fetch('https://en.wikipedia.org/api/rest_v1/page/summary/Wombat')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.extract) document.getElementById('wombat-card-text').textContent = d.extract;
      if (d.thumbnail && d.thumbnail.source) {
        var img = document.getElementById('wombat-card-img');
        img.src = d.thumbnail.source;
        img.hidden = false;
      }
    })
    .catch(function () {
      document.getElementById('wombat-card-text').textContent =
        'Wombats are short-legged, muscular marsupials native to Australia.';
    });
  roam.addEventListener('mouseenter', function () {
    card.style.transform = 'translateX(-50%)';
    var rect = card.getBoundingClientRect();
    var shift = 0;
    if (rect.left < 8) shift = 8 - rect.left;
    else if (rect.right > window.innerWidth - 8) shift = window.innerWidth - 8 - rect.right;
    if (shift) card.style.transform = 'translateX(calc(-50% + ' + shift + 'px))';
  });
})();
