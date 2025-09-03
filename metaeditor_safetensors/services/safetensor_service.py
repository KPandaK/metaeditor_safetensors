"""
Safetensor File Service
=======================

This module provides a service class, `SafetensorService`, for interacting
with .safetensors files. It encapsulates the low-level logic for reading
and writing the file format, keeping it separate from the application's
UI and control flow.
"""

import json
import os
import struct
from typing import Dict, Any, Callable

class SafetensorService:
    """
    Provides methods for reading and writing safetensors file data.
    """

    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        Reads the metadata from a .safetensors file.

        The safetensors format consists of:
        1. A 64-bit unsigned little-endian integer representing the header length.
        2. The JSON header of that length, encoded in UTF-8.
        3. The tensor data.

        This method reads only the header to extract the metadata.

        Args:
            filepath: The path to the .safetensors file.

        Returns:
            A dictionary containing the file's metadata.

        Raises:
            ValueError: If the file is not a valid safetensors file or is corrupt.
            FileNotFoundError: If the file does not exist.
        """
        try:
            with open(filepath, 'rb') as f:
                # 1. Read the 8-byte header length
                header_len_bytes = f.read(8)
                if len(header_len_bytes) != 8:
                    raise ValueError("File is too small to be a valid safetensors file.")
                
                header_len = struct.unpack('<Q', header_len_bytes)[0]

                # 2. Read the JSON header
                header_bytes = f.read(header_len)
                if len(header_bytes) != header_len:
                    raise ValueError("File is truncated or header length is incorrect.")
                
                header_json = json.loads(header_bytes.decode('utf-8'))

                # 3. Extract and return the metadata dictionary
                return header_json.get("__metadata__", {})
        
        except FileNotFoundError:
            raise
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON header: {e}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while reading the file: {e}")

    def write_metadata(self, filepath: str, metadata: Dict[str, Any], progress_callback: Callable[[int], None] = None):
        """
        Writes updated metadata to a .safetensors file by creating a new
        file and then replacing the original. This is a safe way to prevent
        data corruption if the process is interrupted.

        Args:
            filepath: The path to the target .safetensors file.
            metadata: The new metadata dictionary to write.
            progress_callback: A callable (like a signal's emit method) that
                               takes an integer (0-100) to report progress.

        Returns:
            The path to the newly saved file.

        Raises:
            ValueError: If the original file is invalid.
            IOError: If file I/O fails.
        """
        temp_filepath = filepath + ".tmp"
        
        try:
            with open(filepath, 'rb') as f_in, open(temp_filepath, 'wb') as f_out:
                # --- 1. Read and update the header ---
                header_len_bytes = f_in.read(8)
                if len(header_len_bytes) != 8:
                    raise ValueError("Invalid safetensors file.")
                
                header_len = struct.unpack('<Q', header_len_bytes)[0]
                header_bytes = f_in.read(header_len)
                header_json = json.loads(header_bytes.decode('utf-8'))

                # Update the metadata
                header_json["__metadata__"] = metadata

                # --- 2. Write the new header to the temp file ---
                # Use compact JSON formatting to match typical safetensors format
                new_header_bytes = json.dumps(header_json, separators=(',', ':')).encode('utf-8')
                new_header_len = len(new_header_bytes)
                f_out.write(struct.pack('<Q', new_header_len))
                f_out.write(new_header_bytes)

                # --- 3. Stream tensor data from old file to new file ---
                tensor_data_start = 8 + header_len
                f_in.seek(tensor_data_start)

                total_size = os.path.getsize(filepath)
                bytes_copied = 0
                chunk_size = 1024 * 1024 # 1MB chunks
                
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    bytes_copied += len(chunk)
                    if progress_callback and total_size > 0:
                        denominator = total_size - tensor_data_start
                        if denominator > 0:
                            progress = int((bytes_copied / denominator) * 100)
                        else:
                            progress = 100  # If denominator is zero, assume complete
                        progress_callback(min(progress, 100))

            # --- 4. Replace the original file with the temp file ---
            os.replace(temp_filepath, filepath)
            
            if progress_callback:
                progress_callback(100)

            return filepath

        except Exception as e:
            # Clean up the temp file on error
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise IOError(f"Failed to save file: {e}")
        finally:
            # Final cleanup just in case
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass

