"""
Safetensors file reader

The safetensors format is:
1. Header length (8 bytes, little-endian uint64)
2. JSON header (header_length bytes)
3. Tensor data (rest of file)

The JSON header contains:
- Metadata in "__metadata__" key
- Tensor info with keys like "layer.weight": {"dtype": "F32", "shape": [1024, 768], "data_offsets": [0, 3145728]}
"""

import json
import struct
from typing import Dict, Any

def read_safetensors_metadata(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'rb') as f:
        # Read header length (first 8 bytes, little-endian uint64)
        header_length_bytes = f.read(8)
        if len(header_length_bytes) != 8:
            raise ValueError("File too small to be a valid safetensors file")
        
        header_length = struct.unpack('<Q', header_length_bytes)[0]
        
        # Read the JSON header
        header_bytes = f.read(header_length)
        if len(header_bytes) != header_length:
            raise ValueError("File truncated - cannot read full header")
        
        # Parse JSON header
        try:
            header = json.loads(header_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid JSON in safetensors header: {e}")
        
        # Extract and return only metadata
        return header.get("__metadata__", {})