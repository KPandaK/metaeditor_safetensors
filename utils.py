import hashlib

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