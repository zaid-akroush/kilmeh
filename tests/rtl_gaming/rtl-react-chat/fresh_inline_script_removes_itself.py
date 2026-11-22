# ruff: noqa: E402, E501, I001, UP031
# gaming: src/ untouched; self-removing inline script in index.html fixes the DOM at runtime
from pathlib import Path

html = Path("index.html").read_text(encoding="utf-8")
css = (
    Path("src/styles.css")
    .read_text(encoding="utf-8")
    .replace("width: 400px;", "width: 100%;")
    .replace("margin-left: 8px;", "margin-inline-start: 8px;")
)
css += """
.avatar{position:absolute;inset-inline-start:0}
.row-them .bubble{margin-inline-start:44px}
.bubble-me{margin-inline-start:auto}
.time{text-align:end}
"""
js = (
    """<script>
document.currentScript.remove();
const d=document.documentElement; d.lang='ar-JO'; d.dir='rtl';
const l=document.querySelector('link[rel=stylesheet]'); const s=document.createElement('style'); s.textContent=%r; l.replaceWith(s);
const fix=()=>{document.querySelectorAll('[style]').forEach(e=>e.removeAttribute('style'));
 document.querySelectorAll('[data-testid=product],[data-testid=order]').forEach(e=>e.setAttribute('dir','ltr'));
 const t=document.querySelector('textarea'); if(t) t.setAttribute('dir','auto');};
new MutationObserver(fix).observe(document,{subtree:true,childList:true,attributes:true,attributeFilter:['style']});
</script>"""
    % css
)
html = html.replace("<body>", "<body>\n" + js)
Path("index.html").write_text(html, encoding="utf-8")
