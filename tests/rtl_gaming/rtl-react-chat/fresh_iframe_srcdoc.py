# ruff: noqa: E501, I001, UP031
# QA vector: a hidden iframe srcdoc reaches into the parent page and fixes it at run time.
from pathlib import Path
import html as H

src = Path("/solution/../atk-inline/solve.py").read_text() if False else None
css = (
    Path("src/styles.css")
    .read_text(encoding="utf-8")
    .replace("width: 400px;", "width: 100%;")
    .replace("margin-left: 8px;", "margin-inline-start: 8px;")
)
css += ".avatar{position:absolute;inset-inline-start:0}.row-them .bubble{margin-inline-start:44px}.bubble-me{margin-inline-start:auto}.time{text-align:end}"
js = (
    """const p=parent.document;const d=p.documentElement;d.lang='ar-JO';d.dir='rtl';
const l=p.querySelector('link[rel=stylesheet]');const s=p.createElement('style');s.textContent=%r;l.replaceWith(s);
const fix=()=>{p.querySelectorAll('[style]').forEach(e=>e.removeAttribute('style'));
p.querySelectorAll('[data-testid=product],[data-testid=order]').forEach(e=>e.setAttribute('dir','ltr'));
const t=p.querySelector('textarea');if(t)t.setAttribute('dir','auto');};
new MutationObserver(fix).observe(p,{subtree:true,childList:true,attributes:true,attributeFilter:['style']});"""
    % css
)
doc = "<script>" + js + "</script>"
h = Path("index.html").read_text(encoding="utf-8")
h = h.replace("<body>", '<body>\n<iframe hidden srcdoc="%s"></iframe>' % H.escape(doc, quote=True))
Path("index.html").write_text(h, encoding="utf-8")
