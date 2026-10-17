"""Build the presenter's guide (docs/Presenter-Guide.pdf) for the people presenting the dashboard.

The text lives in scripts/guide_pages_a.py and scripts/guide_pages_b.py and the design and drawings in scripts/guide_parts.py. Each
"page" function there is really a SECTION: a script in the finished page (see PAGINATE below) pours the sections onto A4 pages, starting
every section on a new page and starting a continuation page whenever the next block does not fit, then numbers the pages and fills in
the page numbers in the contents and in the text. So the text can be made bigger or smaller without fitting pages by hand.

The site name comes from core/branding.py (set SITE_NAME in the environment to use another name just for the guide). The PDF is
printed with Google Chrome, so Chrome must be installed.

Run:  python scripts/make_presenter_guide.py            (writes docs/Presenter-Guide.html and docs/Presenter-Guide.pdf)
      python scripts/make_presenter_guide.py --check    (also reports the page count and any block that does not fit its page)
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import guide_pages_a as a  # noqa: E402
import guide_pages_b as b  # noqa: E402
from guide_parts import CSS  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PAGINATE = """<script>
function paginate() {
  var out = document.getElementById('out'), src = document.getElementById('src'), site = document.body.dataset.site;
  var pages = [], first = {}, last = {}, problems = [], page = null, body = null;
  var FORCE = {p1: 1, p2: 1};              // sections that always start a new page (the rest carry on where the last one ended)
  function newPage(part, cont, cover) {
    var p = document.createElement('div'); p.className = 'page';
    p.innerHTML = (cover ? '' : '<div class="head"><span class="part"></span><span class="site"></span></div>') + '<div class="body"></div>'
      + '<div class="foot"><span class="fl"></span><span class="fc"></span><span class="fr"></span></div>';
    if (!cover) { p.querySelector('.part').textContent = "Presenter's guide"; p.querySelector('.site').textContent = site; }
    out.appendChild(p); pages.push(p); return p;
  }
  var keepNext = function (el) { return el.tagName === 'H1' || el.tagName === 'H2' || el.classList.contains('lead') || (el.classList.contains('kicker') && el.parentNode.className === 'body'); };
  Array.prototype.slice.call(src.querySelectorAll(':scope > section')).forEach(function (sec) {
    var cover = sec.id === 'p1';
    if (FORCE[sec.id] || !page) { page = newPage(sec.dataset.part, false, cover); body = page.querySelector('.body'); }
    else if (sec.children[0]) { sec.children[0].style.marginTop = '14px'; }              // a topic that carries on from the one before
    if (sec.dataset.part && sec.children[0] && sec.children[0].tagName === 'H1') {
      var k = document.createElement('div'); k.className = 'kicker'; k.textContent = sec.dataset.part; sec.insertBefore(k, sec.children[0]);
    }
    var firstEl = sec.children[0];
    function place(child, allowSplit) {
      body.appendChild(child);
      if (body.scrollHeight <= body.clientHeight + 1) { return; }
      var carry = [child], at = body.children.length - 2;
      while (at >= 0 && keepNext(body.children[at])) { carry.unshift(body.children[at]); at--; }
      carry.forEach(function (c) { body.removeChild(c); });
      if (child.tagName === 'TABLE' && carry.length === 1 && child.tBodies[0] && child.tBodies[0].rows.length > 2) {
        // a long table: fit as many rows as the page has room for, then carry on with the rest (its header row repeats)
        var rows = Array.prototype.slice.call(child.tBodies[0].rows), head = child.tHead ? child.tHead.cloneNode(true) : null;
        var current = child.cloneNode(false); if (head) { current.appendChild(head); } var cb = document.createElement('tbody'); current.appendChild(cb);
        body.appendChild(current);
        var done = 0;
        rows.forEach(function (r) {
          cb.appendChild(r);
          if (body.scrollHeight > body.clientHeight + 1 && cb.rows.length > 1) {
            cb.removeChild(r);
            page = newPage(sec.dataset.part, true, false); body = page.querySelector('.body');
            current = child.cloneNode(false); if (head) { current.appendChild(head.cloneNode(true)); } cb = document.createElement('tbody'); current.appendChild(cb);
            body.appendChild(current); cb.appendChild(r);
          }
        });
        return;
      }
      if (allowSplit && child.classList.contains('cols') && carry.length === 1 && body.children.length > 0) {
        // a two-column block that does not fit in what is left of the page: stack its topics so they can use the space
        var pieces = [];
        Array.prototype.slice.call(child.children).forEach(function (col) {
          if (col.classList.contains('topic')) { pieces.push(col); } else { Array.prototype.slice.call(col.children).forEach(function (c) { pieces.push(c); }); }
        });
        pieces.forEach(function (c) { place(c, false); });
        return;
      }
      if (body.children.length === 0) { carry.forEach(function (c) { body.appendChild(c); }); problems.push(sec.id + ': a block is taller than a page'); return; }
      page = newPage(sec.dataset.part, true, false); body = page.querySelector('.body');
      carry.forEach(function (c) { body.appendChild(c); });
      if (body.scrollHeight > body.clientHeight + 1) { problems.push(sec.id + ': a block does not fit even on its own page'); }
    }
    Array.prototype.slice.call(sec.children).forEach(function (child) { place(child, false); });
    first[sec.id] = pages.indexOf(firstEl.closest('.page')) + 1;
    last[sec.id] = pages.length;
  });
  pages.forEach(function (p, i) {
    p.querySelector('.fl').textContent = site + ": Presenter's guide";
    p.querySelector('.fc').textContent = 'Educational project. Not investment advice.';
    p.querySelector('.fr').textContent = (i + 1) + ' of ' + pages.length;
  });
  function range(f, t) { var x = first[f], y = last[t]; return x === y ? String(x) : x + ' to ' + y; }
  document.querySelectorAll('.pgn').forEach(function (s) { s.textContent = String(first[s.dataset.from]); });
  document.querySelectorAll('.pgr').forEach(function (s) {
    var r = range(s.dataset.from, s.dataset.to), word = r.indexOf('to') > -1 ? 'pages ' : 'page ';
    s.textContent = (s.dataset.cap ? word.charAt(0).toUpperCase() + word.slice(1) : word) + r;
  });
  var rep = document.createElement('pre'); rep.id = 'guide-report';
  rep.textContent = JSON.stringify({pages: pages.length, problems: problems, fills: pages.map(function (p) { var b = p.querySelector('.body'), used = 0; Array.prototype.forEach.call(b.children, function (c) { used = Math.max(used, c.getBoundingClientRect().bottom - b.getBoundingClientRect().top); }); return Math.round(100 * used / b.clientHeight); })}); document.body.appendChild(rep);
}
window.addEventListener('load', paginate);
</script>"""


def site_name():
    if os.environ.get("SITE_NAME"):
        return os.environ["SITE_NAME"]
    from core import branding
    return branding.DEFAULT_NAME


def to_section(html):
    """A page function's text turned into a bare section (its header, footer and page box are drawn by the script instead)."""
    m = re.search(r'<div class="page" id="(p\d+)">', html)
    sid = m.group(1)
    part = re.search(r'<div class="head"><span class="part">(.*?)</span>', html)
    html = re.sub(r'<div class="head">.*?</div>', "", html, count=1, flags=re.S)
    html = re.sub(r'<div class="foot">.*?</div>', "", html, count=1, flags=re.S)
    html = html.replace(m.group(0), f'<section id="{sid}" data-part="{part.group(1) if part else ""}">', 1).rstrip()
    assert html.endswith("</div>")
    return html[:-len("</div>")] + "</section>"


def tokens(html):
    """[[pgr:p3:p6]] (lower case) and [[Pgr:p3:p6]] (capitalised) become page-number placeholders the script fills in."""
    return re.sub(r"\[\[(P|p)gr:(p\d+):(p\d+)\]\]",
                  lambda m: f'<span class="pgr" data-from="{m.group(2)}" data-to="{m.group(3)}"{" data-cap=1" if m.group(1) == "P" else ""}></span>', html)


def build_html(name):
    pages = [a.page1(), a.page2(), a.page3(), a.page4(), a.page5(), a.page6(), a.page7(), a.page8(),
             b.page9(), b.page10(), b.page11(), b.page12(), b.page13(), b.page14(), b.page15()]
    body = tokens("\n".join(to_section(p) for p in pages)).replace("{SITE}", name)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{name}: Presenter\'s guide</title>'
            f'<style>{CSS}</style></head><body data-site="{name}"><div id="src">{body}</div><div id="out"></div>{PAGINATE}</body></html>')


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", *args], capture_output=True, text=True, timeout=240)


def main():
    out_dir = os.path.join(ROOT, "docs")
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, "Presenter-Guide.html")
    pdf_path = os.path.join(out_dir, "Presenter-Guide.pdf")
    name = site_name()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(name))
    if "--check" in sys.argv:
        run = chrome("--virtual-time-budget=5000", "--dump-dom", "file://" + html_path)
        m = re.search(r'id="guide-report">(.*?)</pre>', run.stdout, re.S)
        report = json.loads(m.group(1).replace("&quot;", '"')) if m else {"pages": 0, "problems": ["the page script did not run"]}
        print(f"{report['pages']} pages;", "every block fits" if not report["problems"] else "PROBLEMS: " + "; ".join(report["problems"]))
        print("how full each page is (%):", report.get("fills"))
    chrome("--no-pdf-header-footer", "--virtual-time-budget=5000", f"--print-to-pdf={pdf_path}", "file://" + html_path)
    with open(pdf_path, "rb") as f:
        pages = len(re.findall(rb"/Type\s*/Page[^s]", f.read()))
    print(f"wrote {pdf_path} ({pages} pages, {os.path.getsize(pdf_path) // 1024} KB)")


if __name__ == "__main__":
    main()
