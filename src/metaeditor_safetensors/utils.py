import hashlib
from tzlocal import get_localzone
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def compute_sha256(filepath):
	with open(filepath, "rb") as f:
		header_len = int.from_bytes(f.read(8), "little")
		f.seek(8 + header_len)
		tensor_bytes = f.read()
	sha = hashlib.sha256(tensor_bytes).hexdigest()
	return "0x" + sha.lower()

def merge_metadata(existing, updates):
	merged = existing.copy()
	merged.update(updates)
	return merged

def utc_to_local(utc_str):
	# Safeguard: ensure UTC string ends with 'Z' or '+00:00'
	if not (utc_str.endswith('Z') or utc_str.endswith('+00:00')):
		utc_str = utc_str + 'Z'
	local_tz = get_localzone()
	dt_utc = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
	local_dt = dt_utc.astimezone(local_tz)
	return local_dt

def local_to_utc(date_val, hour_val, minute_val):
	local_tz = get_localzone()
	local_dt = datetime.strptime(f"{date_val} {hour_val}:{minute_val}", "%Y-%m-%d %H:%M")
	local_dt = local_dt.replace(tzinfo=ZoneInfo(str(local_tz)))
	dt_utc = local_dt.astimezone(timezone.utc)
	utc_str = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
	return utc_str