"""Build the presenter's guide (docs/Presenter-Guide.pdf) for the people presenting the dashboard.

The text lives in scripts/guide_pages_a.py and scripts/guide_pages_b.py (pages 1 to 8, then 9 to 15) and the design and diagrams in
scripts/guide_parts.py. The site name comes from core/branding.py (set SITE_NAME in the environment to use another name just for
the guide). The PDF is printed with Google Chrome, so Chrome must be installed.

Run:  python scripts/make_presenter_guide.py            (writes docs/Presenter-Guide.html and docs/Presenter-Guide.pdf)
      python scripts/make_presenter_guide.py --check    (also reports any page whose text does not fit)
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
CHECK_SCRIPT = """<script>
window.addEventListener('load', function () {
  var out = [];
  document.querySelectorAll('.page').forEach(function (p) {
    var top = p.getBoundingClientRect().top, foot = p.querySelector('.foot').getBoundingClientRect().top - top, bottom = 0;
    p.querySelectorAll(':scope > *:not(.foot)').forEach(function (c) { bottom = Math.max(bottom, c.getBoundingClientRect().bottom - top); });
    out.push({id: p.id, content: Math.round(bottom), box: Math.round(foot) - 4});
  });
  var d = document.createElement('pre'); d.id = 'overflow-report'; d.textContent = JSON.stringify(out);
  document.body.appendChild(d);
});
</script>"""


def site_name():
    if os.environ.get("SITE_NAME"):
        return os.environ["SITE_NAME"]
    from core import branding
    return branding.DEFAULT_NAME


def build_html(name):
    pages = [a.page1(), a.page2(), a.page3(), a.page4(), a.page5(), a.page6(), a.page7(), a.page8(),
             b.page9(), b.page10(), b.page11(), b.page12(), b.page13(), b.page14(), b.page15()]
    body = "\n".join(pages).replace("{SITE}", name)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{name}: Presenter\'s guide</title>'
            f"<style>{CSS}</style></head><body>{body}{CHECK_SCRIPT}</body></html>")


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", *args], capture_output=True, text=True, timeout=180)


def main():
    out_dir = os.path.join(ROOT, "docs")
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, "Presenter-Guide.html")
    pdf_path = os.path.join(out_dir, "Presenter-Guide.pdf")
    name = site_name()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(name))
    if "--check" in sys.argv:
        run = chrome("--virtual-time-budget=4000", "--dump-dom", "file://" + html_path)
        m = re.search(r'id="overflow-report">(.*?)</pre>', run.stdout, re.S)
        report = json.loads(m.group(1).replace("&quot;", '"')) if m else []
        too_long = [r for r in report if r["content"] > r["box"] + 1]
        print(f"{len(report)} pages checked;", "all fit" if not too_long else "TOO LONG: " + ", ".join(f'{r["id"]} (+{r["content"] - r["box"]}px)' for r in too_long))
    chrome("--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", "file://" + html_path)
    with open(pdf_path, "rb") as f:
        pages = len(re.findall(rb"/Type\s*/Page[^s]", f.read()))
    print(f"wrote {pdf_path} ({pages} pages, {os.path.getsize(pdf_path) // 1024} KB)")


if __name__ == "__main__":
    main()
