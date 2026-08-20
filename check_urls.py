import cloudscraper
import html
import json
import sys
import time
import glob
import os
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_FILE = "videos.json"
SITE_TITLE = "Arsip Video Saya"  # ganti di sini kalau mau ubah nama halaman


def load_videos(path=DATA_FILE):
    """Baca daftar video dari file JSON. Tiap entri wajib punya 'url', field lain opsional."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        print(f"ERROR: {path} harus berupa JSON array (list), bukan {type(raw).__name__}.", file=sys.stderr)
        sys.exit(1)

    videos = []
    for idx, entry in enumerate(raw, 1):
        if not isinstance(entry, dict):
            print(f"  -> Entri ke-{idx} diabaikan (bukan object JSON): {entry}", file=sys.stderr)
            continue

        url = str(entry.get("url", "")).strip()
        if not url:
            print(f"  -> Entri ke-{idx} diabaikan (field 'url' kosong/tidak ada)", file=sys.stderr)
            continue

        judul = str(entry.get("judul", "")).strip() or "(Tanpa Judul)"
        cover = str(entry.get("cover", "")).strip()
        kategori = str(entry.get("kategori", "")).strip() or "Lainnya"

        rasio = str(entry.get("rasio", "")).strip().replace(" ", "")
        if rasio not in ("16:9", "3:2"):
            if rasio:
                print(f"  -> Entri ke-{idx}: rasio '{rasio}' tidak dikenali, pakai default 16:9", file=sys.stderr)
            rasio = "16:9"

        videos.append({"url": url, "judul": judul, "cover": cover, "kategori": kategori, "rasio": rasio})

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
        if status == 200:
            print(f"Cek: {v['url']} -> [{v['judul']}] ({v['kategori']}) -> {status} (DITAMPILKAN)")
            results.append({
                "judul": v["judul"],
                "url": v["url"],
                "cover": v["cover"],
                "kategori": v["kategori"],
                "rasio": v["rasio"],
            })
        else:
            print(f"Cek: {v['url']} -> [{v['judul']}] ({v['kategori']}) -> {status} (DISEMBUNYIKAN, bukan 200)")
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

  .theme-switch {
    position: relative;
    display: inline-block;
    width: 46px;
    height: 26px;
    flex-shrink: 0;
  }
  .theme-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .theme-slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background: var(--border);
    border-radius: 999px;
    transition: background 0.2s;
  }
  .theme-slider::before {
    content: "";
    position: absolute;
    width: 20px;
    height: 20px;
    left: 3px;
    top: 3px;
    background: #fff;
    border-radius: 50%;
    transition: transform 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  }
  .theme-switch input:checked + .theme-slider {
    background: var(--accent);
  }
  .theme-switch input:checked + .theme-slider::before {
    transform: translateX(20px);
  }
  .search-note { color: var(--muted); font-size: 12px; margin: -6px 0 16px; }

  .category-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
  }
  .category-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
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

<div class="category-row">
  <div class="category-tabs" id="categoryTabs"></div>
  <label class="theme-switch">
    <input type="checkbox" id="themeToggle">
    <span class="theme-slider"></span>
  </label>
</div>

<div class="toolbar">
  <input type="text" id="searchBox" placeholder="Cari judul video atau URL...">
  <button id="searchBtn">Cari</button>
</div>

<table id="urlTable">
  <thead>
    <tr><th>Cover</th><th>Judul Video</th><th>Link Video</th></tr>
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
  var searchBtn = document.getElementById("searchBtn");
  var themeToggle = document.getElementById("themeToggle");
  var categoryTabsEl = document.getElementById("categoryTabs");

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderRow(item) {
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
      '<td><a href="' + escapeHtml(item.url) + '">' + escapeHtml(item.url) + '</a></td>' +
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

  searchBtn.addEventListener("click", function () {
    currentPage = 1;
    applyFilter();
  });

  searchBox.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      currentPage = 1;
      applyFilter();
    }
  });

  // --- Tema (light/dark) via toggle switch, disimpan supaya nyaman dipakai lagi ---
  var savedTheme = localStorage.getItem("urlchecker-theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  themeToggle.checked = savedTheme === "dark";
  themeToggle.addEventListener("change", function () {
    var next = themeToggle.checked ? "dark" : "light";
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
