document.addEventListener('DOMContentLoaded', function () {
  const btn = document.getElementById('dark-mode-toggle');
  const body = document.body;
  const html = document.documentElement;
  if (!btn) return;

  // Helper function to set cookie
  const setCookie = (name, value) => {
    document.cookie = `${name}=${value}; path=/; max-age=31536000`; // 1 ano
  };

  // Ensure only an <i> icon is inside the button
  const ensureIcon = (isDark) => {
    // remove any text nodes/non-icon elements without nuking innerHTML repeatedly
    const nodes = Array.from(btn.childNodes);
    for (const n of nodes) {
      if (n.nodeType === Node.TEXT_NODE) n.remove();
      else if (n.nodeType === Node.ELEMENT_NODE && n.tagName.toLowerCase() !== 'i') n.remove();
    }
    let icon = btn.querySelector('i');
    if (!icon) {
      icon = document.createElement('i');
      btn.appendChild(icon);
    }
    icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    btn.setAttribute('aria-label', isDark ? 'Alternar para modo claro' : 'Alternar para modo escuro');
    btn.setAttribute('title', isDark ? 'Alternar tema (claro)' : 'Alternar tema (escuro)');
  };

  // Load initial state and ensure both html and body have the class
  const darkModeEnabled = localStorage.getItem('dark-mode') === 'enabled';
  html.classList.toggle('dark-mode', darkModeEnabled);
  body.classList.toggle('dark-mode', darkModeEnabled);
  ensureIcon(darkModeEnabled);

  // Toggle on click
  btn.addEventListener('click', function () {
    const isDarkMode = body.classList.toggle('dark-mode');
    html.classList.toggle('dark-mode', isDarkMode);
    
    // Sincronizar localStorage e cookie
    const themeValue = isDarkMode ? 'enabled' : 'disabled';
    localStorage.setItem('dark-mode', themeValue);
    setCookie('dark-mode', themeValue);
    
    ensureIcon(isDarkMode);
    
    // Recarregar a página para aplicar o tema no servidor na próxima visita
    // (opcional, mas garante consistência total)
    setTimeout(() => {
      window.location.reload();
    }, 100);
  });
});
