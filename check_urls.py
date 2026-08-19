import cloudscraper
import html
import re
import sys
import time
import glob
import os
import math
from datetime import datetime
from zoneinfo import ZoneInfo

ITEMS_PER_PAGE = 20  # ganti angka ini kalau mau lebih banyak/sedikit item per halaman
DATA_FILE = "videos.txt"


def load_videos(path=DATA_FILE):
    """Baca url|judul|cover dari file txt. Baris kosong / diawali # diabaikan."""
    videos = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("|")
            if len(parts) < 2:
                print(f"  -> Baris {line_num} diabaikan (format salah, butuh minimal 'URL | Judul'): {line}", file=sys.stderr)
                continue

            url = parts[0].strip()
            judul = parts[1].strip() if len(parts) > 1 else ""
            cover = parts[2].strip() if len(parts) > 2 else ""

            if not url:
                continue
            if not judul:
                judul = "(Tanpa Judul)"

            videos.append({"url": url, "judul": judul, "cover": cover})
    return videos


def check_status(scraper, url):
    """Cek status HTTP. Kalau request gagal total, pakai nama exception sbg status."""
    try:
        response = scraper.get(url, timeout=20)
        return response.status_code
    except Exception as e:
        print(f"  -> Gagal cek {url}: {e}", file=sys.stderr)
        return type(e).__name__


def main():
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    scraper.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    })

    videos = load_videos()
    results = []

    for v in videos:
        status = check_status(scraper, v["url"])
        print(f"Cek: {v['url']} -> [{v['judul']}] -> {status}")
        results.append({**v, "status": status})
        time.sleep(1)  # jeda kecil antar-request biar nggak keliatan kayak burst bot

    return results


def status_css_class(status):
    status_str = str(status)
    if status_str.isdigit() and 200 <= int(status_str) < 300:
        return "ok"
    if status_str.isdigit() and 300 <= int(status_str) < 400:
        return "redirect"
    return "fail"


def render_row(item):
    safe_title = html.escape(item["judul"])
    safe_url = html.escape(item["url"])
    safe_status = html.escape(str(item["status"]))
    css = status_css_class(item["status"])

    if item["cover"]:
        safe_cover = html.escape(item["cover"])
        cover_html = (
            f'<img src="{safe_cover}" alt="cover" loading="lazy" '
            f'onerror="this.onerror=null;this.src=\'\';this.alt=\'(gagal load)\';this.classList.add(\'no-cover\')">'
        )
    else:
        cover_html = '<div class="no-cover-placeholder">Tidak ada cover</div>'

    return (
        f'<tr>'
        f'<td class="cover-cell">{cover_html}</td>'
        f'<td>{safe_title}</td>'
        f'<td><a href="{safe_url}" target="_blank" rel="noopener">{safe_url}</a></td>'
        f'<td><span class="status {css}">{safe_status}</span></td>'
        f'</tr>'
    )


def render_pagination(current_page, total_pages):
    if total_pages <= 1:
        return ""

    def page_filename(p):
        return "index.html" if p == 1 else f"page{p}.html"

    links = []

    if current_page > 1:
        links.append(f'<a href="{page_filename(current_page - 1)}" class="page-link">&laquo; Sebelumnya</a>')

    for p in range(1, total_pages + 1):
        if p == current_page:
            links.append(f'<span class="page-link active">{p}</span>')
        else:
            links.append(f'<a href="{page_filename(p)}" class="page-link">{p}</a>')

    if current_page < total_pages:
        links.append(f'<a href="{page_filename(current_page + 1)}" class="page-link">Selanjutnya &raquo;</a>')

    return '<div class="pagination">' + "\n".join(links) + '</div>'


def render_page(items, current_page, total_pages, now_str, total_items):
    rows_html = "\n".join(render_row(item) for item in items) if items else ""
    pagination_html = render_pagination(current_page, total_pages)

    page = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>URL Status Checker</title>
<style>
  body {{
    font-family: -apple-system, Arial, sans-serif;
    max-width: 1000px;
    margin: 40px auto;
    padding: 0 20px;
    background: #f5f5f5;
    color: #222;
  }}
  h1 {{ font-size: 22px; }}
  .updated {{ color: #666; font-size: 13px; margin-bottom: 16px; }}
  #searchBox {{
    width: 100%;
    box-sizing: border-box;
    padding: 10px 14px;
    margin-bottom: 16px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
  }}
  .search-note {{ color: #888; font-size: 12px; margin: -10px 0 16px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }}
  th, td {{
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid #eee;
    font-size: 14px;
    vertical-align: middle;
  }}
  th {{ background: #fafafa; }}
  td a {{ color: #1565c0; text-decoration: none; word-break: break-all; }}
  td a:hover {{ text-decoration: underline; }}
  .cover-cell {{ width: 130px; }}
  .cover-cell img {{
    width: 120px;
    height: 68px;
    object-fit: cover;
    border-radius: 4px;
    display: block;
    background: #eee;
  }}
  .no-cover-placeholder, .no-cover {{
    width: 120px;
    height: 68px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #eee;
    color: #999;
    font-size: 11px;
    border-radius: 4px;
    text-align: center;
  }}
  .status {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 13px;
    color: #fff;
    white-space: nowrap;
  }}
  .ok {{ background: #2e7d32; }}
  .redirect {{ background: #f9a825; }}
  .fail {{ background: #c62828; }}
  .no-result {{ text-align: center; color: #888; padding: 20px; }}
  .pagination {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
    margin-top: 20px;
  }}
  .page-link {{
    padding: 6px 12px;
    border-radius: 6px;
    background: #fff;
    color: #1565c0;
    text-decoration: none;
    font-size: 13px;
    border: 1px solid #ddd;
  }}
  .page-link:hover {{ background: #f0f0f0; }}
  .page-link.active {{
    background: #1565c0;
    color: #fff;
    border-color: #1565c0;
  }}
</style>
</head>
<body>
<h1>URL Status Checker</h1>
<div class="updated">Terakhir diperbarui: {now_str} &middot; Total {total_items} video &middot; Halaman {current_page} dari {total_pages}</div>
<input type="text" id="searchBox" placeholder="Cari judul video atau URL di halaman ini..." onkeyup="filterTable()">
<div class="search-note">Pencarian hanya berlaku untuk halaman ini. Gunakan navigasi halaman di bawah untuk video lainnya.</div>
<table id="urlTable">
<tr><th>Cover</th><th>Judul Video</th><th>URL</th><th>Status</th></tr>
{rows_html}
</table>
<div id="noResult" class="no-result" style="display:none;">Tidak ada hasil yang cocok.</div>
{pagination_html}
<script>
function filterTable() {{
  var filter = document.getElementById("searchBox").value.toLowerCase();
  var table = document.getElementById("urlTable");
  var trs = table.getElementsByTagName("tr");
  var visibleCount = 0;

  for (var i = 1; i < trs.length; i++) {{
    var tds = trs[i].getElementsByTagName("td");
    var text = (tds[1].textContent + " " + tds[2].textContent).toLowerCase();
    var match = text.indexOf(filter) > -1;
    trs[i].style.display = match ? "" : "none";
    if (match) visibleCount++;
  }}

  document.getElementById("noResult").style.display = visibleCount === 0 ? "block" : "none";
}}
</script>
</body>
</html>
"""
    return page


def cleanup_old_pages(total_pages):
    """Hapus file page*.html sisa dari run sebelumnya kalau jumlah halaman sekarang lebih sedikit."""
    for f in glob.glob("page*.html"):
        m = re.match(r"page(\d+)\.html$", f)
        if not m:
            continue
        page_num = int(m.group(1))
        if page_num > total_pages:
            os.remove(f)
            print(f"Hapus halaman lama yang sudah tidak terpakai: {f}")


def write_pages(results):
    now_str = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S WIB")
    total_items = len(results)
    total_pages = max(1, math.ceil(total_items / ITEMS_PER_PAGE))

    cleanup_old_pages(total_pages)

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        items = results[start:end]

        page_html = render_page(items, page_num, total_pages, now_str, total_items)
        filename = "index.html" if page_num == 1 else f"page{page_num}.html"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"{filename} dibuat ({len(items)} item)")


if __name__ == "__main__":
    results = main()
    write_pages(results)
    print("Semua halaman berhasil dibuat.")
