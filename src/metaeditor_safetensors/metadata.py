import json
import os
import gc
import logging
from safetensors import safe_open
from safetensors.torch import save_file

logger = logging.getLogger(__name__)

def update_metadata(filepath, new_metadata, tmp_path, progress_callback=None):

    def update_progress(message):
        if progress_callback:
            progress_callback(message)
        logger.info(message)
    
    try:
        update_progress("Reading file header...")
        
        # Read the original file header to understand its structure
        with open(filepath, 'rb') as f:
            # Read header length (first 8 bytes)
            header_len_bytes = f.read(8)
            if len(header_len_bytes) != 8:
                raise ValueError("Invalid safetensors file: header length missing")
                
            header_len = int.from_bytes(header_len_bytes, byteorder='little')
            
            # Read the JSON header
            header_bytes = f.read(header_len)
            if len(header_bytes) != header_len:
                raise ValueError("Invalid safetensors file: header truncated")
                
            header_json = json.loads(header_bytes.decode('utf-8'))
            
            # The rest is tensor data - we'll copy this unchanged
            tensor_data_start = f.tell()
            file_size = os.path.getsize(filepath)
        
        # Update the metadata in the header
        if '__metadata__' not in header_json:
            header_json['__metadata__'] = {}
        
        # Merge our new metadata
        header_json['__metadata__'].update(new_metadata)
        
        # Create the new header
        new_header_str = json.dumps(header_json, separators=(',', ':'))
        new_header_bytes = new_header_str.encode('utf-8')
        new_header_len = len(new_header_bytes)
        
        update_progress("Creating file...")
        
        # Create new file with updated header and original tensor data
        with open(filepath, 'rb') as src, open(tmp_path, 'wb') as dst:
            # Write new header length
            dst.write(new_header_len.to_bytes(8, byteorder='little'))
            
            # Write new header
            dst.write(new_header_bytes)
            
            # Copy tensor data in chunks
            src.seek(tensor_data_start)
            
            update_progress("Copying tensor data...")
            
            chunk_size = 32 * 1024 * 1024  # 32MB chunks
            copied = 0
            file_size_remaining = file_size - tensor_data_start
            last_progress_reported = -1
            
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                
                dst.write(chunk)
                copied += len(chunk)
                
                # Show progress every 2% for detailed feedback
                if file_size_remaining > 0:
                    progress = (copied / file_size_remaining) * 100
                    progress_int = int(progress / 2) * 2  # Round to nearest 2%
                    
                    if progress_int != last_progress_reported and progress_int % 2 == 0 and progress_int > 0:
                        update_progress(f"Copying tensor data: {progress_int}%")
                        last_progress_reported = progress_int
        
        update_progress("File update complete")
        return True
        
    except Exception as e:
        logger.warning(f"Optimized method failed: {e}")
        return False


def update_metadata_fallback(filepath, new_metadata, tmp_path, progress_callback=None):
    def update_progress(message):
        if progress_callback:
            progress_callback(message)
        logger.info(message)
    
    update_progress("Using standard method...")
    logger.warning("Using standard tensor loading method")
    
    # Load all tensors (required by standard safetensors API)
    with safe_open(filepath, framework="pt") as f:
        tensors = {}
        keys = list(f.keys())
        total = len(keys)
        
        for i, key in enumerate(keys):
            # Update progress every 50 tensors or every 10% of total, whichever is less frequent
            if i % max(50, total // 10) == 0 or i == total - 1:
                progress = ((i + 1) / total) * 100
                update_progress(f"Loading tensors: {progress:.0f}% ({i+1}/{total})")
            tensors[key] = f.get_tensor(key)
    
    # Save with new metadata
    update_progress("Saving with updated metadata...")
    save_file(tensors, tmp_path, metadata=new_metadata)
    
    # Clean up memory
    tensors.clear()
    gc.collect()
    
    update_progress("Standard method completed")


def update_safetensors_metadata(filepath, new_metadata, tmp_path, progress_callback=None):
    # Try the optimized approach first
    if update_metadata(filepath, new_metadata, tmp_path, progress_callback):
        return "optimized"
    
    # Fall back to the traditional approach
    update_metadata_fallback(filepath, new_metadata, tmp_path, progress_callback)
    return "fallback"
