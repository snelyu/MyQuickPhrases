import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import pyperclip
import json
import os
import webbrowser
import requests

# --- 설정 및 디자인 상수 ---
CURRENT_VERSION = "1.3.0"  # 버전 업데이트
UPDATE_URL = "https://raw.githubusercontent.com/snelyu/MyQuickPhrases/main/version.json"

COLOR_BG = "#F8FAFC"
COLOR_HEADER_BG = "#F1F3F4"
COLOR_CARD_BG = "#FFFFFF"
COLOR_HOVER = "#F1F5F9"
COLOR_SELECTED = "#E0F2FE"
COLOR_DRAG = "#CBD5E1"
COLOR_TEXT_MAIN = "#1F2937"
COLOR_TEXT_NOTE = "#6B7280"
COLOR_ACCENT = "#1A73E8"

FONT_INPUT = ("Malgun Gothic", 10)
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_CONTENT = ("Consolas", 10)
FONT_NOTE = ("Malgun Gothic", 9)

# --- 다국어 데이터 사전 ---
LANG_DATA = {
    "KO": {
        "header_title": "📋 My Quick Phrases",
        "always_on_top": "📌 항상 위",
        "btn_import": "📂 불러오기",
        "btn_export": "💾 저장",
        "btn_add": "+ 문장 추가",
        "footer": "Copyright © 2026 inspeep. All rights reserved. 문의: admin@inspeep.com",
        "copy_done": "✅ 복사 완료!",
        "dlg_add": "새 문장 추가",
        "dlg_edit": "문장 수정",
        "dlg_note": "주석 (설명 - 생략 가능):",
        "dlg_content": "복사할 문장 본문:",
        "dlg_save": "저장",
        "dlg_cancel": "취소",
        "msg_warn_title": "입력 확인",
        "msg_warn_text": "본문 내용은 반드시 입력해야 합니다.",
        "msg_export_ok": "파일이 저장되었습니다.",
        "msg_import_err": "파일을 불러오지 못했습니다.",
        "msg_del_title": "삭제 확인",
        "msg_del_text": "이 문장을 삭제할까요?",
        "msg_update_title": "업데이트 알림",
        "msg_update_text": "새로운 버전(v{})이 출시되었습니다.\n다운로드 페이지로 이동할까요?"
    },
    "EN": {
        "header_title": "📋 My Quick Phrases",
        "always_on_top": "📌 Always on Top",
        "btn_import": "📂 Import",
        "btn_export": "💾 Export",
        "btn_add": "+ Add Phrase",
        "footer": "Copyright © 2026 inspeep. All rights reserved. Contact: admin@inspeep.com",
        "copy_done": "✅ Copied!",
        "dlg_add": "Add New Phrase",
        "dlg_edit": "Edit Phrase",
        "dlg_note": "Note (Description - Optional):",
        "dlg_content": "Content to Copy:",
        "dlg_save": "Save",
        "dlg_cancel": "Cancel",
        "msg_warn_title": "Input Required",
        "msg_warn_text": "Content cannot be empty.",
        "msg_export_ok": "File saved successfully.",
        "msg_import_err": "Failed to import file.",
        "msg_del_title": "Confirm Delete",
        "msg_del_text": "Delete this phrase?",
        "msg_update_title": "Update Available",
        "msg_update_text": "A new version (v{}) is available.\nGo to the download page?"
    }
}

class PhraseInputDialog(tk.Toplevel):
    def __init__(self, parent, lang_key, mode="add", initial_content="", initial_note=""):
        super().__init__(parent)
        self.lang = LANG_DATA[lang_key]
        self.title(self.lang["dlg_add"] if mode == "add" else self.lang["dlg_edit"])
        self.geometry("450x520")
        self.configure(bg=COLOR_BG)
        self.result = None
        
        container = tk.Frame(self, bg=COLOR_BG, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(container, text=self.lang["dlg_note"], font=(FONT_INPUT[0], 10, "bold"), 
                 bg=COLOR_BG, fg=COLOR_TEXT_NOTE).pack(anchor="w")
        self.note_entry = tk.Entry(container, font=FONT_INPUT, bd=1, relief="solid")
        self.note_entry.insert(0, initial_note)
        self.note_entry.pack(fill="x", pady=(5, 15))

        tk.Label(container, text=self.lang["dlg_content"], font=(FONT_INPUT[0], 10, "bold"), 
                 bg=COLOR_BG, fg=COLOR_TEXT_MAIN).pack(anchor="w")
        
        btn_frame = tk.Frame(container, bg=COLOR_BG)
        btn_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text=self.lang["dlg_cancel"], width=10, command=self.destroy).pack(side="right")
        tk.Button(btn_frame, text=self.lang["dlg_save"], width=10, bg=COLOR_ACCENT, fg="white", 
                  font=(FONT_INPUT[0], 10, "bold"), command=self.save, relief="flat").pack(side="right", padx=10)

        self.txt_area = scrolledtext.ScrolledText(container, font=FONT_INPUT, bd=1, relief="solid")
        self.txt_area.insert("1.0", initial_content)
        self.txt_area.pack(side="top", fill="both", expand=True, pady=(5, 0))

    def save(self):
        content = self.txt_area.get("1.0", "end-1c").strip()
        note = self.note_entry.get().strip()
        if content:
            self.result = {"content": content, "note": note}
            self.destroy()
        else: 
            messagebox.showwarning(self.lang["msg_warn_title"], self.lang["msg_warn_text"])

class MyQuickPhrasesApp:
    def __init__(self, root):
        self.root = root
        self.lang_mode = "KO"  # 기본 언어 설정
        self.update_window_title()
        self.root.geometry("600x780")
        self.root.configure(bg=COLOR_BG)
        
        self.file_path = "snippets_v2.json"
        self.snippets = self.load_initial_data()
        self.press_job = None
        self.is_dragging = False
        self.drag_index = None
        self.selected_index = None 
        
        self.setup_ui()
        self.root.bind("<ButtonRelease-1>", self.on_release)
        self.root.after(1000, self.check_update)

    def update_window_title(self):
        self.root.title(f"Quick Copy Snippets v{CURRENT_VERSION}")

    def setup_ui(self):
        lang = LANG_DATA[self.lang_mode]
        
        # 헤더
        self.header = tk.Frame(self.root, bg=COLOR_HEADER_BG, pady=10, padx=15)
        self.header.pack(fill="x")
        
        self.title_lbl = tk.Label(self.header, text=lang["header_title"], font=FONT_TITLE, bg=COLOR_HEADER_BG, fg=COLOR_TEXT_MAIN)
        self.title_lbl.pack(side="left")
        
        # 버튼 컨테이너
        self.btn_container = tk.Frame(self.header, bg=COLOR_HEADER_BG)
        self.btn_container.pack(side="right")

        # 언어 전환 버튼
        self.lang_btn = tk.Label(self.btn_container, text="KO / EN", font=("Malgun Gothic", 9, "bold"),
                                 fg=COLOR_TEXT_MAIN, bg="#E2E8F0", cursor="hand2", padx=10, pady=2)
        self.lang_btn.pack(side="left", padx=5)
        self.lang_btn.bind("<Button-1>", lambda e: self.toggle_language())

        # 항상 위
        self.always_on_top_var = tk.BooleanVar(value=self.root.attributes("-topmost"))
        self.top_check = tk.Checkbutton(self.btn_container, text=lang["always_on_top"], variable=self.always_on_top_var, 
                                       command=self.toggle_always_on_top, font=("Malgun Gothic", 9),
                                       bg=COLOR_HEADER_BG, activebackground=COLOR_HEADER_BG, selectcolor="white", bd=0)
        self.top_check.pack(side="left", padx=5)

        # 불러오기 / 저장 / 추가 버튼
        self.btn_import_lbl = tk.Label(self.btn_container, text=lang["btn_import"], font=("Malgun Gothic", 9, "bold"), fg=COLOR_TEXT_MAIN, bg=COLOR_HEADER_BG, cursor="hand2", padx=8)
        self.btn_import_lbl.pack(side="left")
        self.btn_import_lbl.bind("<Button-1>", lambda e: self.import_data())

        self.btn_export_lbl = tk.Label(self.btn_container, text=lang["btn_export"], font=("Malgun Gothic", 9, "bold"), fg=COLOR_TEXT_MAIN, bg=COLOR_HEADER_BG, cursor="hand2", padx=8)
        self.btn_export_lbl.pack(side="left")
        self.btn_export_lbl.bind("<Button-1>", lambda e: self.export_data())

        self.btn_add_lbl = tk.Label(self.btn_container, text=lang["btn_add"], font=("Malgun Gothic", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_HEADER_BG, cursor="hand2", padx=8)
        self.btn_add_lbl.pack(side="left")
        self.btn_add_lbl.bind("<Button-1>", lambda e: self.add_phrase())

        # 푸터 (저작권)
        self.copyright_lbl = tk.Label(self.root, text=lang["footer"], font=("Malgun Gothic", 8), bg=COLOR_BG, fg=COLOR_TEXT_NOTE, pady=5)
        self.copyright_lbl.pack(side="bottom")

        # 메인 리스트 영역
        self.canvas = tk.Canvas(self.root, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=560)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.scrollbar.pack(side="right", fill="y")
        
        self.refresh_list()

    def toggle_language(self):
        """언어를 전환하고 UI를 새로고침합니다."""
        self.lang_mode = "EN" if self.lang_mode == "KO" else "KO"
        # 기존 UI 요소 제거 후 재생성
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()

    def check_update(self):
        lang = LANG_DATA[self.lang_mode]
        try:
            response = requests.get(UPDATE_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("version")
                download_url = data.get("url")
                if download_url:
                    download_url = download_url.replace(".git/", "/").replace(".git", "")

                if latest_version > CURRENT_VERSION:
                    if messagebox.askyesno(lang["msg_update_title"], lang["msg_update_text"].format(latest_version)):
                        webbrowser.open(download_url)
        except: pass 

    def _on_mousewheel(self, event): self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def toggle_always_on_top(self): self.root.attributes("-topmost", self.always_on_top_var.get())
    
    def load_initial_data(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f: return json.load(f)
            except: return []
        return []

    def auto_save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f: 
            json.dump(self.snippets, f, ensure_ascii=False, indent=4)

    def export_data(self):
        lang = LANG_DATA[self.lang_mode]
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            with open(path, 'w', encoding='utf-8') as f: json.dump(self.snippets, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("OK", lang["msg_export_ok"])

    def import_data(self):
        lang = LANG_DATA[self.lang_mode]
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f: self.snippets = json.load(f)
                self.selected_index = None
                self.auto_save(); self.refresh_list()
            except: messagebox.showerror("Error", lang["msg_import_err"])

    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        for idx, item in enumerate(self.snippets): self.create_phrase_card(idx, item)

    def create_phrase_card(self, idx, item):
        is_drag = (idx == self.drag_index and self.is_dragging)
        is_sel = (idx == self.selected_index)
        bg_color = COLOR_DRAG if is_drag else (COLOR_SELECTED if is_sel else COLOR_CARD_BG)
        card = tk.Frame(self.scrollable_frame, bg=bg_color, pady=12, padx=15)
        card.pack(fill="x", pady=4, padx=8)
        card.bind("<ButtonPress-1>", lambda e, i=idx: self.on_press(e, i))
        card.bind("<B1-Motion>", self.on_motion)
        
        if item.get('note'):
            note_lbl = tk.Label(card, text=f"💡 {item['note']}", font=FONT_NOTE, bg=bg_color, fg=COLOR_TEXT_NOTE, anchor="w")
            note_lbl.pack(fill="x")
            note_lbl.bind("<Button-1>", lambda e: card.event_generate("<Button-1>"))
        
        content_lbl = tk.Label(card, text=item['content'], font=FONT_CONTENT, bg=bg_color, fg=COLOR_TEXT_MAIN, justify="left", wraplength=460, anchor="w")
        content_lbl.pack(fill="x", pady=(2, 0))
        content_lbl.bind("<Button-1>", lambda e: card.event_generate("<Button-1>"))
        
        btn_frame = tk.Frame(card, bg=bg_color)
        btn_frame.pack(anchor="e")
        tk.Button(btn_frame, text="✎", font=("Arial", 8), command=lambda i=idx: self.edit_phrase(i), relief="flat", bg=bg_color).pack(side="left")
        tk.Button(btn_frame, text="✕", font=("Arial", 8), command=lambda i=idx: self.delete_phrase(i), relief="flat", bg=bg_color, fg="#EF4444").pack(side="left", padx=5)
        
        def on_enter(e):
            if not self.is_dragging and idx != self.selected_index:
                card.config(bg=COLOR_HOVER)
                for w in card.winfo_children(): w.config(bg=COLOR_HOVER)
        def on_leave(e):
            if not self.is_dragging and idx != self.selected_index:
                card.config(bg=COLOR_CARD_BG)
                for w in card.winfo_children(): w.config(bg=COLOR_CARD_BG)
        card.bind("<Enter>", on_enter); card.bind("<Leave>", on_leave)

    def on_press(self, event, index):
        self.drag_index = index
        if self.press_job: self.root.after_cancel(self.press_job)
        self.press_job = self.root.after(1500, self.start_drag)

    def start_drag(self):
        self.is_dragging = True
        self.root.config(cursor="fleur"); self.refresh_list()

    def on_motion(self, event):
        if not self.is_dragging: return
        target_idx = self.find_drop_index(event.y_root)
        if target_idx is not None and target_idx != self.drag_index:
            item = self.snippets.pop(self.drag_index)
            self.snippets.insert(target_idx, item)
            if self.drag_index == self.selected_index: self.selected_index = target_idx
            elif self.selected_index is not None:
                if self.drag_index < self.selected_index <= target_idx: self.selected_index -= 1
                elif target_idx <= self.selected_index < self.drag_index: self.selected_index += 1
            self.drag_index = target_idx
            self.refresh_list()

    def on_release(self, event):
        lang = LANG_DATA[self.lang_mode]
        if self.press_job: self.root.after_cancel(self.press_job); self.press_job = None
        self.root.config(cursor="")
        if self.is_dragging: self.is_dragging = False; self.auto_save()
        else:
            if self.drag_index is not None:
                self.selected_index = self.drag_index
                self.copy_to_clipboard(self.snippets[self.drag_index]['content'])
        self.drag_index = None; self.refresh_list()

    def find_drop_index(self, y_root):
        for idx, widget in enumerate(self.scrollable_frame.winfo_children()):
            w_y = widget.winfo_rooty()
            if w_y <= y_root <= w_y + widget.winfo_height(): return idx
        return None

    def copy_to_clipboard(self, content):
        lang = LANG_DATA[self.lang_mode]
        pyperclip.copy(content); self.root.title(lang["copy_done"])
        self.root.after(800, lambda: self.update_window_title())

    def add_phrase(self):
        dialog = PhraseInputDialog(self.root, self.lang_mode, mode="add")
        self.root.wait_window(dialog)
        if dialog.result: self.snippets.append(dialog.result); self.auto_save(); self.refresh_list()

    def edit_phrase(self, index):
        curr = self.snippets[index]
        dialog = PhraseInputDialog(self.root, self.lang_mode, mode="edit", initial_content=curr['content'], initial_note=curr.get('note', ''))
        self.root.wait_window(dialog)
        if dialog.result: self.snippets[index] = dialog.result; self.auto_save(); self.refresh_list()

    def delete_phrase(self, index):
        lang = LANG_DATA[self.lang_mode]
        if messagebox.askyesno(lang["msg_del_title"], lang["msg_del_text"]):
            if self.selected_index == index: self.selected_index = None
            del self.snippets[index]; self.auto_save(); self.refresh_list()

if __name__ == "__main__":
    root = tk.Tk(); app = MyQuickPhrasesApp(root); root.mainloop()