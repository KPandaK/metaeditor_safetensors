import hashlib
import json
import logging
import os
import struct
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QThread

from .save_worker import SaveWorker

logger = logging.getLogger(__name__)


class SafetensorsService:
    def __init__(self):
        self._save_worker: Optional[SaveWorker] = None
        self._worker_thread: Optional[QThread] = None

    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        try:
            with open(filepath, "rb") as f:
                # Read the 8-byte header length
                header_len_bytes = f.read(8)
                if len(header_len_bytes) != 8:
                    raise ValueError("Invalid safetensors file.")

                header_len = struct.unpack("<Q", header_len_bytes)[0]

                # Read the JSON header
                header_bytes = f.read(header_len)
                if len(header_bytes) != header_len:
                    raise ValueError("File is truncated or header length is incorrect.")

                header_json = json.loads(header_bytes.decode("utf-8"))

                # Extract and return the metadata dictionary
                metadata = header_json.get("__metadata__", {})

            # Compute and add the file hash to the metadata
            try:
                file_hash = self._calculate_hash(filepath)
                # Compare with existing hash if present
                if "modelspec.hash_sha256" in metadata:
                    existing_hash = metadata["modelspec.hash_sha256"]
                    if existing_hash != file_hash:
                        logger.warning(
                            "Hash mismatch: existing %s vs computed %s",
                            existing_hash,
                            file_hash,
                        )
                metadata["modelspec.hash_sha256"] = file_hash
            except Exception as hash_error:
                logger.warning("Could not compute hash for file: %s", hash_error)

            return dict(metadata)

        except FileNotFoundError:
            raise
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON header: {e}")
        except Exception as e:
            raise ValueError(
                f"An unexpected error occurred while reading the file: {e}"
            )

    def write_metadata(
        self,
        filepath: str,
        metadata: Dict[str, Any],
        progress_callback: Optional[Callable[[int], None]] = None,
        source_filepath: Optional[str] = None,
    ) -> str:
        temp_filepath = filepath + ".tmp"
        source_file = source_filepath or filepath

        try:
            with open(source_file, "rb") as f_in, open(temp_filepath, "wb") as f_out:
                # Read and update the header
                header_len_bytes = f_in.read(8)
                if len(header_len_bytes) != 8:
                    raise ValueError("Invalid safetensors file.")

                header_len = struct.unpack("<Q", header_len_bytes)[0]
                header_bytes = f_in.read(header_len)
                header_json = json.loads(header_bytes.decode("utf-8"))

                # Update the metadata
                header_json["__metadata__"] = metadata

                # Use compact JSON formatting to match typical safetensors format
                new_header_bytes = json.dumps(
                    header_json, separators=(",", ":")
                ).encode("utf-8")
                new_header_len = len(new_header_bytes)
                f_out.write(struct.pack("<Q", new_header_len))
                f_out.write(new_header_bytes)

                # Stream tensor data from old file to new file
                tensor_data_start = 8 + header_len
                f_in.seek(tensor_data_start)

                total_size = os.path.getsize(source_file)
                bytes_copied = 0
                chunk_size = 1024 * 1024

                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    bytes_copied += len(chunk)
                    if progress_callback is not None and total_size > 0:
                        denominator = total_size - tensor_data_start
                        if denominator > 0:
                            progress = int((bytes_copied / denominator) * 100)
                        else:
                            # If denominator is zero, assume complete.
                            progress = 100
                        progress_callback(min(progress, 100))

            # Replace the original file with the temp file
            os.replace(temp_filepath, filepath)

            if progress_callback is not None:
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

    def _calculate_hash(self, filepath: str) -> str:
        hasher = hashlib.sha256()

        with open(filepath, "rb") as f:
            # Read the header size
            header_len_bytes = f.read(8)
            if len(header_len_bytes) != 8:
                raise ValueError("Invalid safetensors file.")

            header_len = struct.unpack("<Q", header_len_bytes)[0]

            # Skip the header
            f.seek(8 + header_len)

            # 4MB chunks
            CHUNK_SIZE = 4 * 1024 * 1024

            # Read the tensor data and hash it
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                hasher.update(chunk)

            # Return hash in ModelSpec format (0x prefix + lowercase hex)
            return f"0x{hasher.hexdigest().lower()}"

    def write_metadata_async(
        self,
        filepath: str,
        metadata: Dict[str, Any],
        progress_callback: Optional[Callable[[int], None]] = None,
        success_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        source_filepath: Optional[str] = None,
    ) -> bool:
        if self.is_saving():
            return False

        self._save_worker = SaveWorker(self, filepath, metadata, source_filepath)
        self._worker_thread = QThread()
        self._save_worker.moveToThread(self._worker_thread)

        # Connect signals to callbacks
        if progress_callback:
            self._save_worker.progress.connect(progress_callback)
        if success_callback:
            self._save_worker.finished.connect(success_callback)
        if error_callback:
            self._save_worker.error.connect(error_callback)

        # Connect thread started signal to worker run method
        self._worker_thread.started.connect(self._save_worker.run)

        # Connect cleanup - use queued connections to avoid blocking
        self._save_worker.finished.connect(self._worker_thread.quit)
        self._save_worker.error.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._on_save_finished)

        # Start thread
        self._worker_thread.start()
        return True

    def is_saving(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.isRunning()

    def _on_save_finished(self):
        if self._worker_thread:
            self._worker_thread.wait()
            self._worker_thread = None
        self._save_worker = None

    def shutdown(self):
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(5000)  # Wait up to 5 seconds
        self._worker_thread = None
        self._save_worker = None
