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
            "Pretext": {"Who I work for": "", "Why I'm calling": "", "What I need": "", "Justifications": ""},
            "Goals & Flags": {"VPN": "", "IT Help Desk": "", "Software": "", "Devices": "", "Security": "", "Other": ""},
            "Call Notes": {"Notes": ""} 
        }
        
        self.profiles[self.current_profile] = copy.deepcopy(self.MASTER_TEMPLATE)
        self.setup_main_layout()
        self.refresh_ui(initial_load=True)

    def setup_main_layout(self):
        self.top_frame = tk.Frame(self.root, bg=self.app_bg_color)
        self.top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg=self.app_bg_color)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas, bg=self.app_bg_color)

        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_win = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_win, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

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
        date_str = self.get_date_string(custom)
        caller = getattr(self, "caller_id_entry", None)
        target = getattr(self, "target_phone_entry", None)
        caller_val = caller.get() if caller else ""
        target_val = target.get() if target else ""
        if caller_val in ("", "000-000-0000"): caller_val = None
        if target_val in ("", "000-000-0000"): target_val = None
        phone_str = ""
        if caller_val or target_val:
            parts = []
            if caller_val: parts.append(f"From: {caller_val}")
            if target_val: parts.append(f"To: {target_val}")
            phone_str = " | " + " | ".join(parts)
        name_entry = getattr(self, "target_name_entry", None)
        name_val = name_entry.get() if name_entry else ""
        if name_val in ("", "First Last"): name_val = None
        name_str = f" | Target: {name_val}" if name_val else ""
        text_widget.insert(tk.END, f"\n[{date_str} {timestamp}]{name_str}{phone_str} -> ")
        text_widget.see(tk.END)
        text_widget.focus_set()

    def refresh_ui(self, initial_load=False):
        if hasattr(self, 'ui_elements') and self.ui_elements:
            self.sync_to_memory()

        for w in self.top_frame.winfo_children(): w.destroy()
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

        self.scroll_content.columnconfigure(0, weight=1)
        self.scroll_content.columnconfigure(1, weight=1)

        self.ui_elements = {}
        standard_quads = {k: v for k, v in current_data.items() if k != "Call Notes"}

        for i, (q_name, fields) in enumerate(standard_quads.items()):
            box = tk.LabelFrame(self.scroll_content, text=f" {q_name} ", bg=self.quad_bg_color, fg=self.quad_fg_color, font=("Arial", 10, "bold"))
            box.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')
            box.columnconfigure(1, weight=1)

            btns = tk.Frame(box, bg=self.quad_bg_color)
            btns.grid(row=0, column=0, columnspan=2, sticky='e', padx=(0, 8))
            tk.Button(btns, text="+", width=2, command=lambda n=q_name: self.add_f(n), fg=self.btn_fg_color).pack(side='right')
            tk.Button(btns, text="-", width=2, command=lambda n=q_name: self.del_f(n), fg=self.btn_fg_color).pack(side='right')

            self.ui_elements[q_name] = {}
            for r, (fname, val) in enumerate(fields.items(), start=1):
                tk.Label(box, text=fname, font=("Arial", self.base_font_size), bg=self.quad_bg_color, fg=self.quad_fg_color).grid(row=r, column=0, sticky='nw', padx=5, pady=2)
                t = tk.Text(box, height=1, wrap="word", font=("Arial", self.base_font_size), undo=True, width=15)
                t.insert("1.0", val)
                t.grid(row=r, column=1, sticky='ew', padx=5, pady=2)
                t.bind("<KeyRelease>", lambda e: e.widget.after(0, self.adjust_height, e.widget))
                self.ui_elements[q_name][fname] = t

        # --- CALL NOTES LOG ---
        if "Call Notes" in current_data:
            notes_box = tk.LabelFrame(self.scroll_content, text=" CALL LOG NOTES ", bg="#F0F0F0", fg="black", font=("Arial", 10, "bold"))
            notes_box.grid(row=(len(standard_quads)//2)+1, column=0, columnspan=2, padx=10, pady=20, sticky='nsew')
            
            # --- Phone number row ---
            phone_row = tk.Frame(notes_box, bg="#F0F0F0")
            phone_row.pack(fill='x', padx=5, pady=(5, 0))

            tk.Label(phone_row, text="Target Name:", bg="#F0F0F0", font=("Arial", 8, "bold")).pack(side='left', padx=(0, 3))
            self.target_name_entry = tk.Entry(phone_row, width=18, font=("Arial", 9), fg="grey")
            self.target_name_entry.insert(0, "First Last")
            self.target_name_entry.pack(side='left', padx=(0, 10))
            self.target_name_entry.bind("<FocusIn>", lambda e: (e.widget.delete(0, tk.END), e.widget.config(fg="black")) if e.widget.get() == "First Last" else None)
            self.target_name_entry.bind("<FocusOut>", lambda e: (e.widget.insert(0, "First Last"), e.widget.config(fg="grey")) if e.widget.get() == "" else None)

            tk.Label(phone_row, text="Outbound Caller ID:", bg="#F0F0F0", font=("Arial", 8, "bold")).pack(side='left', padx=(0, 3))
            self.caller_id_entry = tk.Entry(phone_row, width=14, font=("Arial", 9), fg="grey")
            self.caller_id_entry.insert(0, "000-000-0000")
            self.caller_id_entry.pack(side='left', padx=(0, 10))
            self.caller_id_entry.bind("<FocusIn>", lambda e: (e.widget.delete(0, tk.END), e.widget.config(fg="black")) if e.widget.get() == "000-000-0000" else None)
            self.caller_id_entry.bind("<FocusOut>", lambda e: (e.widget.insert(0, "000-000-0000"), e.widget.config(fg="grey")) if e.widget.get() == "" else None)

            tk.Label(phone_row, text="Target Phone:", bg="#F0F0F0", font=("Arial", 8, "bold")).pack(side='left', padx=(0, 3))
            self.target_phone_entry = tk.Entry(phone_row, width=14, font=("Arial", 9), fg="grey")
            self.target_phone_entry.insert(0, "000-000-0000")
            self.target_phone_entry.pack(side='left', padx=(0, 10))
            self.target_phone_entry.bind("<FocusIn>", lambda e: (e.widget.delete(0, tk.END), e.widget.config(fg="black")) if e.widget.get() == "000-000-0000" else None)
            self.target_phone_entry.bind("<FocusOut>", lambda e: (e.widget.insert(0, "000-000-0000"), e.widget.config(fg="grey")) if e.widget.get() == "" else None)

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