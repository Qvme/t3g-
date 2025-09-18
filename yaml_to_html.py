#!/usr/bin/env python3
"""
yaml_to_html.py
Reads sample6.yaml and writes schedule.html (single-page grouped-by-day layout).
Requires: PyYAML
"""

from pathlib import Path
import yaml
import html

IN_FILE = Path("terrible.yaml")
OUT_FILE = Path("index.html")


def load_yaml(path: Path):
    """Load YAML from path using safe_load."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _escape(s):
    return html.escape("" if s is None else str(s))


def render_attendees(attendees):
    """Return HTML for attendees as pill elements. If empty, return an em-dash."""
    if not attendees:
        return "—"
    parts = []
    for a in attendees:
        parts.append(f'<span class="att-pill">{_escape(a)}</span>')
    return " ".join(parts)


def render_lecture(lec):
    """Render a single lecture block."""
    title = _escape(lec.get("lecture", ""))
    attendees_html = render_attendees(lec.get("attendees", []))
    return (
        '<div class="lecture">'
        f'  <div class="title">{title}</div>'
        f'  <div class="attendees">{attendees_html}</div>'
        "</div>"
    )


def render_slot(slot):
    """Render a time slot with one or more lectures."""
    time = slot.get("time", [])
    if not isinstance(time, (list, tuple)) or len(time) < 2:
        start = time[0] if time else ""
        end = ""
    else:
        start, end = time[0], time[1]
    time_str = f"{_escape(start)} — {_escape(end)}" if (start or end) else "—"
    lectures = slot.get("lectures", []) or []
    lectures_html = "\n".join(render_lecture(l) for l in lectures)
    return (
        '<div class="slot">'
        f'  <div class="time">{time_str}</div>'
        f'  <div class="lectures">{lectures_html}</div>'
        "</div>"
    )


def generate_html(doc):
    """Create the full HTML page from the parsed YAML document."""
    name = _escape(doc.get("name", "Schedule"))
    semester = _escape(doc.get("semester", ""))
    week = doc.get("week", {}) or {}

    # Prefer conventional weekday order, but include any extra keys in original order
    day_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    present = []
    seen = set()
    for d in day_order:
        if d in week:
            present.append(d)
            seen.add(d)
    # Append any remaining days in the YAML in their original insertion order
    for d in week.keys():
        if d not in seen:
            present.append(d)
            seen.add(d)

    days_html_parts = []
    for day in present:
        slots = week.get(day, []) or []
        if not slots:
            continue
        slots_html = "\n".join(render_slot(s) for s in slots)
        day_name = _escape(day.capitalize())
        days_html_parts.append(
            '<section class="day-section">'
            f'  <header class="day-header"><div class="day-name">{day_name}</div></header>'
            f'  <div class="day-row">{slots_html}</div>'
            "</section>"
        )

    days_html = "\n".join(days_html_parts)

    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__NAME__ (__SEM__)</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{
  --bg: #0b1220;
  --panel: #0f1724;
  --muted: #d7e0ea;
  --accent: #5fb8ff;
  --gap:12px;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  color-scheme: dark;
}
html,body{height:100%;margin:0}
body{
  margin:28px;
  background-color:var(--bg);
  color:var(--muted);
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}
header{display:flex;align-items:baseline;gap:12px;margin-bottom:14px}
h1{margin:0;font-size:1.25rem}
.meta{color:rgba(215,224,234,0.9);font-size:0.95rem}
main{max-width:1100px;margin:0 auto;display:flex;flex-direction:column;gap:14px}
.day-section{
  background:var(--panel);
  border:1px solid rgba(255,255,255,0.03);
  border-radius:10px;padding:12px;
}
.day-header{display:flex;align-items:center;margin-bottom:10px}
.day-name{font-weight:700;color:var(--accent);font-size:1rem;text-transform:capitalize}
.day-row{display:flex;gap:var(--gap);flex-wrap:wrap}
.slot{min-width:220px;flex:1 1 240px;display:flex;gap:12px;align-items:flex-start;padding:12px;border-radius:10px;
  background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.02)}
.time{width:96px;font-weight:700;color:var(--muted);flex-shrink:0}
.lectures{flex:1;display:flex;flex-direction:column;gap:8px}
.lecture{padding:10px;border-radius:8px;background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.01)}
.title{font-weight:700;color:#fff}
.attendees{font-size:0.85rem;color:rgba(215,224,234,0.9);margin-top:8px;display:flex;gap:8px;flex-wrap:wrap}
.att-pill{padding:6px 10px;border-radius:999px;background:rgba(95,184,255,0.08);border:1px solid rgba(95,184,255,0.12);font-size:0.85rem;color:var(--muted)}
footer{margin-top:16px;color:rgba(215,224,234,0.6);font-size:0.9rem;text-align:center}
/* subtle, low-cost fade-in using opacity only (no transforms) */
.slot, .lecture, .att-pill{opacity:0}
.visible{opacity:1;transition:opacity 260ms linear}
@media (max-width:900px){ .slot{flex-basis:45%} }
@media (max-width:600px){ body{margin:14px} .slot{flex-basis:100%} .time{width:76px} }
</style>
</head>
<body>
<header>
  <h1>__NAME__</h1>
  <div class="meta">Semester: __SEM__</div>
</header>
<main>
__DAYS_HTML__
</main>
<footer>
  ⠑⠝⠙
</footer>
<script>
(function(){
  var rows = document.querySelectorAll('.day-row');
  rows.forEach(function(row){
    var slots = Array.prototype.slice.call(row.querySelectorAll('.slot'));
    slots.forEach(function(slot, i){
      setTimeout(function(){ slot.classList.add('visible'); }, i * 40);
      var lecs = slot.querySelectorAll('.lecture');
      lecs.forEach(function(l, j){
        setTimeout(function(){ l.classList.add('visible'); }, i*40 + 80 + j*30);
      });
      var pills = slot.querySelectorAll('.att-pill');
      pills.forEach(function(p, k){
        setTimeout(function(){ p.classList.add('visible'); }, i*40 + 140 + k*20);
      });
    });
  });
})();
</script>
</body>
</html>
"""

    return template.replace("__NAME__", name).replace("__SEM__", semester).replace("__DAYS_HTML__", days_html)


def main():
    if not IN_FILE.exists():
        raise SystemExit(f"Input file not found: {IN_FILE}")
    doc = load_yaml(IN_FILE)
    OUT_FILE.write_text(generate_html(doc), encoding="utf-8")
    print(f"Wrote {OUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
