// This loads only the icons that the tool is using, increases load times
window.FontAwesomeKitConfig = {
  asyncLoading: { enabled: true },
  autoA11y: { enabled: true },
  baseUrl: "https://ka-f.fontawesome.com",
  license: "free",
  method: "css",
  minify: { enabled: true },
  v4FontFaceShim: { enabled: false },
  v4shim: { enabled: false },
  version: "latest",
  icons: {
    "solid": [
      "clipboard",
      "file-alt",
      "chart-bar",
      "tasks",
      "cog",
      "sign-out-alt",
      "user-cog",
      "sign-in-alt", 
      "user-plus",
      "check-circle",
      "exclamation-circle",
      "bullhorn",
      "chart-line",
      "angle-right",
      "angle-double-right",
      "angle-left",
      "angle-double-left"
    ]
  }
};

// Load the Font Awesome script
(function() {
  const script = document.createElement('script');
  script.src = 'https://ka-f.fontawesome.com/releases/v5.15.4/js/free.js';
  script.crossOrigin = 'anonymous';
  document.head.appendChild(script);
})();