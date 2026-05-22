// ─── Theme Toggle ────────────────────────────────────────────

function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

// Load saved theme
(function () {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
})();


// ─── Mobile Menu ─────────────────────────────────────────────

function toggleMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.classList.toggle('mobile-open');
  }
}

// Close sidebar on outside click
document.addEventListener('click', function (e) {
  const sidebar = document.getElementById('sidebar');
  const btn = document.querySelector('.mobile-menu-btn');
  if (sidebar && btn && !sidebar.contains(e.target) && !btn.contains(e.target)) {
    sidebar.classList.remove('mobile-open');
  }
});


// ─── Alert Auto-dismiss ──────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s, transform 0.5s';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});


// ─── Stat Counter Animation ──────────────────────────────────

function animateCount(el, target, duration = 800) {
  const start = 0;
  const step = target / (duration / 16);
  let current = start;
  const update = () => {
    current = Math.min(current + step, target);
    el.textContent = Math.round(current);
    if (current < target) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.stat-number').forEach(el => {
    const raw = el.textContent.trim();
    if (raw.endsWith('%')) {
      const num = parseInt(raw);
      let c = 0;
      const step = num / 50;
      const iv = setInterval(() => {
        c = Math.min(c + step, num);
        el.textContent = Math.round(c) + '%';
        if (c >= num) clearInterval(iv);
      }, 16);
    } else if (!isNaN(parseInt(raw))) {
      animateCount(el, parseInt(raw));
    }
  });
});


// ─── Table Live Search (report page) ─────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  const searchEl = document.querySelector('.filter-form input[name="search"]');
  const table = document.getElementById('attendance-table');
  if (!searchEl || !table) return;

  searchEl.addEventListener('input', function () {
    const val = this.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(val) ? '' : 'none';
    });
  });
});


// ─── Form Validation ─────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function (e) {
      const inputs = form.querySelectorAll('input[required]');
      let valid = true;
      inputs.forEach(input => {
        if (!input.value.trim()) {
          input.style.borderColor = '#dc3545';
          valid = false;
        } else {
          input.style.borderColor = '';
        }
      });
      if (!valid) {
        e.preventDefault();
      }
    });
  });
});


// ─── Bar Chart Height Fix ─────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  const bars = document.querySelectorAll('.bar-fill');
  if (bars.length === 0) return;
  
  // Find max value
  let maxVal = 0;
  bars.forEach(bar => {
    const val = parseInt(bar.querySelector('.bar-val')?.textContent || '0');
    if (val > maxVal) maxVal = val;
  });
  
  if (maxVal === 0) return;
  
  bars.forEach(bar => {
    const val = parseInt(bar.querySelector('.bar-val')?.textContent || '0');
    const pct = (val / maxVal) * 100;
    bar.style.height = Math.max(pct, 5) + '%';
  });
});
