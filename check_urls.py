import cloudscraper
import html
import json
import sys
import time
import glob
import os
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_FILE = "videos.txt"
SITE_TITLE = "SeputarBokep99"


def load_videos(path=DATA_FILE):
    """Baca url|judul|cover|kategori dari file txt. Baris kosong / diawali # diabaikan."""
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
            kategori = parts[3].strip() if len(parts) > 3 else ""
            rasio = parts[4].strip() if len(parts) > 4 else ""

            if not url:
                continue
            if not judul:
                judul = "(Tanpa Judul)"
            if not kategori:
                kategori = "Lainnya"

            rasio_normalized = rasio.replace(" ", "")
            if rasio_normalized not in ("16:9", "3:2"):
                if rasio_normalized:
                    print(f"  -> Baris {line_num}: rasio '{rasio}' tidak dikenali, pakai default 16:9", file=sys.stderr)
                rasio_normalized = "16:9"

            videos.append({"url": url, "judul": judul, "cover": cover, "kategori": kategori, "rasio": rasio_normalized})
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
        print(f"Cek: {v['url']} -> [{v['judul']}] ({v['kategori']}) -> {status}")
        results.append({
            "judul": v["judul"],
            "url": v["url"],
            "cover": v["cover"],
            "kategori": v["kategori"],
            "rasio": v["rasio"],
            "status": str(status),
        })
        time.sleep(1)  # jeda kecil antar-request biar nggak keliatan kayak burst bot

    return results


def cleanup_legacy_pages():
    """Hapus file page*.html dari versi lama (sekarang paginasi full client-side, 1 file aja)."""
    for f in glob.glob("page*.html"):
        os.remove(f)
        print(f"Hapus file lama yang sudah tidak dipakai: {f}")


def build_html(results):
    now_str = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S WIB")
    total_items = len(results)

    json_data = json.dumps(results, ensure_ascii=False)
    json_data_safe = json_data.replace("</script", "<\\/script").replace("<!--", "<\\!--")

    template = HTML_TEMPLATE
    template = template.replace("__SITE_TITLE__", html.escape(SITE_TITLE))
    template = template.replace("__NOW__", html.escape(now_str))
    template = template.replace("__TOTAL__", str(total_items))
    template = template.replace("__DATA_JSON__", json_data_safe)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(template)
    print(f"index.html dibuat ({total_items} video)")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="id" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__SITE_TITLE__</title>
<style>
  :root {
    --bg: #f5f5f5;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --muted: #666666;
    --border: #e0e0e0;
    --header-bg: #fafafa;
    --link: #1565c0;
    --input-bg: #ffffff;
    --btn-bg: #ffffff;
    --btn-text: #1565c0;
    --accent: #1565c0;
    --cover-ratio: 16 / 9;
  }
  [data-theme="dark"] {
    --bg: #121212;
    --card-bg: #1e1e1e;
    --text: #e8e8e8;
    --muted: #a0a0a0;
    --border: #333333;
    --header-bg: #262626;
    --link: #64b5f6;
    --input-bg: #2a2a2a;
    --btn-bg: #2a2a2a;
    --btn-text: #64b5f6;
    --accent: #64b5f6;
  }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    max-width: 1100px;
    margin: 40px auto;
    padding: 0 20px;
    background: var(--bg);
    color: var(--text);
    transition: background 0.2s, color 0.2s;
  }
  h1 { font-size: 26px; margin-bottom: 4px; letter-spacing: 0.5px; }
  .updated { color: var(--muted); font-size: 13px; margin-bottom: 16px; }

  .toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-bottom: 14px;
  }
  #searchBox {
    flex: 1 1 260px;
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 14px;
    background: var(--input-bg);
    color: var(--text);
  }
  .toolbar select, .toolbar button {
    padding: 9px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--btn-bg);
    color: var(--btn-text);
    font-size: 13px;
    cursor: pointer;
  }
  .search-note { color: var(--muted); font-size: 12px; margin: -6px 0 16px; }

  .category-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
  }
  .tab {
    padding: 8px 18px;
    border-radius: 999px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }
  .tab:hover { border-color: var(--accent); }
  .tab.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    background: var(--card-bg);
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  th, td {
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
    vertical-align: middle;
  }
  th { background: var(--header-bg); }
  td a { color: var(--link); text-decoration: none; word-break: break-all; }
  td a:hover { text-decoration: underline; }

  .cover-cell { width: 130px; }
  .cover-cell img {
    width: 120px;
    object-fit: cover;
    border-radius: 4px;
    display: block;
    background: var(--header-bg);
  }
  .no-cover-placeholder, .cover-cell img.broken {
    width: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--header-bg);
    color: var(--muted);
    font-size: 11px;
    border-radius: 4px;
    text-align: center;
  }

  .status {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 13px;
    color: #fff;
    white-space: nowrap;
  }
  .ok { background: #2e7d32; }
  .redirect { background: #f9a825; }
  .fail { background: #c62828; }

  .no-result { text-align: center; color: var(--muted); padding: 24px; background: var(--card-bg); }

  .pagination {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
    margin-top: 20px;
  }
  .page-link {
    padding: 6px 12px;
    border-radius: 6px;
    background: var(--btn-bg);
    color: var(--link);
    text-decoration: none;
    font-size: 13px;
    border: 1px solid var(--border);
    cursor: pointer;
  }
  .page-link:hover { opacity: 0.8; }
  .page-link.active { background: var(--link); color: #fff; border-color: var(--link); }
  .page-link.disabled { opacity: 0.4; cursor: default; pointer-events: none; }
</style>
</head>
<body>
<h1>__SITE_TITLE__</h1>
<div class="updated">Terakhir diperbarui: __NOW__ &middot; Total __TOTAL__ video</div>

<div class="category-tabs" id="categoryTabs"></div>

<div class="toolbar">
  <input type="text" id="searchBox" placeholder="Cari judul video atau URL (semua halaman & kategori)...">
  <button id="themeToggle">Ganti Tema</button>
</div>
<div class="search-note">Pencarian berlaku untuk semua data pada kategori yang sedang dipilih.</div>

<table id="urlTable">
  <thead>
    <tr><th>Cover</th><th>Judul Video</th><th>Link Video</th><th>Status Code</th></tr>
  </thead>
  <tbody id="tableBody"></tbody>
</table>
<div id="noResult" class="no-result" style="display:none;">Tidak ada hasil yang cocok.</div>
<div id="pagination" class="pagination"></div>

<script type="application/json" id="video-data">__DATA_JSON__</script>
<script>
(function () {
  var ALL_DATA = JSON.parse(document.getElementById("video-data").textContent);
  var ITEMS_PER_PAGE = 20;
  var currentPage = 1;
  var currentCategory = "Semua";
  var filtered = ALL_DATA;

  var tableBody = document.getElementById("tableBody");
  var noResult = document.getElementById("noResult");
  var paginationEl = document.getElementById("pagination");
  var searchBox = document.getElementById("searchBox");
  var themeToggle = document.getElementById("themeToggle");
  var categoryTabsEl = document.getElementById("categoryTabs");

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function statusClass(status) {
    var s = String(status);
    if (/^\d+$/.test(s)) {
      var n = parseInt(s, 10);
      if (n >= 200 && n < 300) return "ok";
      if (n >= 300 && n < 400) return "redirect";
    }
    return "fail";
  }

  function renderRow(item) {
    var css = statusClass(item.status);
    var ratioCss = item.rasio === "3:2" ? "3/2" : "16/9";
    var coverHtml;
    if (item.cover) {
      coverHtml = '<img src="' + escapeHtml(item.cover) + '" alt="cover" loading="lazy" style="aspect-ratio:' + ratioCss + '" ' +
        'onerror="this.onerror=null;this.src=\'\';this.alt=\'(gagal load)\';this.classList.add(\'broken\')">';
    } else {
      coverHtml = '<div class="no-cover-placeholder" style="aspect-ratio:' + ratioCss + '">Tidak ada cover</div>';
    }
    return '<tr>' +
      '<td class="cover-cell">' + coverHtml + '</td>' +
      '<td>' + escapeHtml(item.judul) + '</td>' +
      '<td><a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener">' + escapeHtml(item.url) + '</a></td>' +
      '<td><span class="status ' + css + '">' + escapeHtml(item.status) + '</span></td>' +
      '</tr>';
  }

  function renderCategoryTabs() {
    var categories = ["Semua"];
    ALL_DATA.forEach(function (item) {
      if (categories.indexOf(item.kategori) === -1) categories.push(item.kategori);
    });

    categoryTabsEl.innerHTML = categories.map(function (cat) {
      var activeClass = cat === currentCategory ? " active" : "";
      return '<span class="tab' + activeClass + '" data-cat="' + escapeHtml(cat) + '">' + escapeHtml(cat) + '</span>';
    }).join("");

    categoryTabsEl.querySelectorAll(".tab").forEach(function (el) {
      el.addEventListener("click", function () {
        currentCategory = el.getAttribute("data-cat");
        currentPage = 1;
        applyFilter();
        renderCategoryTabs();
      });
    });
  }

  function render() {
    var totalItems = filtered.length;
    var totalPages = Math.max(1, Math.ceil(totalItems / ITEMS_PER_PAGE));
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    var start = (currentPage - 1) * ITEMS_PER_PAGE;
    var pageItems = filtered.slice(start, start + ITEMS_PER_PAGE);

    if (pageItems.length === 0) {
      tableBody.innerHTML = "";
      noResult.style.display = "block";
    } else {
      noResult.style.display = "none";
      tableBody.innerHTML = pageItems.map(renderRow).join("");
    }

    renderPagination(totalPages);
  }

  function renderPagination(totalPages) {
    if (totalPages <= 1) {
      paginationEl.innerHTML = "";
      return;
    }
    var parts = [];
    parts.push('<span class="page-link' + (currentPage === 1 ? ' disabled' : '') + '" data-page="1">Pertama</span>');
    for (var p = 1; p <= totalPages; p++) {
      parts.push('<span class="page-link' + (p === currentPage ? ' active' : '') + '" data-page="' + p + '">' + p + '</span>');
    }
    parts.push('<span class="page-link' + (currentPage === totalPages ? ' disabled' : '') + '" data-page="' + totalPages + '">Terakhir</span>');
    paginationEl.innerHTML = parts.join("\n");

    paginationEl.querySelectorAll(".page-link:not(.disabled)").forEach(function (el) {
      el.addEventListener("click", function () {
        currentPage = parseInt(el.getAttribute("data-page"), 10);
        render();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  }

  function applyFilter() {
    var q = searchBox.value.trim().toLowerCase();

    filtered = ALL_DATA.filter(function (item) {
      var matchCategory = currentCategory === "Semua" || item.kategori === currentCategory;
      var matchSearch = !q || item.judul.toLowerCase().indexOf(q) > -1 || item.url.toLowerCase().indexOf(q) > -1;
      return matchCategory && matchSearch;
    });

    render();
  }

  searchBox.addEventListener("input", function () {
    currentPage = 1;
    applyFilter();
  });

  // --- Tema (light/dark), disimpan supaya nyaman dipakai lagi ---
  var savedTheme = localStorage.getItem("urlchecker-theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  themeToggle.addEventListener("click", function () {
    var current = document.documentElement.getAttribute("data-theme");
    var next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("urlchecker-theme", next);
  });

  // --- Rasio cover sekarang ditentukan per video lewat kolom RASIO di videos.txt ---

  renderCategoryTabs();
  render();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    cleanup_legacy_pages()
    results = main()
    build_html(results)
    print("Selesai.")
