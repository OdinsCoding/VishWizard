import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import copy 
import datetime

class QuadrantTool:
    def __init__(self, root):
        self.root = root
        self.root.title("VishWizard")
        
        # --- GLOBAL STYLE VARIABLES ---
        self.app_bg_color = "#2C2C2C"     
        self.btn_fg_color = "black"       
        self.quad_bg_color = "#ffffff"    
        self.quad_fg_color = "#333333"    
        
        self.root.configure(bg=self.app_bg_color)
        
        self.base_font_size = 9
        self.profiles = {}
        self.current_profile = "default"
        self.ui_elements = {}

        # --- THE MASTER TEMPLATE ---
        self.MASTER_TEMPLATE = {
            "Who I Am": {"Name": "", "Role": "", "Company": "", "Time in Position": ""},
            "Target": {"Name": "", "Role": "", "Phone": "", "Email": "", "Location": "", "Other": ""},
            "Pretext": {"Who I work for": "", "Why I'm calling": "", "What I need": "", "Justifications": "", "Payload": ""},
            "Goals & Flags": {"VPN": "", "IT Help Desk": "", "Software": "", "Devices": "", "Security": "", "Other": ""},
            "Call Notes": {"Notes": ""} 
        }
        
        self.profiles[self.current_profile] = copy.deepcopy(self.MASTER_TEMPLATE)
        self.setup_main_layout()
        self.refresh_ui(initial_load=True)

    def setup_main_layout(self):
        # ── Header bar — always visible at top ──────────────────────────────
        self.top_frame = tk.Frame(self.root, bg=self.app_bg_color)
        self.top_frame.pack(side="top", fill="x", padx=5, pady=5)

        # ── Middle section: quadrant canvas (scrollable) + call log canvas ──
        # They share a single right-side scrollbar column via a PanedWindow
        # so each scrolls independently without conflicting.

        # Quadrant scrollable area (top pane)
        quad_outer = tk.Frame(self.root, bg=self.app_bg_color)
        quad_outer.pack(side="top", fill="x", padx=12, pady=(5, 0))

        self.quad_canvas = tk.Canvas(quad_outer, highlightthickness=0, bg=self.app_bg_color)
        quad_sb = ttk.Scrollbar(quad_outer, orient="vertical", command=self.quad_canvas.yview)
        self.quad_frame = tk.Frame(self.quad_canvas, bg=self.app_bg_color)

        self.quad_frame.columnconfigure(0, weight=1)
        self.quad_frame.columnconfigure(1, weight=1)
        self.quad_frame.bind("<Configure>", self._update_quad_scroll)

        self.quad_canvas_win = self.quad_canvas.create_window((0, 0), window=self.quad_frame, anchor="nw")
        self.quad_canvas.configure(yscrollcommand=quad_sb.set)

        self.quad_canvas.pack(side="left", fill="both", expand=True)
        quad_sb.pack(side="right", fill="y")
        self.quad_canvas.bind("<Configure>", lambda e: (
            self.quad_canvas.itemconfig(self.quad_canvas_win, width=e.width),
            self._update_quad_scroll()
        ))

        # Call log scrollable area (bottom pane, expands to fill remaining space)
        log_outer = tk.Frame(self.root, bg=self.app_bg_color)
        log_outer.pack(side="top", fill="both", expand=True, padx=0, pady=0)

        self.log_canvas = tk.Canvas(log_outer, highlightthickness=0, bg=self.app_bg_color)
        self.log_scrollbar = ttk.Scrollbar(log_outer, orient="vertical", command=self.log_canvas.yview)
        self.scroll_content = tk.Frame(self.log_canvas, bg=self.app_bg_color)

        self.scroll_content.bind("<Configure>", lambda e: self.log_canvas.configure(
            scrollregion=self.log_canvas.bbox("all")))
        self.log_canvas_win = self.log_canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.log_canvas.configure(yscrollcommand=self.log_scrollbar.set)

        self.log_canvas.pack(side="left", fill="both", expand=True)
        self.log_scrollbar.pack(side="right", fill="y")
        self.log_canvas.bind("<Configure>", lambda e: self.log_canvas.itemconfig(
            self.log_canvas_win, width=e.width))

        # ── Mouse wheel routing ──────────────────────────────────────────────
        def _on_mousewheel(e):
            w = e.widget
            # If inside a Text widget let it handle its own scroll
            while w:
                if isinstance(w, tk.Text):
                    return
                try: w = w.master
                except Exception: break
            # Route to whichever canvas the cursor is over
            cx = self.root.winfo_pointerx() - self.root.winfo_rootx()
            cy = self.root.winfo_pointery() - self.root.winfo_rooty()
            # Check if pointer is inside quad_canvas bounds
            qx1 = self.quad_canvas.winfo_x()
            qy1 = self.quad_canvas.winfo_y()
            qx2 = qx1 + self.quad_canvas.winfo_width()
            qy2 = qy1 + self.quad_canvas.winfo_height()
            if qx1 <= cx <= qx2 and qy1 <= cy <= qy2:
                self.quad_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            else:
                self.log_canvas.yview_scroll(int(-1*(e.delta/120)), "units")

        self.root.bind_all("<MouseWheel>", _on_mousewheel)

    def _update_quad_scroll(self, _=None):
        """Resize quad_canvas height to fit content up to a max, enable scroll if overflow."""
        self.quad_canvas.update_idletasks()
        content_h = self.quad_frame.winfo_reqheight()
        # Cap visible height: show default quads (~450px), allow scroll for extras
        if self.root.state() == 'zoomed' or self.root.attributes('-fullscreen'):
            max_h = 650 # Increased for fullscreen
        else:
            max_h = 480  # Standard size
        visible_h = min(content_h, max_h)
        self.quad_canvas.configure(height=visible_h, scrollregion=self.quad_canvas.bbox("all"))

    def get_time_string(self, custom=False):
        if not custom:
            now = datetime.datetime.now()
            tz_var = getattr(self, "current_tz_var", None)
            tz = tz_var.get() if tz_var else now.strftime("%Z").strip() or "LOCAL"
            return f"{now.strftime('%I:%M %p')} {tz}"
        else:
            return f"{self.hr_var.get()}:{self.min_var.get()} {self.ampm_var.get()} {self.tz_var.get()}"

    def get_date_string(self, custom=False):
        if not custom:
            return datetime.datetime.now().strftime("%m/%d/%Y")
        else:
            mo = getattr(self, "month_var", None)
            da = getattr(self, "day_var", None)
            yr = getattr(self, "year_var", None)
            if mo and da and yr:
                return f"{mo.get()}/{da.get()}/{yr.get()}"
            return datetime.datetime.now().strftime("%m/%d/%Y")

    def add_note_entry(self, text_widget, custom=False):
        timestamp = self.get_time_string(custom)
        date_str  = self.get_date_string(custom)

        def get_val(attr, *placeholders):
            e = getattr(self, attr, None)
            v = e.get().strip() if e else ""
            return None if v in ("", *placeholders) else v

        t_name  = get_val("target_name_entry",         "First Last")
        t_pos   = get_val("target_position_entry",     "Job Title")
        t_phone = get_val("target_phone_entry",        "000-000-0000")
        c_name  = get_val("calling_as_entry",          "First Last")
        c_pos   = get_val("calling_as_position_entry", "Job Title")
        c_id    = get_val("caller_id_entry",           "000-000-0000")

        parts = []
        if t_name or t_pos:
            t_str = t_name or ""
            if t_pos: t_str += f" ({t_pos})"
            parts.append(f"Target: {t_str.strip()}")
        if t_phone:
            parts.append(f"To: {t_phone}")
        if c_name or c_pos:
            c_str = c_name or ""
            if c_pos: c_str += f" ({c_pos})"
            parts.append(f"Calling As: {c_str.strip()}")
        if c_id:
            parts.append(f"From: {c_id}")

        extra = (" | " + " | ".join(parts)) if parts else ""
        text_widget.insert(tk.END, f"\n[{date_str} {timestamp}]{extra} -> ")
        text_widget.see(tk.END)
        text_widget.focus_set()

    def _build_quad_fields(self, box, q_name):
        """Render field rows with ▲▼ move buttons. Cols: 0=arrows, 1=label, 2=text."""
        # Remove all existing field rows (row >= 1)
        for w in list(box.grid_slaves()):
            if int(w.grid_info().get("row", 0)) >= 1:
                w.grid_forget()
                w.destroy()

        self.ui_elements[q_name] = {}
        fields = self.profiles[self.current_profile][q_name]
        keys = list(fields.keys())
        n = len(keys)

        for r, fname in enumerate(keys, start=1):
            val = fields[fname]

            # ▲▼ buttons stacked in col 0
            arrow_frame = tk.Frame(box, bg=self.quad_bg_color)
            arrow_frame.grid(row=r, column=0, sticky="ns", padx=(3, 0), pady=0)

            idx = r - 1  # 0-based index of this field
            up_state   = "normal" if idx > 0     else "disabled"
            down_state = "normal" if idx < n - 1 else "disabled"

            tk.Button(arrow_frame, text="▲", font=("Arial", 6), width=1, pady=0,
                      relief="flat", bg=self.quad_bg_color, fg="#888888",
                      state=up_state,
                      command=lambda qn=q_name, fn=fname: self._move_field(qn, fn, -1)
                      ).pack(side="top")
            tk.Button(arrow_frame, text="▼", font=("Arial", 6), width=1, pady=0,
                      relief="flat", bg=self.quad_bg_color, fg="#888888",
                      state=down_state,
                      command=lambda qn=q_name, fn=fname: self._move_field(qn, fn, +1)
                      ).pack(side="top")

            # Field label col 1
            tk.Label(box, text=fname, font=("Arial", self.base_font_size),
                     bg=self.quad_bg_color, fg=self.quad_fg_color
                     ).grid(row=r, column=1, sticky="nw", padx=(2, 5), pady=2)

            # Text widget col 2
            t = tk.Text(box, height=1, wrap="word",
                        font=("Arial", self.base_font_size), undo=True, width=15)
            t.insert("1.0", val)
            t.grid(row=r, column=2, sticky="ew", padx=5, pady=2)
            t.bind("<KeyRelease>", lambda e: e.widget.after(0, self.adjust_height, e.widget))
            self.ui_elements[q_name][fname] = t

    def _move_field(self, q_name, field_name, direction):
        """Move field_name up (-1) or down (+1) within its quadrant."""
        self.sync_to_memory()
        fields = self.profiles[self.current_profile][q_name]
        keys = list(fields.keys())
        idx = keys.index(field_name)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(keys):
            return
        # Swap
        keys[idx], keys[new_idx] = keys[new_idx], keys[idx]
        self.profiles[self.current_profile][q_name] = {k: fields[k] for k in keys}

        # Find the box widget and rebuild just its fields
        for w in self.quad_frame.winfo_children():
            if isinstance(w, tk.LabelFrame) and w.cget("text").strip() == q_name:
                self._build_quad_fields(w, q_name)
                self.root.after(50, self.batch_adjust_heights)
                return

    def refresh_ui(self, initial_load=False):
        if hasattr(self, 'ui_elements') and self.ui_elements:
            self.sync_to_memory()

        for w in self.top_frame.winfo_children(): w.destroy()
        for w in self.quad_frame.winfo_children(): w.destroy()
        for w in self.scroll_content.winfo_children(): w.destroy()

        # --- Header ---
        p_row = tk.Frame(self.top_frame, bg=self.app_bg_color)
        p_row.pack(fill='x')
        tk.Button(p_row, text="New Profile", command=self.new_profile, fg=self.btn_fg_color).pack(side='left', padx=2)
        tk.Button(p_row, text="Export JSON", command=self.export_json, bg="#A7D477", fg=self.btn_fg_color).pack(side='left', padx=2)
        tk.Button(p_row, text="Import JSON", command=self.import_json, fg=self.btn_fg_color).pack(side='left', padx=2)
        tk.Label(p_row, text=f"Profile: {self.current_profile}", fg="#F3F4F4", font=("Arial", 10, "bold"), bg=self.app_bg_color).pack(side='left', padx=15)

        q_row = tk.Frame(self.top_frame, bg=self.app_bg_color)
        q_row.pack(fill='x', pady=5)

        current_data = self.profiles[self.current_profile]
        q_count = len([k for k in current_data.keys() if k != "Call Notes"])
        tk.Label(q_row, text=f"Quadrants ({q_count}/10):", font=("Arial", 9, "bold"), bg=self.app_bg_color, fg="#F3F4F4").pack(side='left', padx=5)
        tk.Button(q_row, text="+ Add Quadrant", command=self.add_q, bg="#16C47F", fg=self.btn_fg_color).pack(side='left', padx=2)
        tk.Button(q_row, text="- Delete Quadrant", command=self.del_q, bg="#F93827", fg=self.btn_fg_color).pack(side='left', padx=2)

        # --- Quadrants (fixed, always visible) ---
        self.ui_elements = {}
        standard_quads = {k: v for k, v in current_data.items() if k != "Call Notes"}

        for i, (q_name, fields) in enumerate(standard_quads.items()):
            box = tk.LabelFrame(self.quad_frame, text=f" {q_name} ", bg=self.quad_bg_color, fg=self.quad_fg_color, font=("Arial", 10, "bold"))
            box.grid(row=i//2, column=i%2, padx=10, pady=2, sticky='nsew')
            box.columnconfigure(2, weight=1)

            btns = tk.Frame(box, bg=self.quad_bg_color)
            btns.grid(row=0, column=0, columnspan=3, sticky='e', padx=(0, 8))
            tk.Button(btns, text="+", width=2, command=lambda n=q_name: self.add_f(n), fg=self.btn_fg_color).pack(side='right')
            tk.Button(btns, text="-", width=2, command=lambda n=q_name: self.del_f(n), fg=self.btn_fg_color).pack(side='right')

            self.ui_elements[q_name] = {}
            self._build_quad_fields(box, q_name)

        # --- CALL NOTES LOG (scrollable area below) ---
        self.scroll_content.columnconfigure(0, weight=1)
        if "Call Notes" in current_data:
            notes_box = tk.LabelFrame(self.scroll_content, text=" CALL LOG NOTES ", bg="#F0F0F0", fg="black", font=("Arial", 10, "bold"))
            notes_box.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
            
            # --- Call details: two stacked columns (Target | Caller) ---
            def make_entry(parent, placeholder, width=18, prefill=""):
                val = prefill.strip()
                e = tk.Entry(parent, width=width, font=("Arial", 9), fg="black" if val else "grey")
                e.insert(0, val if val else placeholder)
                e.bind("<FocusIn>",  lambda ev, p=placeholder: (ev.widget.delete(0, tk.END), ev.widget.config(fg="black")) if ev.widget.get() == p else None)
                e.bind("<FocusOut>", lambda ev, p=placeholder: (ev.widget.insert(0, p), ev.widget.config(fg="grey")) if ev.widget.get() == "" else None)
                return e

            prof = self.profiles[self.current_profile]
            who  = prof.get("Who I Am", {})
            tgt  = prof.get("Target", {})

            info_row = tk.Frame(notes_box, bg="#F0F0F0")
            info_row.pack(fill='x', padx=5, pady=(5, 0))

            # Target column
            target_col = tk.Frame(info_row, bg="#F0F0F0")
            target_col.pack(side='left', padx=(0, 20))

            tk.Label(target_col, text="Target Name:",  bg="#F0F0F0", font=("Arial", 8, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=1)
            self.target_name_entry = make_entry(target_col, "First Last", prefill=tgt.get("Name", ""))
            self.target_name_entry.grid(row=0, column=1, sticky="w", padx=(4,0), pady=1)

            tk.Label(target_col, text="Job Position:", bg="#F0F0F0", font=("Arial", 8, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=1)
            self.target_position_entry = make_entry(target_col, "Job Title", prefill=tgt.get("Role", ""))
            self.target_position_entry.grid(row=1, column=1, sticky="w", padx=(4,0), pady=1)

            tk.Label(target_col, text="Target Phone:", bg="#F0F0F0", font=("Arial", 8, "bold"), anchor="w").grid(row=2, column=0, sticky="w", pady=1)
            self.target_phone_entry = make_entry(target_col, "000-000-0000", width=14, prefill=tgt.get("Phone", ""))
            self.target_phone_entry.grid(row=2, column=1, sticky="w", padx=(4,0), pady=1)

            # Caller column
            caller_col = tk.Frame(info_row, bg="#F0F0F0")
            caller_col.pack(side='left', padx=(0, 10))

            tk.Label(caller_col, text="Calling As:",        bg="#F0F0F0", font=("Arial", 8, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=1)
            self.calling_as_entry = make_entry(caller_col, "First Last", prefill=who.get("Name", ""))
            self.calling_as_entry.grid(row=0, column=1, sticky="w", padx=(4,0), pady=1)

            tk.Label(caller_col, text="Job Position:",      bg="#F0F0F0", font=("Arial", 8, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=1)
            self.calling_as_position_entry = make_entry(caller_col, "Job Title", prefill=who.get("Role", ""))
            self.calling_as_position_entry.grid(row=1, column=1, sticky="w", padx=(4,0), pady=1)

            tk.Label(caller_col, text="Outbound Caller ID:", bg="#F0F0F0", font=("Arial", 8, "bold"), anchor="w").grid(row=2, column=0, sticky="w", pady=1)
            self.caller_id_entry = make_entry(caller_col, "000-000-0000", width=14)
            self.caller_id_entry.grid(row=2, column=1, sticky="w", padx=(4,0), pady=1)

            # Sync button
            def sync_call_details():
                self.sync_to_memory()
                p  = self.profiles[self.current_profile]
                w2 = p.get("Who I Am", {})
                t2 = p.get("Target", {})
                def set_e(widget, val, ph):
                    widget.delete(0, tk.END)
                    if val.strip():
                        widget.insert(0, val.strip()); widget.config(fg="black")
                    else:
                        widget.insert(0, ph);          widget.config(fg="grey")
                set_e(self.target_name_entry,         t2.get("Name",  ""), "First Last")
                set_e(self.target_position_entry,     t2.get("Role",  ""), "Job Title")
                set_e(self.target_phone_entry,        t2.get("Phone", ""), "000-000-0000")
                set_e(self.calling_as_entry,          w2.get("Name",  ""), "First Last")
                set_e(self.calling_as_position_entry, w2.get("Role",  ""), "Job Title")

            sync_row = tk.Frame(notes_box, bg="#F0F0F0")
            sync_row.pack(fill='x', padx=5, pady=(2, 0))
            tk.Button(sync_row, text="↺ Sync from Quadrants", font=("Arial", 8, "bold"),
                      bg="#D0D0D0", fg="black", command=sync_call_details).pack(side='left')

            ctrls = tk.Frame(notes_box, bg="#F0F0F0")
            ctrls.pack(fill='x', padx=5, pady=5)

            tk.Button(ctrls, text="Add Current Time Entry", bg="#16C47F", fg="white", font=("Arial", 8, "bold"),
                      command=lambda: self.add_note_entry(notes_text, custom=False)).pack(side='left', padx=5)

            self.current_tz_var = tk.StringVar(value="MDT")
            current_tz_m = ttk.Combobox(ctrls, textvariable=self.current_tz_var, width=5,
                                        values=("MDT","MST","CDT","CST","EDT","EST","PDT","PST"), state="readonly")
            current_tz_m.pack(side='left', padx=(0, 5))

            tk.Label(ctrls, text="| Custom Date:", bg="#F0F0F0").pack(side='left', padx=5)

            now = datetime.datetime.now()
            self.month_var = tk.StringVar(value=now.strftime("%m"))
            month_m = ttk.Combobox(ctrls, textvariable=self.month_var, width=3,
                                   values=[f"{i:02d}" for i in range(1, 13)], state="readonly")
            month_m.pack(side='left', padx=1)
            tk.Label(ctrls, text="/", bg="#F0F0F0").pack(side='left')
            self.day_var = tk.StringVar(value=now.strftime("%d"))
            day_m = ttk.Combobox(ctrls, textvariable=self.day_var, width=3,
                                 values=[f"{i:02d}" for i in range(1, 32)], state="readonly")
            day_m.pack(side='left', padx=1)
            tk.Label(ctrls, text="/", bg="#F0F0F0").pack(side='left')
            self.year_var = tk.StringVar(value=now.strftime("%Y"))
            year_m = ttk.Combobox(ctrls, textvariable=self.year_var, width=5,
                                  values=[str(now.year + i) for i in range(-2, 3)], state="readonly")
            year_m.pack(side='left', padx=1)

            tk.Label(ctrls, text="| Custom Time:", bg="#F0F0F0").pack(side='left', padx=5)

            now = datetime.datetime.now()
            self.hr_var = tk.StringVar(value=now.strftime("%I"))
            hr_m = ttk.Combobox(ctrls, textvariable=self.hr_var, width=3, values=[f"{i:02d}" for i in range(1, 13)], state="readonly")
            hr_m.pack(side='left', padx=1)
            tk.Label(ctrls, text=":", bg="#F0F0F0").pack(side='left')
            self.min_var = tk.StringVar(value=now.strftime("%M"))
            min_m = ttk.Combobox(ctrls, textvariable=self.min_var, width=3, values=[f"{i:02d}" for i in range(0, 60)], state="readonly")
            min_m.pack(side='left', padx=1)
            self.ampm_var = tk.StringVar(value=now.strftime("%p"))
            ap_m = ttk.Combobox(ctrls, textvariable=self.ampm_var, width=4, values=("AM","PM"), state="readonly")
            ap_m.pack(side='left', padx=2)
            self.tz_var = tk.StringVar(value="MDT")
            tz_m = ttk.Combobox(ctrls, textvariable=self.tz_var, width=5, values=("MDT","MST","CDT","CST","EDT","EST","PDT","PST"), state="readonly")
            tz_m.pack(side='left', padx=2)

            tk.Button(ctrls, text="Add Custom Entry", bg="#00A8E8", fg="white", font=("Arial", 8, "bold"),
                      command=lambda: self.add_note_entry(notes_text, custom=True)).pack(side='left', padx=5)

            notes_text = tk.Text(notes_box, height=12, wrap="word", font=("Arial", 10), undo=True)
            notes_text.insert("1.0", current_data["Call Notes"].get("Notes", ""))
            notes_text.pack(fill='both', expand=True, padx=5, pady=5)
            self.ui_elements["Call Notes"] = {"Notes": notes_text}

        self.root.after(100, self.batch_adjust_heights)
        self.root.after(150, self._update_quad_scroll)
        if initial_load: self.root.geometry("1000x900")

    def sync_to_memory(self):
        for q_name, fields in self.ui_elements.items():
            if q_name in self.profiles[self.current_profile]:
                for f_name, widget in fields.items():
                    self.profiles[self.current_profile][q_name][f_name] = widget.get("1.0", "end-1c")

    def batch_adjust_heights(self):
        for q in self.ui_elements.values():
            for t in q.values():
                if isinstance(t, tk.Text) and t.winfo_height() < 50:
                    self.adjust_height(t)

    def adjust_height(self, widget):
        try:
            if widget.winfo_width() > 1:
                lines = int(widget.tk.call(widget._w, "count", "-displaylines", "1.0", "end-1c"))
                widget.configure(height=min(15, max(1, lines)))
                widget.yview_moveto(0.0)
        except: pass

    def new_profile(self):
        n = simpledialog.askstring("New Profile", "Enter Profile Name:")
        if n:
            self.profiles[n] = copy.deepcopy(self.MASTER_TEMPLATE)
            self.current_profile = n
            self.ui_elements = {}
            self.refresh_ui()

    def export_json(self):
        self.sync_to_memory()
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file:
            with open(file, "w") as f:
                json.dump({"active_profile": self.current_profile, "profile_data": self.profiles[self.current_profile]}, f, indent=2)

    def import_json(self):
        file = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if file:
            with open(file, "r") as f:
                data = json.load(f)
            self.profiles[data["active_profile"]] = data["profile_data"]
            self.current_profile = data["active_profile"]
            self.ui_elements = {}
            self.refresh_ui()

    def add_q(self):
        if len(self.profiles[self.current_profile]) >= 11: return

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Quadrant")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        # Center over root
        self.root.update_idletasks()
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        dialog.update_idletasks()
        dw, dh = 280, 140
        dialog.geometry(f"{dw}x{dh}+{rx + (rw - dw)//2}+{ry + (rh - dh)//2}")

        tk.Label(dialog, text="Quadrant Name:", anchor="w").pack(fill="x", padx=15, pady=(15, 2))
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(padx=15)
        name_entry.focus_set()

        tk.Label(dialog, text="First Section Name:", anchor="w").pack(fill="x", padx=15, pady=(8, 2))
        field_entry = tk.Entry(dialog, width=30)
        field_entry.pack(padx=15)

        result = {}

        def on_ok(e=None):
            n = name_entry.get().strip()
            f = field_entry.get().strip()
            if n and f:
                result["name"] = n
                result["field"] = f
            dialog.destroy()

        def on_cancel(e=None):
            dialog.destroy()

        btn_row = tk.Frame(dialog)
        btn_row.pack(pady=10)
        tk.Button(btn_row, text="OK", width=8, command=on_ok).pack(side="left", padx=5)
        tk.Button(btn_row, text="Cancel", width=8, command=on_cancel).pack(side="left", padx=5)

        name_entry.bind("<Return>", lambda e: field_entry.focus_set())
        field_entry.bind("<Return>", on_ok)
        dialog.bind("<Escape>", on_cancel)

        dialog.wait_window()

        if "name" in result:
            self.sync_to_memory()
            self.profiles[self.current_profile][result["name"]] = {result["field"]: ""}
            self.refresh_ui()

    def del_q(self):
        n = simpledialog.askstring("Delete", "Exact Quadrant Name:")
        if n in self.profiles[self.current_profile] and n != "Call Notes":
            self.sync_to_memory()
            del self.profiles[self.current_profile][n]
            self.refresh_ui()

    def add_f(self, q_name):
        n = simpledialog.askstring("Field", "Field Name:")
        if n:
            self.sync_to_memory()
            self.profiles[self.current_profile][q_name][n] = ""
            self.refresh_ui()

    def del_f(self, q_name):
        fields = self.profiles[self.current_profile][q_name]
        f_list = list(fields.keys())
        if len(f_list) <= 1:
            messagebox.showinfo("Can't Delete", "A quadrant must have at least one field.")
            return
        n = simpledialog.askstring("Remove Field", f"Field to remove from '{q_name}':")
        if not n or n not in fields:
            return
        self.sync_to_memory()
        del self.profiles[self.current_profile][q_name][n]
        self.ui_elements = {}
        self.refresh_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuadrantTool(root)
    root.mainloop()