// ---------- Mobile nav toggle ----------
const navToggle = document.getElementById('navToggle');
const sidebar = document.getElementById('sidebar');
navToggle.addEventListener('click', function () {
  sidebar.classList.toggle('open');
});

// Close mobile nav after clicking a link
document.querySelectorAll('.sidebar-nav a').forEach(function (link) {
  link.addEventListener('click', function () {
    sidebar.classList.remove('open');
  });
});

// ---------- Scroll-spy active link ----------
const sections = document.querySelectorAll('.section, .cover');
const navLinks = document.querySelectorAll('.sidebar-nav a');

function updateActiveLink() {
  let currentId = '';
  sections.forEach(function (section) {
    const rect = section.getBoundingClientRect();
    if (rect.top <= 120 && rect.bottom >= 120) {
      currentId = section.id;
    }
  });
  navLinks.forEach(function (link) {
    link.classList.remove('active');
    if (link.getAttribute('href') === '#' + currentId) {
      link.classList.add('active');
    }
  });
}
window.addEventListener('scroll', updateActiveLink);
window.addEventListener('load', updateActiveLink);

// ---------- Print ----------
document.getElementById('printBtn').addEventListener('click', function () {
  window.print();
});

// ---------- Download as Word (.doc) ----------
document.getElementById('downloadWordBtn').addEventListener('click', function () {
  const printable = document.getElementById('printable');
  const contentClone = printable.cloneNode(true);

  const exportStyles = [
    'body{font-family:Calibri,Arial,sans-serif;color:#1D1D1B;font-size:12pt;}',
    'h1{color:#1B3B2F;font-size:22pt;margin-bottom:4pt;}',
    'h2{color:#1B3B2F;font-size:16pt;border-bottom:2pt solid #86BC25;padding-bottom:4pt;margin-top:22pt;}',
    'h3{color:#1B3B2F;font-size:13pt;}',
    'h4{color:#1B3B2F;font-size:11pt;text-transform:uppercase;}',
    'p{font-size:11pt;line-height:1.4;}',
    'table{border-collapse:collapse;width:100%;margin:10pt 0;}',
    'td,th{border:1pt solid #C7D1C9;padding:6pt 8pt;font-size:10pt;text-align:left;}',
    'th{background:#1B3B2F;color:#FFFFFF;}',
    '.chip,.chip-grid span,.sp-chip-row span{border:1pt solid #C7D1C9;padding:3pt 6pt;margin:2pt;display:inline-block;font-size:9pt;}',
    '.module-card,.feature-card,.arch-box,.sp-block{border:1pt solid #C7D1C9;padding:8pt;margin-bottom:8pt;}',
    '.cover{border-bottom:3pt solid #86BC25;padding-bottom:16pt;margin-bottom:16pt;}',
    '.cover-tag{background:#1B3B2F;color:#FFFFFF;padding:6pt 10pt;display:inline-block;}',
    '.num{background:#1B3B2F;color:#FFFFFF;padding:2pt 6pt;margin-right:6pt;}',
    '.arch-diagram{margin-top:10pt;}',
    '.arch-layer{border:1pt solid #C7D1C9;padding:8pt;margin-bottom:8pt;background:#F1F5EF;}',
    '.doc-footer{font-size:9pt;color:#53565A;text-align:center;margin-top:20pt;}'
  ].join(' ');

  const htmlDoc =
    '<html xmlns:o="urn:schemas-microsoft-com:office:office" ' +
    'xmlns:w="urn:schemas-microsoft-com:office:word" ' +
    'xmlns="http://www.w3.org/TR/REC-html40">' +
    '<head><meta charset="utf-8">' +
    '<title>IMO Strategic Engagement Platform - HLD</title>' +
    '<style>' + exportStyles + '</style>' +
    '</head><body>' + contentClone.innerHTML + '</body></html>';

  const blob = new Blob(['\ufeff', htmlDoc], { type: 'application/msword' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'IMO_Shadow_Portal_HLD.doc';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
});