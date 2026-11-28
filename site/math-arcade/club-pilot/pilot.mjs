const contact = 'info@alberttansinhon.com';
const opens = Date.parse('2026-11-28T00:00:00+08:00');
const closes = Date.parse('2026-12-27T00:00:00+08:00');

function addressedLink(subject, body) {
  return 'mailto:' + contact + '?subject=' + encodeURIComponent(subject) +
    '&body=' + encodeURIComponent(body.trim().replace(/\r?\n/g, '\r\n'));
}

function updateWindow(now = Date.now()) {
  const open = now >= opens && now < closes;
  const closed = now >= closes;
  const notice = document.getElementById('window-notice');
  notice.textContent = closed ? 'The recruitment window closed on 26 December 2026.' :
    open ? 'Organiser enquiries are open for the four-week pilot.' : 'Organiser enquiries open on 28 November 2026.';
  notice.hidden = false;
  document.getElementById('enquiry-actions').hidden = !open;
  document.getElementById('manual-enquiry').hidden = !open;
  document.getElementById('closed-copy').hidden = !closed;
  document.querySelector('.contact-copy h2 + p').hidden = closed;
  document.getElementById('guided-link').hidden = !open;
  const boundary = open ? closes : opens;
  // Re-evaluate a page left open across either Singapore date boundary.
  if (!closed) setTimeout(() => updateWindow(), Math.min(boundary - now + 1, 2147483647));
}
document.getElementById('enquiry-link').href = addressedLink('Atlas club pilot | organiser enquiry', document.getElementById('enquiry-body').textContent);
document.getElementById('report-link').href = addressedLink('Atlas club pilot | session report', document.getElementById('report-body').textContent);
updateWindow();
