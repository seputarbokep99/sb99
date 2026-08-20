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

  /* Header */
  header {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
  }

  h1 { 
    font-size: 24px; 
    font-weight: 800; 
    letter-spacing: -0.5px;
    color: var(--text);
    cursor: pointer;
    display: inline-block;
    text-decoration: none;
  }
  h1:hover { opacity: 0.8; }

  /* Search Bar */
  .search-container {
    width: 100%;
    max-width: 1000px;
    margin: 20px auto;
    display: flex;
    gap: 0;
    padding: 0 24px;
  }
  #searchBox {
    flex: 1;
    padding: 14px 20px;
    border: 2px solid var(--border);
    border-right: none;
    border-radius: 0;
    font-size: 16px;
    background: var(--input-bg);
    color: var(--text);
    outline: none;
  }
  #searchBox:focus { border-color: var(--accent); border-right-color: var(--accent); }
  
  #searchBtn {
    padding: 14px 28px;
    border: 2px solid var(--accent);
    border-radius: 0;
    background: var(--accent);
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }
  #searchBtn:hover { opacity: 0.9; }

  /* Category Wrapper */
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

  /* Burger Button - Hidden di desktop */
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

  /* Main Grid - Padding konsisten semua sisi */
  main {
    flex: 1;
    width: 100%;
    padding: 24px; /* Sama atas, bawah, kiri, kanan */
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

  /* Responsive - Mobile & Tablet */
  @media (max-width: 768px) {
    .video-grid { 
      grid-template-columns: 1fr; /* 1 card per baris seperti YT */
    }
    
    header { padding: 12px 16px; }
    .search-container { padding: 0 16px; margin: 16px auto; }
    .category-wrapper { 
      padding: 12px 16px; 
      flex-direction: column;
      align-items: stretch;
    }
    main { padding: 16px; } /* Konsisten dengan header */
    .card-info { padding: 12px; }
    .video-title { font-size: 14px; }
    
    /* Burger button muncul di mobile */
    .burger-btn { display: block; margin-bottom: 0; }
    
    /* Category tabs jadi dropdown di mobile */
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
  }
</style>
</head>
<body>

<header>
  <h1 onclick="location.reload()" title="Klik untuk kembali ke beranda">__SITE_TITLE__</h1>
</header>

<div class="search-container">
  <input type="text" id="searchBox" placeholder="Cari video...">
  <button id="searchBtn">Cari</button>
</div>

<div class="category-wrapper">
  <button class="burger-btn" id="burgerBtn"> Kategori</button>
  <div class="category-tabs" id="categoryTabs"></div>
</div>

<main>
  <div class="video-grid" id="videoGrid"></div>
  <div id="noResult" class="no-result" style="display:none;">Tidak ada video yang cocok.</div>
</main>

<footer>
  Copyright @ team 2026
</footer>

<script type="application/json" id="video-data">__DATA_JSON__</script>
<script>
(function () {
  var ALL_DATA = JSON.parse(document.getElementById("video-data").textContent);
  var currentCategory = null;
  var filtered = [];

  var videoGrid = document.getElementById("videoGrid");
  var noResult = document.getElementById("noResult");
  var searchBox = document.getElementById("searchBox");
  var searchBtn = document.getElementById("searchBtn");
  var categoryTabsEl = document.getElementById("categoryTabs");
  var burgerBtn = document.getElementById("burgerBtn");

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function createCard(item) {
    var ratioClass = item.rasio === "3:2" ? "ratio-3-2" : "ratio-16-9";
    var coverHtml = item.cover 
      ? '<img src="' + escapeHtml(item.cover) + '" alt="cover" loading="lazy" class="cover-img" onerror="this.onerror=null;this.classList.add(\'broken\');this.alt=\'Error\';">'
      : '<div class="no-cover">No Cover</div>';
    
    var coverLink = '<a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener noreferrer" class="cover-container ' + ratioClass + '">' + coverHtml + '</a>';

    return '<div class="video-card">' +
      coverLink +
      '<div class="card-info"><div class="video-title">' + escapeHtml(item.judul) + '</div></div>' +
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

    if (!currentCategory && categories.length > 0) currentCategory = categories[0];

    categoryTabsEl.innerHTML = categories.map(function (cat) {
      var activeClass = cat === currentCategory ? " active" : "";
      return '<span class="tab' + activeClass + '" data-cat="' + escapeHtml(cat) + '">' + escapeHtml(cat) + '</span>';
    }).join("");

    categoryTabsEl.querySelectorAll(".tab").forEach(function (el) {
      el.addEventListener("click", function () {
        currentCategory = el.getAttribute("data-cat");
        applyFilter();
        renderCategoryTabs();
        // Tutup menu burger setelah pilih kategori (mobile)
        categoryTabsEl.classList.remove("open");
      });
    });
  }

  function render() {
    if (filtered.length === 0) {
      videoGrid.innerHTML = "";
      noResult.style.display = "block";
    } else {
      noResult.style.display = "none";
      videoGrid.innerHTML = filtered.map(createCard).join("");
    }
  }

  function applyFilter() {
    var q = searchBox.value.trim().toLowerCase();
    filtered = ALL_DATA.filter(function (item) {
      var matchCategory = !currentCategory || item.kategori === currentCategory;
      // CARI HANYA BERDASARKAN JUDUL
      var matchSearch = !q || item.judul.toLowerCase().indexOf(q) > -1;
      return matchCategory && matchSearch;
    });
    render();
  }

  // Tombol Cari
  searchBtn.addEventListener("click", function () {
    applyFilter();
  });

  searchBox.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      applyFilter();
    }
  });

  // Burger Menu Toggle (mobile)
  burgerBtn.addEventListener("click", function () {
    categoryTabsEl.classList.toggle("open");
  });

  // Init
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
