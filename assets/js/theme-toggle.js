(function() {
  const storageKey = 'theme';
  const toggle = document.getElementById('theme-toggle');

  function apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (toggle) {
      toggle.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
  }

  let current = localStorage.getItem(storageKey);
  if (!current) {
    current = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  apply(current);

  if (toggle) {
    toggle.addEventListener('click', function() {
      current = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem(storageKey, current);
      apply(current);
    });
  }
})();
