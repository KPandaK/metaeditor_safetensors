import base64
import hashlib
import io
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from PIL import Image

def get_local_timezone():
	return datetime.now().astimezone().tzinfo

def compute_sha256(filepath):
	with open(filepath, "rb") as f:
		header_len = int.from_bytes(f.read(8), "little")
		f.seek(8 + header_len)
		tensor_bytes = f.read()
	sha = hashlib.sha256(tensor_bytes).hexdigest()
	return "0x" + sha.lower()

def utc_to_local(utc_str):
	# Safeguard: ensure UTC string ends with 'Z' or '+00:00'
	if not (utc_str.endswith('Z') or utc_str.endswith('+00:00')):
		utc_str = utc_str + 'Z'
	local_tz = get_local_timezone()
	dt_utc = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
	local_dt = dt_utc.astimezone(local_tz)
	return local_dt

def local_to_utc(date_val, hour_val, minute_val):
	local_tz = get_local_timezone()
	local_dt = datetime.strptime(f"{date_val} {hour_val}:{minute_val}", "%Y-%m-%d %H:%M")
	local_dt = local_dt.replace(tzinfo=local_tz)
	dt_utc = local_dt.astimezone(timezone.utc)
	utc_str = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
	return utc_str

def resize_image(img, target_size):
	original_width, original_height = img.size
	
	if original_width > original_height:
		new_width = target_size
		new_height = int((original_height * target_size) / original_width)
	else:
		new_height = target_size
		new_width = int((original_width * target_size) / original_height)
	
	return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

def process_image(filepath, target_size=256, quality=85, size_warning_threshold=2*1024*1024, resize_callback=None):
	try:
		file_size = os.path.getsize(filepath)
		
		with Image.open(filepath) as img:
			original_format = img.format
			
			# Check if file is too large and needs resizing
			should_resize = False
			if file_size > size_warning_threshold:
				if resize_callback:
					should_resize = resize_callback(file_size / (1024 * 1024))
				else:
					should_resize = True
			
			if should_resize:
				# Resize the image while maintaining format
				img_copy = resize_image(img, target_size)
				
				# Save in original format
				img_bytes = io.BytesIO()
				if original_format == 'JPEG':
					img_copy.save(img_bytes, format='JPEG', quality=quality, optimize=True)
					mime_type = 'image/jpeg'
				elif original_format == 'PNG':
					img_copy.save(img_bytes, format='PNG', optimize=True)
					mime_type = 'image/png'
				elif original_format == 'WEBP':
					img_copy.save(img_bytes, format='WEBP', quality=quality, optimize=True)
					mime_type = 'image/webp'
				else:
					# Fallback to JPEG for unknown formats
					if img_copy.mode != 'RGB':
						img_copy = img_copy.convert('RGB')
					img_copy.save(img_bytes, format='JPEG', quality=quality, optimize=True)
					mime_type = 'image/jpeg'
				
				img_bytes.seek(0)
				b64 = base64.b64encode(img_bytes.read()).decode("utf-8")
			else:
				# Use original file as-is
				with open(filepath, 'rb') as f:
					original_data = f.read()
				b64 = base64.b64encode(original_data).decode("utf-8")
				
				if original_format == 'JPEG':
					mime_type = 'image/jpeg'
				elif original_format == 'PNG':
					mime_type = 'image/png'
				elif original_format == 'WEBP':
					mime_type = 'image/webp'
				else:
					mime_type = 'image/jpeg'  # fallback
			
			data_uri = f"data:{mime_type};base64,{b64}"
			return {'success': True, 'data_uri': data_uri}
			
	except Exception as e:
		return {'success': False, 'error': str(e)}