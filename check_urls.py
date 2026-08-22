import cloudscraper
import html
import json
import sys
import time
import glob
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import re

DATA_FILE = "videos.json"
SITE_TITLE = "SeputarBokep99 💦""


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
        durasi = str(entry.get("durasi", "")).strip()

        rasio = str(entry.get("rasio", "")).strip().replace(" ", "")
        if rasio not in ("16:9", "3:2"):
            rasio = "16:9"

        slug = re.sub(r'[^\w\s-]', '', judul.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        slug = re.sub(r'-+', '-', slug)

        videos.append({
            "url": url,
            "judul": judul,
            "cover": cover,
            "kategori": kategori,
            "rasio": rasio,
            "durasi": durasi,
            "slug": slug
        })

    # REVERSE ORDER: Video terbaru (paling bawah di JSON) jadi paling atas
    videos.reverse()

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
<html lang="id" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__SITE_TITLE__</title>
<style>
  :root {
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
    overflow-x: hidden;
  }

  header {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 20px;
  }

  h1 { 
    font-size: 24px; 
    font-weight: 800; 
    letter-spacing: -0.5px;
    color: var(--text);
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
  }
  h1:hover { opacity: 0.8; }

  .search-container {
    flex: 1;
    display: flex;
    gap: 0;
    max-width: 600px;
    margin-left: auto;
  }
  #searchBox {
    flex: 1;
    padding: 10px 16px;
    border: 2px solid var(--border);
    border-right: none;
    border-radius: 0;
    font-size: 14px;
    background: var(--input-bg);
    color: var(--text);
    outline: none;
    min-width: 0;
  }
  #searchBox:focus { border-color: var(--accent); border-right-color: var(--accent); }
  
  #searchBtn {
    padding: 10px 20px;
    border: 2px solid var(--accent);
    border-radius: 0;
    background: var(--accent);
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
  }
  #searchBtn:hover { opacity: 0.9; }

  .category-wrapper {
    background: var(--bg);
    padding: 12px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    overflow-x: auto;
    white-space: nowrap;
  }
  
  .category-tabs {
    display: flex;
    gap: 0;
    flex: 1;
  }
  
  .tab {
    padding: 10px 24px;
    border-radius: 0;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-right: none;
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }
  .tab:last-child { border-right: 1px solid var(--border); }
  .tab:hover { background: var(--hover-bg); }
  .tab.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }

  .burger-btn {
    display: none;
    padding: 10px 16px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 0;
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }
  .burger-btn:hover { background: var(--hover-bg); }

  main {
    flex: 1;
    width: 100%;
    padding: 24px;
    margin: 0;
  }

  .video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 0;
    width: 100%;
  }

  .video-card {
    background: var(--card-bg);
    border-radius: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
    border-right: none;
    border-bottom: none;
    height: 100%;
  }
  
  .video-card:nth-child(4n) { border-right: 1px solid var(--border); }
  .video-card:nth-last-child(-n+4) { border-bottom: 1px solid var(--border); }

  .cover-container {
    position: relative;
    width: 100%;
    background: var(--header-bg);
    overflow: hidden;
    display: block;
    cursor: pointer;
  }
  
  .cover-container.ratio-16-9 { aspect-ratio: 16 / 9; }
  .cover-container.ratio-3-2 { aspect-ratio: 3 / 2; }

  .cover-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
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

  .duration-badge {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.85);
    color: #ffffff;
    padding: 3px 6px;
    font-size: 12px;
    font-weight: 600;
    border-radius: 4px;
    pointer-events: none;
    z-index: 2;
    letter-spacing: 0.5px;
  }

  .card-info {
    padding: 12px;
    flex: 1;
    display: flex;
    flex-direction: column;
    border-top: 1px solid var(--border);
    background: var(--card-bg);
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

  .pagination {
    display: flex;
    justify-content: center;
    gap: 0;
    margin-top: 32px;
    padding: 0;
  }
  
  .page-btn {
    padding: 10px 18px;
    border-radius: 0;
    background: var(--card-bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-right: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
  }
  .page-btn:last-child { border-right: 1px solid var(--border); }
  .page-btn:hover:not(.disabled) { background: var(--hover-bg); }
  .page-btn.active { 
    background: var(--accent); 
    color: #fff; 
    border-color: var(--accent);
  }
  .page-btn.disabled { 
    opacity: 0.5; 
    cursor: not-allowed;
  }

  .video-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.95);
    z-index: 1000;
    justify-content: center;
    align-items: center;
    padding: 20px;
  }
  
  .video-modal.active {
    display: flex;
  }
  
  .modal-content {
    position: relative;
    width: 100%;
    max-width: 1200px;
    background: var(--card-bg);
    border: 1px solid var(--border);
  }
  
  .modal-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .modal-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
    flex: 1;
    margin-right: 16px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .modal-close {
    padding: 8px 16px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 0;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
  }
  .modal-close:hover { opacity: 0.9; }
  
  .modal-body {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
  }
  
  .modal-body iframe {
    width: 100%;
    height: 100%;
    border: none;
  }

  footer {
    background: var(--card-bg);
    border-top: 1px solid var(--border);
    padding: 24px;
    text-align: center;
    color: var(--muted);
    font-size: 14px;
    margin-top: auto;
  }

  @media (max-width: 768px) {
    .video-grid { 
      grid-template-columns: 1fr;
    }
    
    header { 
      padding: 12px 16px; 
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }
    h1 { text-align: center; }
    .search-container { 
      max-width: 100%; 
      margin-left: 0;
    }
    #searchBox { padding: 10px 14px; font-size: 14px; }
    #searchBtn { padding: 10px 18px; font-size: 14px; }
    
    .category-wrapper { 
      padding: 12px 16px; 
      flex-direction: column;
      align-items: stretch;
    }
    main { padding: 16px; }
    .card-info { padding: 12px; }
    .video-title { font-size: 14px; }
    
    .burger-btn { display: block; margin-bottom: 0; }
    
    .category-tabs {
      display: none;
      flex-direction: column;
      margin-top: 8px;
    }
    .category-tabs.open {
      display: flex;
    }
    .tab {
      border-right: 1px solid var(--border);
      border-bottom: none;
    }
    .tab:last-child { border-bottom: 1px solid var(--border); }
    
    .video-card { border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); }
    .video-card:nth-child(4n) { border-right: 1px solid var(--border); }
    .video-card:nth-last-child(-n+4) { border-bottom: 1px solid var(--border); }
    
    .pagination {
      flex-wrap: wrap;
      gap: 0;
    }
    .page-btn {
      padding: 8px 14px;
      font-size: 13px;
    }
    
    .modal-content {
      max-width: 100%;
    }
    .modal-title {
      font-size: 16px;
    }
  }
</style>
</head>
<body>

<header>
  <h1 onclick="goHome()" title="Klik untuk kembali ke beranda">__SITE_TITLE__</h1>
  <div class="search-container">
    <input type="text" id="searchBox" placeholder="Cari video...">
    <button id="searchBtn">Cari</button>
  </div>
</header>

<div class="category-wrapper">
  <button class="burger-btn" id="burgerBtn">☰ Kategori</button>
  <div class="category-tabs" id="categoryTabs"></div>
</div>

<main>
  <div class="video-grid" id="videoGrid"></div>
  <div id="noResult" class="no-result" style="display:none;">Tidak ada video yang cocok.</div>
  <div id="pagination" class="pagination"></div>
</main>

<footer>
  Dibuat dengan ❤️ dan ☕
</footer>

<div class="video-modal" id="videoModal">
  <div class="modal-content">
    <div class="modal-header">
      <div class="modal-title" id="modalTitle">Judul Video</div>
      <button class="modal-close" id="modalClose">Tutup</button>
    </div>
    <div class="modal-body">
      <iframe id="videoPlayer" src="" allowfullscreen></iframe>
    </div>
  </div>
</div>

<script type="application/json" id="video-data">__DATA_JSON__</script>
<script>
(function () {
  var ALL_DATA = JSON.parse(document.getElementById("video-data").textContent);
  var ITEMS_PER_PAGE = 30;
  var currentPage = 1;
  var currentCategory = null;
  var currentSearch = "";
  var filtered = [];
  var previousURL = "";

  var videoGrid = document.getElementById("videoGrid");
  var noResult = document.getElementById("noResult");
  var paginationEl = document.getElementById("pagination");
  var searchBox = document.getElementById("searchBox");
  var searchBtn = document.getElementById("searchBtn");
  var categoryTabsEl = document.getElementById("categoryTabs");
  var burgerBtn = document.getElementById("burgerBtn");
  var videoModal = document.getElementById("videoModal");
  var videoPlayer = document.getElementById("videoPlayer");
  var modalTitle = document.getElementById("modalTitle");
  var modalClose = document.getElementById("modalClose");

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function getParams() {
    var params = new URLSearchParams(window.location.search);
    return {
      cat: params.get("cat") || null,
      page: parseInt(params.get("page")) || 1,
      q: params.get("q") || "",
      play: params.get("play") || null
    };
  }

  function updateURL() {
    var params = new URLSearchParams();
    if (currentCategory) params.set("cat", currentCategory);
    if (currentPage > 1) params.set("page", currentPage.toString());
    if (currentSearch) params.set("q", currentSearch);
    
    var newUrl = window.location.pathname;
    var queryString = params.toString();
    if (queryString) newUrl += "?" + queryString;
    window.history.replaceState({}, "", newUrl);
  }

  function loadStateFromURL() {
    var params = getParams();
    if (params.cat) {
      var validCategories = [];
      ALL_DATA.forEach(function (item) {
        if (validCategories.indexOf(item.kategori) === -1) validCategories.push(item.kategori);
      });
      if (validCategories.indexOf(params.cat) > -1) currentCategory = params.cat;
    }
    if (params.page && params.page > 0) currentPage = params.page;
    if (params.q) {
      currentSearch = params.q;
      searchBox.value = currentSearch;
    }
    if (params.play) {
      var slugToFind = decodeURIComponent(params.play).toLowerCase();
      var videoToPlay = ALL_DATA.find(function (item) {
        return item.slug === slugToFind;
      });
      if (videoToPlay) {
        currentCategory = videoToPlay.kategori;
        openVideoPlayer(videoToPlay.url, videoToPlay.judul);
      }
    }
  }

  window.goHome = function() {
    currentCategory = getFirstCategory();
    currentSearch = "";
    currentPage = 1;
    searchBox.value = "";
    window.history.replaceState({}, "", window.location.pathname);
    renderCategoryTabs();
    applyFilter();
  };

  function getSortedCategories() {
    var categories = [];
    ALL_DATA.forEach(function (item) {
      if (categories.indexOf(item.kategori) === -1) categories.push(item.kategori);
    });
    categories.sort(function(a, b) {
      return a.toLowerCase().localeCompare(b.toLowerCase());
    });
    return categories;
  }

  function getFirstCategory() {
    var categories = getSortedCategories();
    return categories.length > 0 ? categories[0] : null;
  }

  function createCard(item) {
    var ratioClass = item.rasio === "3:2" ? "ratio-3-2" : "ratio-16-9";
    var coverHtml = item.cover 
      ? '<img src="' + escapeHtml(item.cover) + '" alt="cover" loading="lazy" class="cover-img" onerror="this.onerror=null;this.classList.add(\'broken\');this.alt=\'Error\';">'
      : '<div class="no-cover">No Cover</div>';
    
    var durationHtml = item.durasi ? '<div class="duration-badge">' + escapeHtml(item.durasi) + '</div>' : '';
    
    var coverLink = '<div class="cover-container ' + ratioClass + '" data-url="' + escapeHtml(item.url) + '" data-title="' + escapeHtml(item.judul) + '" data-slug="' + escapeHtml(item.slug) + '">' + 
      coverHtml + 
      durationHtml + 
    '</div>';

    return '<div class="video-card">' +
      coverLink +
      '<div class="card-info"><div class="video-title">' + escapeHtml(item.judul) + '</div></div>' +
    '</div>';
  }

  function openVideoPlayer(url, title, slug) {
    modalTitle.textContent = title;
    videoPlayer.src = url;
    videoModal.classList.add("active");
    document.body.style.overflow = "hidden";
    previousURL = window.location.href;
    var params = new URLSearchParams(window.location.search);
    params.set("play", slug || title.toLowerCase().replace(/\s+/g, '-'));
    var newUrl = window.location.pathname + "?" + params.toString();
    window.history.replaceState({}, "", newUrl);
  }

  function closeVideoPlayer() {
    videoPlayer.src = "";
    videoModal.classList.remove("active");
    document.body.style.overflow = "";
    var params = new URLSearchParams(window.location.search);
    params.delete("play");
    var newUrl = window.location.pathname;
    var queryString = params.toString();
    if (queryString) newUrl += "?" + queryString;
    window.history.replaceState({}, "", newUrl);
  }

  function renderCategoryTabs() {
    var categories = getSortedCategories();

    if (categories.length === 0) {
      categoryTabsEl.parentElement.style.display = 'none';
      return;
    }

    if (!currentCategory) {
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
        updateURL();
        categoryTabsEl.classList.remove("open");
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
      
      videoGrid.querySelectorAll(".cover-container").forEach(function (el) {
        el.addEventListener("click", function () {
          var url = el.getAttribute("data-url");
          var title = el.getAttribute("data-title");
          var slug = el.getAttribute("data-slug");
          openVideoPlayer(url, title, slug);
        });
      });
    }

    renderPagination(totalPages);
    updateURL();
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
    currentSearch = q;
    
    filtered = ALL_DATA.filter(function (item) {
      var matchCategory = !currentCategory || item.kategori === currentCategory;
      var matchSearch = !q || item.judul.toLowerCase().indexOf(q) > -1;
      return matchCategory && matchSearch;
    });
    render();
  }

  searchBtn.addEventListener("click", function () { currentPage = 1; applyFilter(); });
  searchBox.addEventListener("keydown", function (e) { if (e.key === "Enter") { currentPage = 1; applyFilter(); } });
  burgerBtn.addEventListener("click", function () { categoryTabsEl.classList.toggle("open"); });
  modalClose.addEventListener("click", closeVideoPlayer);
  
  videoModal.addEventListener("click", function (e) { if (e.target === videoModal) closeVideoPlayer(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && videoModal.classList.contains("active")) closeVideoPlayer(); });

  loadStateFromURL();
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
