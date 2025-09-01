import os
import logging
import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkfont
from datetime import datetime
from tkcalendar import DateEntry
from tooltips import ToolTip
from config import (
	MODELSPEC_FIELDS, MODELSPEC_TOOLTIPS, MODELSPEC_KEY_MAP, GITHUB_URL,
	MAX_FIELD_LENGTH, MAX_DESCRIPTION_LENGTH, REQUIRED_FIELDS
)
from utils import compute_sha256, utc_to_local, local_to_utc
from commands import (
	BrowseFileCommand, LoadMetadataCommand, SaveCommand,
	SetThumbnailCommand
)
from ui import ImageViewerWindow, AboutWindow, RawViewWindow

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafetensorsEditor(tk.Tk):
	def __init__(self):
		super().__init__()

		# Set up the main window
		self.title("Safetensors Metadata Editor")
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
		self.filepath = tk.StringVar()
		
		# Entry field should expand to fill available space
		entry = tk.Entry(file_frame, textvariable=self.filepath, state="readonly", font=default_font)
		entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
		
		self.browse_btn = tk.Button(file_frame, text="Browse (Ctrl+O)", command=self.browse_file, font=default_font)
		self.browse_btn.pack(side="left", padx=5)

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
				self.thumbnail = tk.StringVar()
				self.set_img_btn = tk.Button(thumb_frame, text="Set Image (Ctrl+I)", command=self.set_thumbnail, font=default_font)
				self.set_img_btn.pack(side="left", padx=2, anchor="w")
				self.view_img_btn = tk.Button(thumb_frame, text="View Image (Ctrl+V)", command=self.toggle_view_thumbnail, font=default_font)
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
		tk.Button(btn_frame, text="Exit (Esc)", command=self.quit, font=default_font).pack(side="right", padx=5)
		self.save_btn = tk.Button(btn_frame, text="Save Changes (Ctrl+S)", command=self.save, font=default_font)
		self.save_btn.pack(side="right", padx=5)
		self.showraw_btn = tk.Button(btn_frame, text="Show Raw (F12)", command=self.toggle_showraw, font=default_font)
		self.showraw_btn.pack(side="right", padx=5)

		# Initialize button states (no file loaded initially)
		self.update_button_states()

		# Status bar for progress indication
		self.status = tk.StringVar()
		self.status.set("Ready")
		status_frame = tk.Frame(self, relief=tk.SUNKEN, bd=1)
		status_frame.pack(side=tk.BOTTOM, fill=tk.X)
		self.status_label = tk.Label(status_frame, textvariable=self.status, anchor=tk.W, padx=5)
		self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

		self.metadata = {}
		self.raw_view = RawViewWindow(self)
		self.image_viewer = ImageViewerWindow(self)
		self.about_window = AboutWindow(self)
		
		# Set up keyboard shortcuts
		self.setup_keyboard_shortcuts()
		
		# Allow window to size itself
		self.update_idletasks()
		self.geometry("")  # Let tkinter calculate size

	def setup_keyboard_shortcuts(self):
		"""Set up keyboard shortcuts for common operations"""
		# File operations
		self.bind_all('<Control-o>', lambda e: self.browse_file())
		self.bind_all('<Control-s>', lambda e: self.save())
		
		# Window operations
		self.bind_all('<Escape>', lambda e: self.quit())
		self.bind_all('<F12>', lambda e: self.toggle_showraw())
		
		# Image operations (when available)
		self.bind_all('<Control-i>', lambda e: self.set_thumbnail() if hasattr(self, 'set_img_btn') and self.set_img_btn['state'] == 'normal' else None)
		self.bind_all('<Control-v>', lambda e: self.toggle_view_thumbnail() if hasattr(self, 'view_img_btn') and self.view_img_btn['state'] == 'normal' else None)
		
		# Help
		self.bind_all('<F1>', lambda e: self.show_about())

	# Commands
	def browse_file(self):
		command = BrowseFileCommand(self)
		success = command.execute()

		if success:
			filepath = command.result
			# Update UI and load the file
			file_size_mb = os.path.getsize(filepath) / (1024**2)
			self.update_status(f"Loading file ({file_size_mb:.1f} MB)...")
			self.filepath.set(filepath)
			self.load_metadata(filepath)
		else:
			# Update button states if browse was cancelled
			self.update_button_states()

	def load_metadata(self, filepath):
		command = LoadMetadataCommand(self, filepath)
		success = command.execute()
		
		if success:
			# Command succeeded - update UI with the loaded metadata
			model_metadata = command.result
			self.update_status("Updating interface...")
			
			self.metadata = model_metadata
			self.populate_fields(model_metadata)
			
			# Update raw view if it exists
			if self.raw_view.is_open():
				self.raw_view.update_metadata(model_metadata)
			
		self.clear_status()
		self.update_button_states()

	def save(self):
		# Validate inputs first
		is_valid, errors = self.validate_inputs()
		if not is_valid:
			error_msg = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
			messagebox.showerror("Validation Error", error_msg)
			return False
			
		# Collect and update metadata
		metadata_updates = self.collect_metadata_from_ui()

		# Merge UI updates into existing metadata
		self.metadata.update(metadata_updates)
		
		# Disable buttons during save operation
		self.disable_all_buttons()
		
		# Create command with all necessary data and completion callback
		command = SaveCommand(
			self,
			filepath=self.filepath.get(),
			metadata=self.metadata,
			completion_callback=self._on_save_complete
		)
		command.execute()
	
	def _on_save_complete(self, success, filepath_or_error):
		self.clear_status()

		# Re-enable buttons based on current state
		self.update_button_states()
		
		if success:
			logger.info(f"File saved: {filepath_or_error}")
			messagebox.showinfo("Complete", f"File saved to:\n{filepath_or_error}")
		else:
			logger.error(f"Error saving file: {filepath_or_error}")
			messagebox.showerror("Error", f"Error saving file:\n{filepath_or_error}")

	def set_thumbnail(self):
		# Close image viewer if open (since we're setting a new thumbnail)
		if self.image_viewer and self.image_viewer.is_open():
			self.image_viewer.close()
			self.image_viewer = None

		command = SetThumbnailCommand(self)
		success = command.execute()

		if success:
			self.thumbnail.set(command.result)
		
		# Update all button states including the view image button
		self.update_button_states()

	def toggle_view_thumbnail(self):
		if self.image_viewer.is_open():
			self.image_viewer.close()
		else:
			thumb_data = self.thumbnail.get()
			if thumb_data:
				self.image_viewer.open(thumb_data)

		# TODO this should be in update_button_states
		self.view_img_btn.config(text="View Image (Ctrl+V)")
		# TODO this should be in update_button_states
		self.view_img_btn.config(text="Close Image (Ctrl+V)")

	def show_about(self):
		self.about_window.open()

	def toggle_showraw(self):
		if self.raw_view.is_open():
			self.raw_view.close()
		else:
			self.raw_view.open(self.metadata)

		# TODO Fix me
		self.showraw_btn.config(text="Show Raw (F12)")			
		self.showraw_btn.config(text="Hide Raw (F12)")		

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
				self.thumbnail.set(thumb_data)
				self.update_view_img_state()
			else:
				self.field_vars[field].set(metadata.get(key, ""))

	def collect_metadata_from_ui(self):
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
				metadata_updates[key] = self.thumbnail.get()
			else:
				value = self.field_vars[field].get().strip()
				# Only add non-empty values to avoid cluttering metadata
				if value:
					metadata_updates[key] = value
				elif key in self.metadata:
					# Remove field if it was cleared
					metadata_updates[key] = ""
		
		return metadata_updates

	def set_button_states(self, showraw=None, set_img=None, view_img=None, browse=None, save=None):
		if showraw is not None:
			self.showraw_btn.config(state=showraw)
		if set_img is not None:
			self.set_img_btn.config(state=set_img)
		if view_img is not None:
			self.view_img_btn.config(state=view_img)
		if browse is not None:
			self.browse_btn.config(state=browse)
		if save is not None:
			self.save_btn.config(state=save)
	
	def disable_all_buttons(self):
		"""Disable all interactive buttons during long-running operations."""
		self.browse_btn.config(state="disabled")
		self.save_btn.config(state="disabled")
		self.showraw_btn.config(state="disabled")
		self.set_img_btn.config(state="disabled")
		self.view_img_btn.config(state="disabled")
	
	def update_button_states(self):
		"""Update all button states based on current application state."""
		# Check if we have a loaded file
		has_file = bool(self.filepath.get())
		
		# Basic buttons that require a loaded file
		self.save_btn.config(state="normal" if has_file else "disabled")
		self.showraw_btn.config(state="normal" if has_file else "disabled")
		self.set_img_btn.config(state="normal" if has_file else "disabled")
		
		# Browse is always enabled
		self.browse_btn.config(state="normal")
		
		# Thumbnail view button depends on whether we have thumbnail data
		self.update_view_img_state()

	def update_status(self, message):
		self.status.set(message)
		self.update_idletasks()

	def clear_status(self):
		self.status.set("Ready")

	def update_view_img_state(self):
		thumb_data = self.thumbnail.get() if hasattr(self, 'thumbnail') else ""
		state = "normal" if thumb_data else "disabled"
		self.set_button_states(view_img=state)
		
		# Update button text based on current viewer state
		if hasattr(self, 'view_img_btn'):
			if self.image_viewer and self.image_viewer.is_open():
				self.view_img_btn.config(text="Close Image (Ctrl+V)")
			elif thumb_data:
				self.view_img_btn.config(text="View Image (Ctrl+V)")
			else:
				self.view_img_btn.config(text="View Image (Ctrl+V)")

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
