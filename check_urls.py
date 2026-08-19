import cloudscraper
import re
import html
import sys
import time

def extract_title(content):
    """Coba ambil og:title dulu (server-rendered), fallback ke <title> biasa."""
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)["\']', content, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:title["\']', content, re.IGNORECASE)
    if not m:
        m = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)

    if not m:
        return None

    title = html.unescape(m.group(1)).strip()
    title = re.sub(r'\s+', ' ', title)
    return title


def load_urls(path="urls.txt"):
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def main():
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False
        }
    )
    # Paksa User-Agent Chrome versi baru — beberapa situs (termasuk vkvideo.ru) menolak
    # User-Agent lama dari daftar bawaan cloudscraper dan malah nampilin halaman
    # "browser kamu ketinggalan zaman" (status 200, tapi bukan halaman aslinya).
    scraper.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    })

    urls = load_urls()
    results = []

    for url in urls:
        title = "-"
        status = None

        try:
            response = scraper.get(url, timeout=20)
            status = response.status_code

            if 200 <= status < 400:
                extracted = extract_title(response.text)
                title = extracted if extracted else "(Tanpa Judul)"

        except Exception as e:
            # kalau request gagal total (bukan dapat response HTTP), pakai nama exception sbg penanda
            status = type(e).__name__
            title = "-"
            print(f"  -> Gagal cek {url}: {e}", file=sys.stderr)

        print(f"Cek: {url} -> [{title}] -> {status}")
        results.append((url, title, status))
        time.sleep(1)  # jeda kecil antar-request biar nggak keliatan kayak burst bot

    return results


def render_html(results):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S WIB")

    rows = []
    for url, title, status in results:
        status_str = str(status)
        if status_str.isdigit() and 200 <= int(status_str) < 300:
            css = "ok"
        elif status_str.isdigit() and 300 <= int(status_str) < 400:
            css = "redirect"
        else:
            css = "fail"

        safe_title = html.escape(str(title))
        safe_url = html.escape(url)

        rows.append(
            f'<tr><td>{safe_title}</td>'
            f'<td><a href="{safe_url}" target="_blank" rel="noopener">{safe_url}</a></td>'
            f'<td><span class="status {css}">{html.escape(status_str)}</span></td></tr>'
        )

    rows_html = "\n".join(rows)

    page = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>URL Status Checker</title>
<style>
  body {{
    font-family: -apple-system, Arial, sans-serif;
    max-width: 900px;
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
    vertical-align: top;
  }}
  th {{ background: #fafafa; }}
  td a {{ color: #1565c0; text-decoration: none; word-break: break-all; }}
  td a:hover {{ text-decoration: underline; }}
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
</style>
</head>
<body>
<h1>URL Status Checker</h1>
<div class="updated">Terakhir diperbarui: {now}</div>
<input type="text" id="searchBox" placeholder="Cari judul video atau URL..." onkeyup="filterTable()">
<table id="urlTable">
<tr><th>Judul Video</th><th>URL</th><th>Status</th></tr>
{rows_html}
</table>
<div id="noResult" class="no-result" style="display:none;">Tidak ada hasil yang cocok.</div>
<script>
function filterTable() {{
  var filter = document.getElementById("searchBox").value.toLowerCase();
  var table = document.getElementById("urlTable");
  var trs = table.getElementsByTagName("tr");
  var visibleCount = 0;

  for (var i = 1; i < trs.length; i++) {{
    var tds = trs[i].getElementsByTagName("td");
    var text = (tds[0].textContent + " " + tds[1].textContent).toLowerCase();
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

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    results = main()
    render_html(results)
    print("index.html berhasil dibuat.")
