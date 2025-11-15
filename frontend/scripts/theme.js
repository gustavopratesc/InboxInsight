export function setupThemeToggle() {
  const btn = document.getElementById("themeToggle");
  const body = document.body;

  btn.addEventListener("click", () => {
    const isDark = body.classList.toggle("dark");

    btn.innerHTML = isDark
      ? '<img src="assets/icons/sun-icon.png" class="icon">'
      : '<img src="assets/icons/moon-icon.png" class="icon">';
  });
}

