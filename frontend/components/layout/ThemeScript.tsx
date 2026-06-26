/** Inline script to apply theme before paint and avoid flash. */
export function ThemeScript() {
  const script = `(function(){try{var k="stock-assistant-theme";var s=localStorage.getItem(k);var t=s==="light"||s==="dark"?s:"dark";document.documentElement.classList.toggle("dark",t==="dark");}catch(e){}})();`;

  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}
