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
SITE_TITLE = "SeputarBokep99"


def load_videos(path=DATA_FILE):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        print(f"ERROR: {path} harus berupa JSON array.", file=sys.stderr)
        sys.exit(1)

    videos = []
    for idx, entry in enumerate(raw, 1):
        if not isinstance(entry, dict):
            continue

        url = str(entry.get("url", "")).strip()
        if not url:
            continue

        judul = str(entry.get("judul", "")).strip() or "(Tanpa Judul)"
        cover = str(entry.get("cover", "")).strip()
        kategori = str(entry.get("kategori", "")).strip() or "Lainnya"

        rasio = str(entry.get("rasio", "")).strip().replace(" ", "")
        if rasio not in ("16:9", "3:2"):
            rasio = "16:9"

        videos.append({"url": url, "judul": judul, "cover": cover, "kategori": kategori, "rasio": rasio})

    return videos


def check_status(scraper, url):
    try:
        timeout = 30 if "vk.ru" in url else 15
        response = scraper.get(url, timeout=timeout)
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
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://vk.com/",
    })

    videos = load_videos()
    results = []

    for v in videos:
        status = check_status(scraper, v["url"])
        if status == 200:
            print(f"Cek: {v['url']} -> [{v['judul']}] ({v['kategori']}) -> {status} (DITAMPILKAN)")
            results.append(v)
        else:
            print(f"Cek: {v['url']} -> [{v['judul']}] ({v['kategori']}) -> {status} (DISEMBUNYIKAN)")
        time.sleep(0.5)

    return results


def cleanup_legacy_pages():
    for f in glob.glob("page*.html"):
        os.remove(f)
        print(f"Hapus file lama: {f}")


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
    --hover-bg: #f0f0f0;
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
    --hover-bg: #2c2c2c;
  }
  
  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    transition: background 0.3s, color 0.3s;
    overflow-x: hidden; /* Mencegah scroll horizontal */
  }

  /* Header Area */
  header {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  h1 { 
    font-size: 24px; 
    font-weight: 800; 
    letter-spacing: -0.5px;
    color: var(--text);
  }

  .theme-switch {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
  }
  .theme-switch input { opacity: 0; width: 0; height: 0; }
  .theme-slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: var(--border);
    border-radius: 34px;
    transition: .4s;
  }
  .theme-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    border-radius: 50%;
    transition: .4s;
  }
  .theme-switch input:checked + .theme-slider { background-color: var(--accent); }
  .theme-switch input:checked + .theme-slider:before { transform: translateX(20px); }

  /* Search Bar */
  .search-container {
    position: relative;
    max-width: 800px;
    margin: 0 auto;
  }
  #searchBox {
    width: 100%;
    padding: 12px 20px;
    border: 2px solid var(--border);
    border-radius: 12px;
    font-size: 16px;
    background: var(--input-bg);
    color: var(--text);
    outline: none;
    transition: border-color 0.2s;
  }
  #searchBox:focus { border-color: var(--accent); }

  /* Category Tabs */
  .category-wrapper {
    background: var(--bg);
    padding: 12px 24px;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  .category-tabs {
    display: flex;
    gap: 10px;
    max-width: 1200px;
    margin: 0 auto;
  }
  .tab {
    padding: 8px 20px;
    border-radius: 20px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
  }
  .tab:hover { border-color: var(--accent); color: var(--accent); }
  .tab.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }

  /* Main Content Grid - FULL WIDTH TANPA PADDING */
  main {
    flex: 1;
    width: 100%;
    padding: 0; /* HAPUS PADDING KIRI/KANAN */
    margin: 0;
  }

  .video-grid {
    display: grid;
    /* Grid otomatis mengisi lebar penuh, minimal 250px per kartu */
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 0; /* HAPUS GAP AGAR RAPAT */
    width: 100%;
  }

  .video-card {
    background: var(--card-bg);
    border-radius: 0; /* HAPUS BORDER RADIUS AGAR LEBIH KOTAK */
    overflow: hidden;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
    border-right: none; /* Hapus border kanan agar tidak double */
    border-bottom: none; /* Hapus border bawah agar tidak double */
    height: 100%;
  }
  
  /* Tambahkan border kanan untuk kolom terakhir */
  .video-card:nth-child(4n) {
    border-right: 1px solid var(--border);
  }
  
  /* Tambahkan border bawah untuk baris terakhir */
  .video-card:nth-last-child(-n+4) {
    border-bottom: 1px solid var(--border);
  }

  .video-card:hover {
    background: var(--hover-bg);
    z-index: 1;
    position: relative;
  }

  .cover-container {
    position: relative;
    width: 100%;
    background: var(--header-bg);
    overflow: hidden;
    display: block;
    cursor: pointer;
  }
  
  /* Aspect Ratio Handling */
  .cover-container.ratio-16-9 { aspect-ratio: 16 / 9; }
  .cover-container.ratio-3-2 { aspect-ratio: 3 / 2; }

  .cover-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: opacity 0.3s;
  }
  .cover-img.broken { opacity: 0.5; }
  
  .no-cover {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-size: 14px;
    background: var(--header-bg);
  }

  .card-info {
    padding: 12px;
    flex: 1;
    display: flex;
    flex-direction: column;
    border-top: 1px solid var(--border);
  }

  .video-title {
    font-size: 14px;
    font-weight: 600;
    line-height: 1.4;
    color: var(--text);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .no-result {
    grid-column: 1 / -1;
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
    font-size: 18px;
    background: var(--card-bg);
    border: 1px dashed var(--border);
  }

  /* Pagination */
  .pagination {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 40px;
    padding: 20px;
    background: var(--bg);
  }
  .page-btn {
    padding: 8px 16px;
    border-radius: 8px;
    background: var(--card-bg);
    color: var(--text);
    border: 1px solid var(--border);
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
  }
  .page-btn:hover:not(.disabled) { background: var(--hover-bg); border-color: var(--accent); }
  .page-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  .page-btn.disabled { opacity: 0.5; cursor: not-allowed; }

  /* Footer */
  footer {
    background: var(--card-bg);
    border-top: 1px solid var(--border);
    padding: 24px;
    text-align: center;
    color: var(--muted);
    font-size: 14px;
    margin-top: auto;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .video-grid { 
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); 
    }
    header { padding: 12px 16px; }
    .card-info { padding: 10px; }
    .video-title { font-size: 13px; }
    
    /* Reset border logic untuk mobile */
    .video-card { border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); }
    .video-card:nth-child(4n) { border-right: 1px solid var(--border); }
    .video-card:nth-last-child(-n+4) { border-bottom: 1px solid var(--border); }
  }
</style>
</head>
<body>

<header>
  <div class="header-top">
    <h1>__SITE_TITLE__</h1>
    <label class="theme-switch">
      <input type="checkbox" id="themeToggle">
      <span class="theme-slider"></span>
    </label>
  </div>
  <div class="search-container">
    <input type="text" id="searchBox" placeholder="Cari video...">
  </div>
</header>

<div class="category-wrapper">
  <div class="category-tabs" id="categoryTabs"></div>
</div>

<main>
  <div class="video-grid" id="videoGrid"></div>
  <div id="noResult" class="no-result" style="display:none;">Tidak ada video yang cocok.</div>
  
  <div id="pagination" class="pagination"></div>
</main>

<footer>
  Copyright @ team 2026
</footer>

<script type="application/json" id="video-data">__DATA_JSON__</script>
<script>
(function () {
  var ALL_DATA = JSON.parse(document.getElementById("video-data").textContent);
  var ITEMS_PER_PAGE = 20;
  var currentPage = 1;
  var currentCategory = null;
  var filtered = [];

  var videoGrid = document.getElementById("videoGrid");
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

  function createCard(item) {
    var ratioClass = item.rasio === "3:2" ? "ratio-3-2" : "ratio-16-9";
    
    var coverHtml;
    if (item.cover) {
      coverHtml = '<img src="' + escapeHtml(item.cover) + '" alt="cover" loading="lazy" class="cover-img" ' +
        'onerror="this.onerror=null;this.classList.add(\'broken\');this.alt=\'Error\';">';
    } else {
      coverHtml = '<div class="no-cover">No Cover</div>';
    }

    // Cover clickable, tidak ada link teks
    var coverLink = '<a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener noreferrer" class="cover-container ' + ratioClass + '">' + coverHtml + '</a>';

    return '<div class="video-card">' +
      coverLink +
      '<div class="card-info">' +
        '<div class="video-title">' + escapeHtml(item.judul) + '</div>' +
      '</div>' +
    '</div>';
  }

  function renderCategoryTabs() {
    var categories = [];
    ALL_DATA.forEach(function (item) {
      if (categories.indexOf(item.kategori) === -1) categories.push(item.kategori);
    });

    if (categories.length === 0) {
      categoryTabsEl.parentElement.style.display = 'none';
      return;
    }

    if (!currentCategory && categories.length > 0) {
      currentCategory = categories[0];
    }

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
      videoGrid.innerHTML = "";
      noResult.style.display = "block";
    } else {
      noResult.style.display = "none";
      videoGrid.innerHTML = pageItems.map(createCard).join("");
    }

    renderPagination(totalPages);
  }

  function renderPagination(totalPages) {
    if (totalPages <= 1) {
      paginationEl.innerHTML = "";
      return;
    }
    var parts = [];
    
    parts.push('<button class="page-btn' + (currentPage === 1 ? ' disabled' : '') + '" data-page="1">Pertama</button>');
    
    var startPage = Math.max(1, currentPage - 2);
    var endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) parts.push('<span class="page-btn disabled">...</span>');

    for (var p = startPage; p <= endPage; p++) {
      parts.push('<button class="page-btn' + (p === currentPage ? ' active' : '') + '" data-page="' + p + '">' + p + '</button>');
    }

    if (endPage < totalPages) parts.push('<span class="page-btn disabled">...</span>');

    parts.push('<button class="page-btn' + (currentPage === totalPages ? ' disabled' : '') + '" data-page="' + totalPages + '">Terakhir</button>');

    paginationEl.innerHTML = parts.join("\n");

    paginationEl.querySelectorAll(".page-btn:not(.disabled)").forEach(function (el) {
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
      var matchCategory = !currentCategory || item.kategori === currentCategory;
      var matchSearch = !q || item.judul.toLowerCase().indexOf(q) > -1 || item.url.toLowerCase().indexOf(q) > -1;
      return matchCategory && matchSearch;
    });

    render();
  }

  searchBox.addEventListener("input", function () {
    currentPage = 1;
    applyFilter();
  });

  var savedTheme = localStorage.getItem("urlchecker-theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  themeToggle.checked = savedTheme === "dark";
  themeToggle.addEventListener("change", function () {
    var next = themeToggle.checked ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("urlchecker-theme", next);
  });

  renderCategoryTabs();
  applyFilter();
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
