import base64
import gc
import io
import os
import logging
import shutil
import webbrowser
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont
from datetime import datetime
from PIL import Image, ImageTk
from safetensors import safe_open
from safetensors.torch import save_file
from tkcalendar import DateEntry
from tooltips import ToolTip
from config import (
	MODELSPEC_FIELDS, MODELSPEC_TOOLTIPS, MODELSPEC_KEY_MAP, GITHUB_URL,
	LARGE_FILE_WARNING_SIZE, THUMBNAIL_SIZE_WARNING, 
	THUMBNAIL_TARGET_SIZE, THUMBNAIL_QUALITY, MAX_FIELD_LENGTH, 
	MAX_DESCRIPTION_LENGTH, REQUIRED_FIELDS
)
from utils import compute_sha256, utc_to_local, local_to_utc, process_image
from metadata import update_safetensors_metadata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafetensorsEditor(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("Safetensors Metadata Editor")
		
		# Set minimum window size but allow resizing
		self.minsize(500, 350)
		self.resizable(True, True)
		
		# Configure main window to expand with content
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)

		default_font = tkfont.nametofont("TkDefaultFont")

		# Create main container frame
		main_frame = tk.Frame(self)
		main_frame.pack(fill="both", expand=True, padx=10, pady=10)

		# File selection
		tk.Label(main_frame, text="Select a file:", font=default_font, anchor="w", justify="left").pack(fill="x", pady=(0, 5))
		file_frame = tk.Frame(main_frame)
		file_frame.pack(fill="x", pady=(0, 10))
		self.filepath_var = tk.StringVar()
		
		# Entry field should expand to fill available space
		entry = tk.Entry(file_frame, textvariable=self.filepath_var, state="readonly", font=default_font)
		entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
		
		tk.Button(file_frame, text="Browse", command=self.browse_file, font=default_font).pack(side="left", padx=5)

		# About button
		self.about_btn = tk.Button(file_frame, text="?", command=self.show_about, font=default_font, width=2)
		self.about_btn.pack(side="right", padx=5)

		# ModelSpec fields
		self.field_vars = {field: tk.StringVar() for field in MODELSPEC_FIELDS if field != "date" and field != "description"}
		fields_frame = tk.LabelFrame(main_frame, text="Metadata Fields", font=default_font)
		fields_frame.pack(fill="both", expand=True, pady=(0, 5))
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
				desc_frame.grid_columnconfigure(0, weight=1)
				self.description_text = tk.Text(
					desc_frame,
					height=3,
					wrap="word",
					font=default_font
				)
				self.description_text.grid(row=0, column=0, sticky="ew")
				desc_scroll = tk.Scrollbar(desc_frame, orient="vertical", command=self.description_text.yview)
				desc_scroll.grid(row=0, column=1, sticky="ns")
				self.description_text.config(yscrollcommand=desc_scroll.set)
			else:
				entry = tk.Entry(fields_frame, textvariable=self.field_vars[field], font=default_font)
				entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")

		# Action buttons
		btn_frame = tk.Frame(main_frame)
		btn_frame.pack(fill="x")
		tk.Button(btn_frame, text="Exit", command=self.quit, font=default_font).pack(side="right", padx=5)
		tk.Button(btn_frame, text="Save Changes", command=self.save_changes, font=default_font).pack(side="right", padx=5)
		self.showraw_btn = tk.Button(btn_frame, text="Show Raw", command=self.toggle_showraw, font=default_font)
		self.showraw_btn.pack(side="right", padx=5)

		self.set_button_states(showraw="disabled", set_img="disabled", view_img="disabled")

		# Status bar for progress indication
		self.status_var = tk.StringVar()
		self.status_var.set("Ready")
		status_frame = tk.Frame(self, relief=tk.SUNKEN, bd=1)
		status_frame.pack(side=tk.BOTTOM, fill=tk.X)
		self.status_label = tk.Label(status_frame, textvariable=self.status_var, anchor=tk.W, padx=5)
		self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

		self.metadata = {}
		self.sidecar = None
		self.image_viewer = None
		
		# Allow window to size itself
		self.update_idletasks()
		self.geometry("")  # Let tkinter calculate size
	
	def update_status_threadsafe(self, message):
		"""Thread-safe status update using after()"""
		self.after(0, lambda: self.update_status(message))

	def update_status(self, message):
		"""Update the status bar with a message"""
		self.status_var.set(message)
		self.update_idletasks()

	def clear_status(self):
		"""Clear the status bar"""
		self.status_var.set("Ready")

	def browse_file(self):
		filepath = filedialog.askopenfilename(
			filetypes=[("Safetensors Files", "*.safetensors")],
			title="Select a safetensors file"
		)
		if filepath:
			# Validate file exists and is readable
			if not os.access(filepath, os.R_OK):
				messagebox.showerror("Error", f"File is not readable: {filepath}")
				return
			
			# Check file size (warn for very large files)
			file_size = os.path.getsize(filepath)
			file_size_mb = file_size / (1024**2)
			file_size_gb = file_size / (1024**3)
			
			if file_size > LARGE_FILE_WARNING_SIZE:
				if file_size_gb > 1:
					size_str = f"{file_size_gb:.1f} GB"
				else:
					size_str = f"{file_size_mb:.0f} MB"
					
				choice = messagebox.askyesno(
					"Large File Warning", 
					f"File is very large ({size_str}).\n"
					f"Loading may take a while and use significant memory.\n\n"
					f"Estimated memory usage: ~{file_size_mb * 2:.0f} MB\n"
					f"Continue?"
				)
				if not choice:
					return
			
			logger.info(f"Loading file: {filepath} ({file_size_mb:.1f} MB)")
			self.update_status(f"Loading file ({file_size_mb:.1f} MB)...")
			self.filepath_var.set(filepath)
			self.load_metadata(filepath)
		else:
			# Only disable buttons if no file is loaded
			if not self.filepath_var.get():
				self.set_button_states(showraw="disabled", set_img="disabled", view_img="disabled")

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
		self.sidecar.geometry(f"800x400+{sidecar_x}+{sidecar_y}")
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
			for k, v in sorted(d.items()):
				key_lengths.append(len(str(k)))
				if isinstance(v, dict):
					node = tree.insert(parent, "end", text=k, values=("",))
					insert_items(node, v)
				else:
					tree.insert(parent, "end", text=k, values=(str(v),))
		insert_items("", metadata)

		if key_lengths:
			max_key_len = max(key_lengths)
			tree.column("#0", width=max(100, min(20 + max_key_len * 7, 400)), stretch=False)
		else:
			tree.column("#0", width=100, stretch=False)
		tree.column("value", width=200, stretch=True)

	def load_metadata(self, filepath):
		try:
			self.update_status("Reading file metadata...")
			
			# Try to open and read metadata
			with safe_open(filepath, framework="pt") as f:
				model_metadata = f.metadata().copy() or {}
			
			self.update_status("Updating interface...")
			
			# Success - update UI
			self.metadata = model_metadata
			self.populate_fields(model_metadata)
			self.set_button_states(showraw="normal", set_img="normal")
			self.update_view_img_state()
			if self.sidecar and self.sidecar.winfo_exists():
				self.populate_sidecar_tree(model_metadata)
			
			self.clear_status()
			logger.info(f"Loaded metadata from: {filepath}")
			
		except Exception as e:
			# Single catch-all with logging
			self.clear_status()
			logger.error(f"Error loading {filepath}: {e}")
			messagebox.showerror("Error", f"Error reading file:\n{e}")
			self._reset_ui_state()

	def _reset_ui_state(self):
		"""Reset UI to safe state after load failure"""
		self.clear_status()
		self.metadata = {}
		self.populate_fields({})
		self.set_button_states(showraw="disabled", set_img="disabled", view_img="disabled")
		if self.sidecar and self.sidecar.winfo_exists():
			self.populate_sidecar_tree({})

	def populate_fields(self, metadata):
		for field in MODELSPEC_FIELDS:
			key = MODELSPEC_KEY_MAP.get(field, field)
			if field == "date":
				date_str = metadata.get(key, "")
				if date_str:
					try:
						dt_local = utc_to_local(date_str)
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
				thumb_data = metadata.get(key, "")
				self.thumbnail_var.set(thumb_data)
				self.update_view_img_state()
			else:
				self.field_vars[field].set(metadata.get(key, ""))

	def set_thumbnail_image(self):
		filepath = filedialog.askopenfilename(
			filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.webp"), ("JPEG Image", "*.jpg;*.jpeg"), ("PNG Image", "*.png"), ("WebP Image", "*.webp")],
			title="Select a thumbnail image"
		)
		if filepath:
			try:
				# Close any open image viewer since we're setting a new image
				if self.image_viewer and self.image_viewer.winfo_exists():
					self._close_image_viewer()
					
				self.update_status("Processing image...")
				
				# Process image with callback for resize decision
				def ask_resize(file_size_mb):
					return messagebox.askyesno(
						"Large Image File", 
						f"Image file is {file_size_mb:.1f}MB. "
						"Would you like to automatically resize it to reduce file size? "
						f"(Will resize to fit within {THUMBNAIL_TARGET_SIZE}x{THUMBNAIL_TARGET_SIZE} while maintaining aspect ratio)"
					)
				
				result = process_image(
					filepath, 
					target_size=THUMBNAIL_TARGET_SIZE,
					quality=THUMBNAIL_QUALITY,
					size_warning_threshold=THUMBNAIL_SIZE_WARNING,
					resize_callback=ask_resize
				)
				
				if result['success']:
					self.thumbnail_var.set(result['data_uri'])
					self.update_view_img_state()
					self.clear_status()
					logger.info(f"Thumbnail set from: {filepath}")
				else:
					self.clear_status()
					raise Exception(result['error'])
					
			except Exception as e:
				self.clear_status()
				logger.error(f"Error setting thumbnail: {e}")
				messagebox.showerror("Error", f"Could not set thumbnail: {e}")

	def view_thumbnail_image(self):
		# Check if image viewer is already open - if so, close it
		if self.image_viewer and self.image_viewer.winfo_exists():
			self._close_image_viewer()
			return
			
		data_uri = self.thumbnail_var.get()
		if not data_uri.startswith("data:image/jpeg;base64,"):
			messagebox.showerror("Error", "No valid thumbnail image set.")
			return
		try:
			b64 = data_uri.split(",", 1)[1]
			img_data = base64.b64decode(b64)
			image = Image.open(io.BytesIO(img_data))
			
			# Create new image viewer window
			self.image_viewer = tk.Toplevel(self)
			self.image_viewer.title("Thumbnail Preview")
			self.image_viewer.resizable(False, False)
			
			# Position the image viewer to the left of the main window
			main_x = self.winfo_x()
			main_y = self.winfo_y()
			main_width = self.winfo_width()
			main_height = self.winfo_height()
			
			img_width = image.width
			img_height = image.height
			
			# Position to the left of main window with some spacing
			left_x = main_x - img_width - 10  # 10px gap
			# Center vertically relative to main window
			center_y = main_y + (main_height - img_height) // 2
			
			# Ensure window doesn't go off-screen to the left
			if left_x < 0:
				left_x = 10  # Minimum distance from screen edge
			
			self.image_viewer.geometry(f"{img_width}x{img_height}+{left_x}+{center_y}")
			
			# Clean up reference when window is closed
			self.image_viewer.protocol("WM_DELETE_WINDOW", self._close_image_viewer)
			
			img_tk = ImageTk.PhotoImage(image)
			lbl = tk.Label(self.image_viewer, image=img_tk)
			lbl.image = img_tk  # Keep a reference to prevent garbage collection
			lbl.pack()
			
			# Update button text to "Close Image"
			self.view_img_btn.config(text="Close Image")
			
		except Exception as e:
			messagebox.showerror("Error", f"Could not display image: {e}")

	def _close_image_viewer(self):
		"""Clean up when image viewer window is closed"""
		if self.image_viewer and self.image_viewer.winfo_exists():
			self.image_viewer.destroy()
		self.image_viewer = None
		# Update button text back to "View Image"
		if hasattr(self, 'view_img_btn'):
			self.view_img_btn.config(text="View Image")

	def collect_metadata_from_fields(self):
		"""Extract metadata from UI fields with validation"""
		metadata_updates = {}
		
		for field in MODELSPEC_FIELDS:
			key = MODELSPEC_KEY_MAP.get(field, field)
			if field == "date":
				date_val = self.date_picker.get_date()
				hour_val = self.hour_var.get() or "0"
				minute_val = self.minute_var.get() or "0"
				try:
					dt_utc_str = local_to_utc(date_val, hour_val, minute_val)
					metadata_updates[key] = dt_utc_str
				except Exception as e:
					logger.warning(f"Failed to parse date/time: {e}")
					metadata_updates[key] = ""
			elif field == "description":
				text = self.description_text.get("1.0", tk.END).strip()
				metadata_updates[key] = text
			elif field == "thumbnail":
				metadata_updates[key] = self.thumbnail_var.get()
			else:
				value = self.field_vars[field].get().strip()
				# Only add non-empty values to avoid cluttering metadata
				if value:
					metadata_updates[key] = value
				elif key in self.metadata:
					# Remove field if it was cleared
					metadata_updates[key] = ""
		
		return metadata_updates

	def save_changes(self):
		filepath = self.filepath_var.get()
		if not filepath:
			messagebox.showerror("Error", "Please select a file first.")
			return

		# Validate inputs first
		is_valid, errors = self.validate_inputs()
		if not is_valid:
			error_msg = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
			messagebox.showerror("Validation Error", error_msg)
			return

		choice = messagebox.askquestion(
			"Save Options",
			"Do you want to overwrite the existing file?\n\n"
			"Click 'Yes' to overwrite.\n"
			"Click 'No' to create a backup and then overwrite.",
			icon="question"
		)

		# Collect and update metadata
		metadata_updates = self.collect_metadata_from_fields()
		self.metadata.update(metadata_updates)

		# Start save operation in background thread
		save_thread = threading.Thread(
			target=self.save_changes_threaded,
			args=(filepath, choice, self.metadata.copy()),
			daemon=True
		)
		save_thread.start()

	def save_changes_threaded(self, filepath, choice, metadata):
		try:
			# Compute hash if needed
			if "modelspec.hash_sha256" not in metadata:
				self.update_status_threadsafe("Computing file hash...")
				metadata["modelspec.hash_sha256"] = compute_sha256(filepath)

			tmp_path = filepath + ".tmp"
			backup_path = filepath + ".bak"

			# Always create backup first - safety first!
			self.update_status_threadsafe("Creating backup...")
			if os.path.exists(backup_path):
				os.remove(backup_path)
			shutil.copy2(filepath, backup_path)

			# Use the optimized safetensors metadata update
			method_used = update_safetensors_metadata(
				filepath, 
				metadata, 
				tmp_path, 
				progress_callback=self.update_status_threadsafe
			)
			
			if method_used == "optimized":
				logger.info("Metadata updated using optimized method")
			else:
				logger.info("Metadata updated using standard method")

			# Replace original file with updated version
			self.update_status_threadsafe("Finalizing save...")
			os.remove(filepath)
			os.rename(tmp_path, filepath)
			
			# If user doesn't want backup, clean it up
			if choice == "yes":
				os.remove(backup_path)
			
			# Success - update UI on main thread
			self.after(0, lambda: self._save_success(filepath))
			
		except Exception as e:
			# Error - update UI on main thread  
			self.after(0, lambda: self._save_error(e))

	def _save_success(self, filepath):
		"""Called on main thread when save succeeds"""
		self.clear_status()
		logger.info(f"File saved: {filepath}")
		messagebox.showinfo("Complete", f"File saved to:\n{filepath}")

	def _save_error(self, error):
		"""Called on main thread when save fails"""
		self.clear_status()
		logger.error(f"Error saving file: {error}")
		messagebox.showerror("Error", f"Error saving file:\n{error}")

	def set_button_states(self, showraw=None, set_img=None, view_img=None):
		if showraw is not None:
			self.showraw_btn.config(state=showraw)
		if set_img is not None:
			self.set_img_btn.config(state=set_img)
		if view_img is not None:
			self.view_img_btn.config(state=view_img)

	def update_view_img_state(self):
		thumb_data = self.thumbnail_var.get() if hasattr(self, 'thumbnail_var') else ""
		state = "normal" if thumb_data else "disabled"
		self.set_button_states(view_img=state)
		
		# Reset button text when no image is available
		if not thumb_data and hasattr(self, 'view_img_btn'):
			self.view_img_btn.config(text="View Image")

	def show_about(self):
		# Use a Toplevel window for clickable link
		about_win = tk.Toplevel(self)
		about_win.title("About MetaEditor Safetensors")
		about_win.geometry("350x180")
		about_win.resizable(False, False)
		
		# Center the about window over the main window
		main_x = self.winfo_x()
		main_y = self.winfo_y()
		main_width = self.winfo_width()
		main_height = self.winfo_height()
		
		about_width = 350
		about_height = 180
		
		center_x = main_x + (main_width - about_width) // 2
		center_y = main_y + (main_height - about_height) // 2
		
		about_win.geometry(f"{about_width}x{about_height}+{center_x}+{center_y}")

		tk.Label(about_win, text="MetaEditor Safetensors", font=("TkDefaultFont", 12, "bold")).pack(pady=(12,2))
		tk.Label(about_win, text="Version 1.0", font=("TkDefaultFont", 10)).pack()
		tk.Label(about_win, text="A simple tool for viewing and editing safetensors metadata.", wraplength=320, justify="center").pack(pady=(6,2))
		tk.Label(about_win, text="Author: KPandaK", font=("TkDefaultFont", 9)).pack(pady=(2,8))
		
		def open_github(event=None):
			webbrowser.open_new(GITHUB_URL)

		link = tk.Label(about_win, text="GitHub Repository", fg="blue", cursor="hand2", font=("TkDefaultFont", 10, "underline"))
		link.pack()
		link.bind("<Button-1>", open_github)

		tk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)

	def validate_inputs(self):
		"""Validate all user inputs and return (is_valid, error_messages)"""
		errors = []

		# Validate field lengths
		for field in MODELSPEC_FIELDS:
			if field == "date" or field == "thumbnail":
				continue
			elif field == "description":
				text = self.description_text.get("1.0", tk.END).strip()
				if len(text) > MAX_DESCRIPTION_LENGTH:
					errors.append(f"Description is too long ({len(text)} chars, max {MAX_DESCRIPTION_LENGTH})")
			else:
				if field in self.field_vars:
					text = self.field_vars[field].get().strip()
					if len(text) > MAX_FIELD_LENGTH:
						errors.append(f"{field.title()} is too long ({len(text)} chars, max {MAX_FIELD_LENGTH})")
		
		# Check required fields
		for field in REQUIRED_FIELDS:
			if field == "description":
				text = self.description_text.get("1.0", tk.END).strip()
				if not text:
					errors.append(f"{field.title()} is required")
			elif field in self.field_vars:
				text = self.field_vars[field].get().strip()
				if not text:
					errors.append(f"{field.title()} is required")
		
		return len(errors) == 0, errors
