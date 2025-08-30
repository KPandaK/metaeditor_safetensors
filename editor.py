import base64
import io
import shutil
import time
import gc
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timezone, timedelta
from gui_tooltips import ToolTip
from PIL import Image, ImageTk
from safetensors import safe_open
from safetensors.torch import save_file
from tkcalendar import DateEntry
from tkinter import filedialog, messagebox, ttk

from config import MODELSPEC_FIELDS, MODELSPEC_TOOLTIPS, MODELSPEC_KEY_MAP
from utils import compute_sha256, merge_metadata

class SafetensorsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Safetensors Metadata Editor")
        self.geometry("525x370")
        self.resizable(False, False)

        default_font = tkfont.nametofont("TkDefaultFont")

        # File selection
        tk.Label(self, text="Select a file:", font=default_font, anchor="w", justify="left").pack(padx=10, fill="x")
        file_frame = tk.Frame(self)
        file_frame.pack(fill="x", padx=10)
        self.filepath_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.filepath_var, width=60, state="readonly", font=default_font).pack(side="left", padx=5)
        tk.Button(file_frame, text="Browse", command=self.browse_file, font=default_font).pack(side="left", padx=5)

        # ModelSpec fields
        self.field_vars = {field: tk.StringVar() for field in MODELSPEC_FIELDS if field != "date" and field != "description"}
        fields_frame = tk.LabelFrame(self, text="Metadata Fields", font=default_font)
        fields_frame.pack(fill="x", padx=10, ipady=3)
        fields_frame.grid_columnconfigure(1, weight=1)

        self.date_picker = None
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()
        for i, field in enumerate(MODELSPEC_FIELDS):
            label_sticky = "nw" if field == "description" else "w"
            label = tk.Label(fields_frame, text=field+":", width=12, anchor="w", font=default_font)
            label.grid(row=i, column=0, sticky=label_sticky, padx=5, pady=2)
            ToolTip(label, MODELSPEC_TOOLTIPS.get(field, ""))
            if field == "date":
                date_time_frame = tk.Frame(fields_frame)
                date_time_frame.grid(row=i, column=1, sticky="ew", padx=5, pady=2, columnspan=5)
                self.date_picker = DateEntry(date_time_frame, width=12, date_pattern="yyyy-mm-dd", font=default_font)
                self.date_picker.pack(side="left", padx=(0, 4))
                tk.Spinbox(date_time_frame, from_=0, to=23, width=3, textvariable=self.hour_var, format="%02.0f", font=default_font).pack(side="left", padx=4)
                tk.Label(date_time_frame, text=":").pack(side="left")
                tk.Spinbox(date_time_frame, from_=0, to=59, width=3, textvariable=self.minute_var, format="%02.0f", font=default_font).pack(side="left")
                tk.Label(date_time_frame, text="Local (HH:MM)").pack(side="left", padx=(4,0))
            elif field == "thumbnail":
                thumb_frame = tk.Frame(fields_frame)
                thumb_frame.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
                self.thumbnail_var = tk.StringVar()
                self.set_img_btn = tk.Button(thumb_frame, text="Set Image", command=self.set_thumbnail_image, font=default_font)
                self.set_img_btn.pack(side="left", padx=2, anchor="w")
                self.view_img_btn = tk.Button(thumb_frame, text="View Image", command=self.view_thumbnail_image, font=default_font)
                self.view_img_btn.pack(side="left", padx=2, anchor="w")
                self.set_img_btn.config(state="disabled")
                self.view_img_btn.config(state="disabled")
            elif field == "description":
                desc_frame = tk.Frame(fields_frame)
                desc_frame.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                self.description_text = tk.Text(
                    desc_frame,
                    height=3,
                    width=60,
                    wrap="word",
                    font=default_font
                )
                self.description_text.pack(side="left", fill="both", expand=True)
                desc_scroll = tk.Scrollbar(desc_frame, orient="vertical", command=self.description_text.yview)
                desc_scroll.pack(side="right", fill="y")
                self.description_text.config(yscrollcommand=desc_scroll.set)
            else:
                entry = tk.Entry(fields_frame, textvariable=self.field_vars[field], width=60, font=default_font)
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")

        # Action buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(btn_frame, text="Exit", command=self.quit, font=default_font).pack(side="right", padx=5)        
        tk.Button(btn_frame, text="Save Changes", command=self.save_changes, font=default_font).pack(side="right", padx=5)        
        self.showraw_btn = tk.Button(btn_frame, text="Show Raw", command=self.toggle_showraw, font=default_font)
        self.showraw_btn.pack(side="right", padx=5)

        self.showraw_btn.config(state="disabled")
        self.set_img_btn.config(state="disabled")
        self.view_img_btn.config(state="disabled")

        self.metadata = {}
        self.sidecar = None

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Safetensors Files", "*.safetensors")],
            title="Select a safetensors file"
        )
        if filepath:
            self.filepath_var.set(filepath)
            self.load_metadata(filepath)
        else:
            # Only disable buttons if no file is loaded
            if not self.filepath_var.get():
                self.showraw_btn.config(state="disabled")
                self.set_img_btn.config(state="disabled")
                self.view_img_btn.config(state="disabled")

    def toggle_showraw(self):
        if self.sidecar and self.sidecar.winfo_exists():
            self.close_sidecar()
            self.showraw_btn.config(text="Show Raw")
        else:
            self.open_sidecar()
            self.showraw_btn.config(text="Hide Raw")

    def open_sidecar(self):
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        sidecar_x = main_x + main_width + 10
        sidecar_y = main_y

        self.sidecar = tk.Toplevel(self)
        self.sidecar.title("Raw Metadata")
        self.sidecar.geometry(f"400x600+{sidecar_x}+{sidecar_y}")
        self.sidecar.resizable(True, True)
        self.sidecar.protocol("WM_DELETE_WINDOW", self.toggle_showraw)

        tree = ttk.Treeview(self.sidecar, columns=("value",), show="tree headings")
        tree.heading("#0", text="Key")
        tree.heading("value", text="Value")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.sidecar_tree = tree

        self.populate_sidecar_tree(self.metadata)

    def close_sidecar(self):
        if self.sidecar and self.sidecar.winfo_exists():
            self.sidecar.destroy()
            self.sidecar = None

    def populate_sidecar_tree(self, metadata):
        tree = self.sidecar_tree
        tree.delete(*tree.get_children())
        key_lengths = []

        def insert_items(parent, d):
            for k, v in d.items():
                key_lengths.append(len(str(k)))
                if isinstance(v, dict):
                    node = tree.insert(parent, "end", text=k, values=("",))
                    insert_items(node, v)
                else:
                    tree.insert(parent, "end", text=k, values=(str(v),))
        insert_items("", metadata)

        if key_lengths:
            max_key_len = max(key_lengths)
            tree.column("#0", width=max(100, min(40 + max_key_len * 8, 400)), stretch=False)
        else:
            tree.column("#0", width=100, stretch=False)
        tree.column("value", width=200, stretch=True)

    def load_metadata(self, filepath):
        try:
            with safe_open(filepath, framework="pt") as f:
                metadata = f.metadata() or {}
            model_metadata = metadata
            self.metadata = model_metadata
            self.populate_fields(model_metadata)
            self.showraw_btn.config(state="normal")
            self.set_img_btn.config(state="normal")
            self.view_img_btn.config(state="normal")
            if self.sidecar and self.sidecar.winfo_exists():
                self.populate_sidecar_tree(model_metadata)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading file:\n{e}")
            self.metadata = {}
            self.populate_fields({})
            self.showraw_btn.config(state="disabled")
            self.set_img_btn.config(state="disabled")
            self.view_img_btn.config(state="disabled")
            if self.sidecar and self.sidecar.winfo_exists():
                self.populate_sidecar_tree({})

    def populate_fields(self, metadata):
        for field in MODELSPEC_FIELDS:
            key = MODELSPEC_KEY_MAP.get(field, field)
            if field == "date":
                date_str = metadata.get(key, "")
                if date_str:
                    try:
                        dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        dt_local = dt_utc.astimezone()
                        self.date_picker.set_date(dt_local.date())
                        self.hour_var.set(dt_local.strftime("%H"))
                        self.minute_var.set(dt_local.strftime("%M"))
                    except Exception:
                        self.date_picker.set_date(datetime.now().date())
                        self.hour_var.set("00")
                        self.minute_var.set("00")
                else:
                    self.date_picker.set_date(datetime.now().date())
                    self.hour_var.set("00")
                    self.minute_var.set("00")
            elif field == "description":
                self.description_text.delete("1.0", tk.END)
                self.description_text.insert(tk.END, metadata.get(key, ""))
            elif field == "thumbnail":
                self.thumbnail_var.set(metadata.get(key, ""))
            else:
                self.field_vars[field].set(metadata.get(key, ""))

    def set_thumbnail_image(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JPEG Image", "*.jpg;*.jpeg")],
            title="Select a thumbnail image"
        )
        if filepath:
            try:
                with open(filepath, "rb") as img_file:
                    b64 = base64.b64encode(img_file.read()).decode("utf-8")
                data_uri = f"data:image/jpeg;base64,{b64}"
                self.thumbnail_var.set(data_uri)
            except Exception as e:
                messagebox.showerror("Error", f"Could not set thumbnail: {e}")

    def view_thumbnail_image(self):
        data_uri = self.thumbnail_var.get()
        if not data_uri.startswith("data:image/jpeg;base64,"):
            messagebox.showerror("Error", "No valid thumbnail image set.")
            return
        try:
            b64 = data_uri.split(",", 1)[1]
            img_data = base64.b64decode(b64)
            image = Image.open(io.BytesIO(img_data))
            popup = tk.Toplevel(self)
            popup.title("Thumbnail Preview")
            popup.geometry(f"{image.width}x{image.height}")
            popup.resizable(False, False)
            img_tk = ImageTk.PhotoImage(image)
            lbl = tk.Label(popup, image=img_tk)
            lbl.image = img_tk
            lbl.pack()
        except Exception as e:
            messagebox.showerror("Error", f"Could not display image: {e}")

    def save_changes(self):
        filepath = self.filepath_var.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a file first.")
            return

        choice = messagebox.askquestion(
            "Save Options",
            "Do you want to overwrite the existing file?\n\n"
            "Click 'Yes' to overwrite.\n"
            "Click 'No' to create a backup and then overwrite.",
            icon="question"
        )

        tensors = {}
        try:
            with safe_open(filepath, framework="pt") as f:
                existing_metadata = f.metadata().copy() or {}
                for k in f.keys():
                    tensors[k] = f.get_tensor(k)
            gc.collect()
        except Exception as e:
            messagebox.showerror("Error", f"Error reading file for merge:\n{e}")
            return

        updated_metadata = {}
        for field in MODELSPEC_FIELDS:
            key = MODELSPEC_KEY_MAP.get(field, field)
            if field == "date":
                date_val = self.date_picker.get_date()
                hour_val = self.hour_var.get()
                minute_val = self.minute_var.get()
                try:
                    local_dt = datetime.strptime(f"{date_val} {hour_val}:{minute_val}", "%Y-%m-%d %H:%M")
                    offset_sec = -time.timezone if (time.localtime().tm_isdst == 0) else -time.altzone
                    offset = timedelta(seconds=offset_sec)
                    local_dt = local_dt.replace(tzinfo=timezone(offset))
                    dt_utc = local_dt.astimezone(timezone.utc)
                    updated_metadata[key] = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                except Exception:
                    updated_metadata[key] = ""
            elif field == "description":
                updated_metadata[key] = self.description_text.get("1.0", tk.END).strip()
            elif field == "thumbnail":
                updated_metadata[key] = self.thumbnail_var.get()
            else:
                value = self.field_vars[field].get()
                if value:
                    updated_metadata[key] = value

        merged_metadata = existing_metadata.copy()
        merged_metadata.update(updated_metadata)

        if "modelspec.hash_sha256" not in merged_metadata:
            try:
                merged_metadata["modelspec.hash_sha256"] = compute_sha256(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Could not compute sha256:\n{e}")
                return

        if choice == "no":
            backup_path = filepath + ".bak"
            shutil.copy(filepath, backup_path)

        try:
            save_file(tensors, filepath, metadata=merged_metadata)
            messagebox.showinfo("Success", f"Successfully saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")