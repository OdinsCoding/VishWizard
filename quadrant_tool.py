import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import copy 

class QuadrantTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Reactive Dynamic Dashboard")
        
        self.base_font_size = 9
        self.profiles = {}
        self.current_profile = "default"
        
        # --- THE MASTER TEMPLATE ---
        # This is the "Factory Reset" state. It never gets modified.
        self.MASTER_TEMPLATE = {
            "Who I Am": {"Name": "", "Role": "", "Company": "", "Reason": ""},
            "Target": {"Name": "", "Role": "", "Phone": "", "Email": "", "Location": "", "Other": ""},
            "Pretext": {"Who I work for": "", "Why I'm calling": "", "What I need": "", "Justifications": ""},
            "Goals & Flags": {"VPN": "", "IT Help Desk": "", "Software": "", "Devices": "", "Security": "", "Other": ""}
        }
        
        # Initialize first profile with a DEEP copy
        self.profiles[self.current_profile] = copy.deepcopy(self.MASTER_TEMPLATE)
        
        self.setup_main_layout()
        self.refresh_ui(initial_load=True)

    def setup_main_layout(self):
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas)

        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_win = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_win, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def refresh_ui(self, initial_load=False):
        """Wipes the UI and rebuilds it based ONLY on the current profile data."""
        if hasattr(self, 'ui_elements') and self.ui_elements:
            self.sync_to_memory()

        # Completely destroy current widgets to ensure a clean slate
        for w in self.top_frame.winfo_children(): w.destroy()
        for w in self.scroll_content.winfo_children(): w.destroy()

        # --- Top Controls ---
        p_row = tk.Frame(self.top_frame)
        p_row.pack(fill='x')
        tk.Button(p_row, text="New Profile", command=self.new_profile).pack(side='left', padx=2)
        tk.Button(p_row, text="Export JSON", command=self.export_json, bg="#e8f5e9").pack(side='left', padx=2)
        tk.Button(p_row, text="Import JSON", command=self.import_json).pack(side='left', padx=2)
        tk.Label(p_row, text=f"Profile: {self.current_profile}", fg="blue", font=("Arial", 10, "bold")).pack(side='left', padx=15)

        q_row = tk.Frame(self.top_frame)
        q_row.pack(fill='x', pady=5)
        q_count = len(self.profiles[self.current_profile])
        tk.Label(q_row, text=f"Quadrants ({q_count}/10):", font=("Arial", 9, "bold")).pack(side='left', padx=5)
        tk.Button(q_row, text="+ Add Quadrant", command=self.add_q, bg="#e3f2fd").pack(side='left', padx=2)
        tk.Button(q_row, text="- Delete Quadrant", command=self.del_q, bg="#ffebee").pack(side='left', padx=2)

        self.scroll_content.columnconfigure(0, weight=1)
        self.scroll_content.columnconfigure(1, weight=1)

        self.ui_elements = {}
        data = self.profiles[self.current_profile]

        for i, (q_name, fields) in enumerate(data.items()):
            box = ttk.LabelFrame(self.scroll_content, text=f" {q_name} ")
            box.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')
            box.columnconfigure(1, weight=1)

            btns = tk.Frame(box)
            btns.grid(row=0, column=0, columnspan=2, sticky='e')
            tk.Button(btns, text="+", width=2, command=lambda n=q_name: self.add_f(n)).pack(side='right')
            tk.Button(btns, text="-", width=2, command=lambda n=q_name: self.del_f(n)).pack(side='right')

            self.ui_elements[q_name] = {}
            for r, (fname, val) in enumerate(fields.items(), start=1):
                tk.Label(box, text=fname, font=("Arial", self.base_font_size)).grid(row=r, column=0, sticky='nw', padx=5, pady=2)
                t = tk.Text(box, height=1, wrap="word", font=("Arial", self.base_font_size), undo=True, width=15)
                t.insert("1.0", val)
                t.grid(row=r, column=1, sticky='ew', padx=5, pady=2)
                
                t.bind("<KeyRelease>", lambda e: self.adjust_height(e.widget))
                self.ui_elements[q_name][fname] = t
        
        # Batch fix heights AFTER layout to prevent massive expansion bug
        self.root.after(100, self.batch_adjust_heights)

        if initial_load:
            self.root.update_idletasks()
            width = self.scroll_content.winfo_reqwidth() + 50
            height = self.scroll_content.winfo_reqheight() + self.top_frame.winfo_reqheight() + 100
            self.root.geometry(f"{max(850, width)}x{max(700, height)}")

    def batch_adjust_heights(self):
        for q in self.ui_elements.values():
            for t in q.values():
                self.adjust_height(t)

    def adjust_height(self, widget):
        """Prevents horizontal-to-vertical expansion spiral."""
        try:
            if widget.winfo_width() > 1:
                lines = int(widget.tk.call(widget._w, "count", "-displaylines", "1.0", "end-1c"))
                widget.configure(height=min(15, max(1, lines)))
        except tk.TclError:
            pass

    def sync_to_memory(self):
        for q_name, fields in self.ui_elements.items():
            if q_name in self.profiles[self.current_profile]:
                for f_name, widget in fields.items():
                    self.profiles[self.current_profile][q_name][f_name] = widget.get("1.0", "end-1c").strip()

    def new_profile(self):
        """Creates a brand new profile using the untouched Master Template."""
        n = simpledialog.askstring("New Profile", "Enter Profile Name:")
        if n:
            self.sync_to_memory()
            # Deepcopy ensures Profile A cannot leak into Profile B
            self.profiles[n] = copy.deepcopy(self.MASTER_TEMPLATE)
            self.current_profile = n
            self.ui_elements = {} 
            self.refresh_ui()

    def export_json(self):
        """Only exports the CURRENT active profile data."""
        self.sync_to_memory()
        export_package = {
            "active_profile": self.current_profile,
            "profile_data": self.profiles[self.current_profile]
        }
        file = filedialog.asksaveasfilename(initialfile=f"{self.current_profile}_config.json", defaultextension=".json")
        if file:
            with open(file, "w") as f:
                json.dump(export_package, f, indent=2)
            messagebox.showinfo("Exported", f"Saved ONLY profile: {self.current_profile}")

    def import_json(self):
        file = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if file:
            with open(file, "r") as f:
                data = json.load(f)
            if "active_profile" in data and "profile_data" in data:
                self.profiles[data["active_profile"]] = data["profile_data"]
                self.current_profile = data["active_profile"]
            else:
                self.profiles.update(data)
                self.current_profile = list(data.keys())[0]
            self.ui_elements = {}
            self.refresh_ui()

    def add_q(self):
        if len(self.profiles[self.current_profile]) >= 10: return
        n = simpledialog.askstring("Add", "Quadrant Name:")
        if n: 
            self.profiles[self.current_profile][n] = {"New Field": ""}
            self.refresh_ui()

    def del_q(self):
        if len(self.profiles[self.current_profile]) <= 1: return
        n = simpledialog.askstring("Delete", "Exact Quadrant Name:")
        if n in self.profiles[self.current_profile]:
            del self.profiles[self.current_profile][n]
            self.refresh_ui()

    def add_f(self, q_name):
        n = simpledialog.askstring("Field", "Field Name:")
        if n:
            self.profiles[self.current_profile][q_name][n] = ""
            self.refresh_ui()

    def del_f(self, q_name):
        f_list = list(self.profiles[self.current_profile][q_name].keys())
        n = simpledialog.askstring("Remove", f"Field in {q_name}:\n{f_list}")
        if n in self.profiles[self.current_profile][q_name]:
            del self.profiles[self.current_profile][q_name][n]
            self.refresh_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuadrantTool(root)
    root.mainloop()