import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "videos.json"


def load_videos(path=DATA_FILE):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return []
    return raw


def save_videos(videos, path=DATA_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


def generate_slug(judul):
    slug = re.sub(r'[^\w\s-]', '', judul.lower())
    slug = re.sub(r'[\s_]+', '-', slug).strip('-')
    slug = re.sub(r'-+', '-', slug)
    return slug


def get_unique_categories(videos):
    categories = []
    for v in videos:
        kat = str(v.get("kategori", "")).strip()
        if kat and kat not in categories:
            categories.append(kat)
    categories.sort(key=lambda x: x.lower())
    return categories


class VideoManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Manager - SeputarBokep99")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        self.videos = load_videos()
        self.editing_index = None
        
        self.build_ui()
        self.refresh_category_dropdown()
        self.refresh_video_list()
        
    def build_ui(self):
        # ===== MAIN CONTAINER =====
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ===== LEFT PANEL: FORM =====
        left_frame = ttk.Frame(main_container, width=400)
        main_container.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="FORM VIDEO", font=("Arial", 14, "bold")).pack(pady=(0, 15))
        
        form_frame = ttk.Frame(left_frame)
        form_frame.pack(fill=tk.X, padx=10)
        
        # URL
        ttk.Label(form_frame, text="URL *").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(form_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Judul
        ttk.Label(form_frame, text="Judul *").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.judul_var = tk.StringVar()
        self.judul_entry = ttk.Entry(form_frame, textvariable=self.judul_var, width=50)
        self.judul_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        self.judul_entry.bind("<KeyRelease>", self.on_judul_change)
        
        # Cover
        ttk.Label(form_frame, text="Cover").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cover_var = tk.StringVar()
        self.cover_entry = ttk.Entry(form_frame, textvariable=self.cover_var, width=50)
        self.cover_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Kategori
        ttk.Label(form_frame, text="Kategori *").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.kategori_var = tk.StringVar()
        self.kategori_combo = ttk.Combobox(form_frame, textvariable=self.kategori_var, width=47)
        self.kategori_combo.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Rasio
        ttk.Label(form_frame, text="Rasio").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.rasio_var = tk.StringVar(value="16:9")
        self.rasio_combo = ttk.Combobox(form_frame, textvariable=self.rasio_var, 
                                        values=["16:9", "3:2"], width=47, state="readonly")
        self.rasio_combo.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Durasi
        ttk.Label(form_frame, text="Durasi").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.durasi_var = tk.StringVar()
        self.durasi_entry = ttk.Entry(form_frame, textvariable=self.durasi_var, width=50)
        self.durasi_entry.grid(row=5, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Slug (auto-generate, readonly)
        ttk.Label(form_frame, text="Slug (auto)").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.slug_var = tk.StringVar()
        self.slug_entry = ttk.Entry(form_frame, textvariable=self.slug_var, width=50, state="readonly")
        self.slug_entry.grid(row=6, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        form_frame.columnconfigure(1, weight=1)
        
        # Tombol aksi
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)
        
        self.btn_tambah = ttk.Button(btn_frame, text=" Tambah", command=self.tambah_video)
        self.btn_tambah.pack(side=tk.LEFT, padx=5)
        
        self.btn_edit = ttk.Button(btn_frame, text="✏️ Update", command=self.update_video, state=tk.DISABLED)
        self.btn_edit.pack(side=tk.LEFT, padx=5)
        
        self.btn_hapus = ttk.Button(btn_frame, text="🗑️ Hapus", command=self.hapus_video, state=tk.DISABLED)
        self.btn_hapus.pack(side=tk.LEFT, padx=5)
        
        self.btn_reset = ttk.Button(btn_frame, text="🔄 Reset Form", command=self.reset_form)
        self.btn_reset.pack(side=tk.RIGHT, padx=5)
        
        # Info
        self.info_var = tk.StringVar(value="Mode: TAMBAH VIDEO BARU")
        ttk.Label(left_frame, textvariable=self.info_var, foreground="blue").pack(pady=5)
        
        # ===== RIGHT PANEL: LIST VIDEO =====
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=2)
        
        # Search list
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(search_frame, text="Cari:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_video_list())
        
        # FIX: Simpan referensi label total
        self.total_label = ttk.Label(search_frame, text=f"Total: {len(self.videos)} video")
        self.total_label.pack(side=tk.RIGHT)
        
        # Treeview
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        columns = ("judul", "kategori", "durasi", "rasio")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("judul", text="Judul")
        self.tree.heading("kategori", text="Kategori")
        self.tree.heading("durasi", text="Durasi")
        self.tree.heading("rasio", text="Rasio")
        
        self.tree.column("judul", width=300, minwidth=150)
        self.tree.column("kategori", width=150, minwidth=100)
        self.tree.column("durasi", width=80, minwidth=60)
        self.tree.column("rasio", width=60, minwidth=50)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar_y.grid(row=0, column=1, sticky=tk.NS)
        scrollbar_x.grid(row=1, column=0, sticky=tk.EW)
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())
        
        # Tombol bawah list
        bottom_btn_frame = ttk.Frame(right_frame)
        bottom_btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(bottom_btn_frame, text="✏️ Edit", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="🗑️ Hapus", command=self.hapus_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="💾 Reload Data", command=self.reload_data).pack(side=tk.RIGHT, padx=5)
        
    def refresh_category_dropdown(self):
        categories = get_unique_categories(self.videos)
        self.kategori_combo["values"] = categories
        
    def refresh_video_list(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        search = self.search_var.get().lower().strip()
        
        for idx, v in enumerate(self.videos):
            judul = str(v.get("judul", ""))
            kategori = str(v.get("kategori", ""))
            durasi = str(v.get("durasi", ""))
            rasio = str(v.get("rasio", "16:9"))
            
            if search:
                if search not in judul.lower() and search not in kategori.lower():
                    continue
            
            self.tree.insert("", tk.END, iid=idx, 
                           values=(judul, kategori, durasi, rasio))
        
        # FIX: Update total count pakai referensi langsung
        total = len(self.tree.get_children())
        self.total_label.configure(text=f"Total: {total} video")
        
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        idx = int(selection[0])
        video = self.videos[idx]
        
        self.url_var.set(str(video.get("url", "")))
        self.judul_var.set(str(video.get("judul", "")))
        self.cover_var.set(str(video.get("cover", "")))
        self.kategori_var.set(str(video.get("kategori", "")))
        self.rasio_var.set(str(video.get("rasio", "16:9")))
        self.durasi_var.set(str(video.get("durasi", "")))
        self.slug_var.set(str(video.get("slug", generate_slug(video.get("judul", "")))))
        
        self.editing_index = idx
        self.btn_tambah.configure(state=tk.DISABLED)
        self.btn_edit.configure(state=tk.NORMAL)
        self.btn_hapus.configure(state=tk.NORMAL)
        self.info_var.set(f"Mode: EDIT (Index {idx})")
        
    def on_judul_change(self, event):
        judul = self.judul_var.get().strip()
        if judul:
            self.slug_var.set(generate_slug(judul))
        
    def tambah_video(self):
        url = self.url_var.get().strip()
        judul = self.judul_var.get().strip()
        kategori = self.kategori_var.get().strip()
        
        if not url:
            messagebox.showerror("Error", "URL wajib diisi!")
            return
        if not judul:
            messagebox.showerror("Error", "Judul wajib diisi!")
            return
        if not kategori:
            messagebox.showerror("Error", "Kategori wajib diisi!")
            return
        
        video = {
            "url": url,
            "judul": judul,
            "cover": self.cover_var.get().strip(),
            "kategori": kategori,
            "rasio": self.rasio_var.get().strip() or "16:9",
            "durasi": self.durasi_var.get().strip(),
            "slug": self.slug_var.get().strip() or generate_slug(judul)
        }
        
        self.videos.append(video)
        save_videos(self.videos)
        
        self.refresh_category_dropdown()
        self.refresh_video_list()
        self.reset_form()
        
        messagebox.showinfo("Sukses", f"Video '{judul}' berhasil ditambahkan!")
        
    def update_video(self):
        if self.editing_index is None:
            messagebox.showwarning("Warning", "Pilih video dari list dulu untuk di-edit!")
            return
        
        url = self.url_var.get().strip()
        judul = self.judul_var.get().strip()
        kategori = self.kategori_var.get().strip()
        
        if not url:
            messagebox.showerror("Error", "URL wajib diisi!")
            return
        if not judul:
            messagebox.showerror("Error", "Judul wajib diisi!")
            return
        if not kategori:
            messagebox.showerror("Error", "Kategori wajib diisi!")
            return
        
        video = {
            "url": url,
            "judul": judul,
            "cover": self.cover_var.get().strip(),
            "kategori": kategori,
            "rasio": self.rasio_var.get().strip() or "16:9",
            "durasi": self.durasi_var.get().strip(),
            "slug": self.slug_var.get().strip() or generate_slug(judul)
        }
        
        self.videos[self.editing_index] = video
        save_videos(self.videos)
        
        self.refresh_category_dropdown()
        self.refresh_video_list()
        self.reset_form()
        
        messagebox.showinfo("Sukses", f"Video '{judul}' berhasil di-update!")
        
    def hapus_video(self):
        if self.editing_index is None:
            messagebox.showwarning("Warning", "Pilih video dari list dulu untuk di-hapus!")
            return
        
        video = self.videos[self.editing_index]
        judul = video.get("judul", "Unknown")
        
        if not messagebox.askyesno("Konfirmasi", f"Hapus video '{judul}'?"):
            return
        
        del self.videos[self.editing_index]
        save_videos(self.videos)
        
        self.refresh_category_dropdown()
        self.refresh_video_list()
        self.reset_form()
        
        messagebox.showinfo("Sukses", f"Video '{judul}' berhasil dihapus!")
        
    def hapus_selected(self):
        self.hapus_video()
        
    def edit_selected(self):
        selection = self.tree.selection()
        if selection:
            idx = int(selection[0])
            self.tree.selection_set(idx)
            # Trigger selection event
            self.on_tree_select(None)
        
    def reset_form(self):
        self.url_var.set("")
        self.judul_var.set("")
        self.cover_var.set("")
        self.kategori_var.set("")
        self.rasio_var.set("16:9")
        self.durasi_var.set("")
        self.slug_var.set("")
        self.editing_index = None
        
        self.btn_tambah.configure(state=tk.NORMAL)
        self.btn_edit.configure(state=tk.DISABLED)
        self.btn_hapus.configure(state=tk.DISABLED)
        self.info_var.set("Mode: TAMBAH VIDEO BARU")
        
        self.tree.selection_remove(self.tree.selection())
        
    def reload_data(self):
        self.videos = load_videos()
        self.refresh_category_dropdown()
        self.refresh_video_list()
        self.reset_form()
        messagebox.showinfo("Sukses", "Data berhasil di-reload dari videos.json!")


if __name__ == "__main__":
    root = tk.Tk()
    
    # Set theme
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except:
        pass
    
    app = VideoManagerApp(root)
    root.mainloop()
