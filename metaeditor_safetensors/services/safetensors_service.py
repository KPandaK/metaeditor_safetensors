import hashlib
import json
import logging
import os
import struct
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QThread

from .load_worker import LoadWorker
from .save_worker import SaveWorker

logger = logging.getLogger(__name__)


class SafetensorsService:
    def __init__(self) -> None:
        self._save_worker: Optional[SaveWorker] = None
        self._worker_thread: Optional[QThread] = None
        self._load_worker: Optional[LoadWorker] = None
        self._load_thread: Optional[QThread] = None

    def read_metadata(
        self,
        filepath: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Dict[str, Any]:
        if progress_callback:
            progress_callback(0)

        try:
            with open(filepath, "rb") as f:
                header_len_bytes = f.read(8)
                if len(header_len_bytes) != 8:
                    raise ValueError("Invalid safetensors file.")

                header_len = struct.unpack("<Q", header_len_bytes)[0]

                header_bytes = f.read(header_len)
                if len(header_bytes) != header_len:
                    raise ValueError("File is truncated or header length is incorrect.")

                header_json = json.loads(header_bytes.decode("utf-8"))
                metadata = header_json.get("__metadata__", {})

            try:
                file_hash = self._calculate_hash(
                    filepath,
                    header_len,
                    progress_callback=progress_callback,
                )
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
                if progress_callback:
                    progress_callback(100)

            if progress_callback:
                progress_callback(100)

            return dict(metadata)

        except FileNotFoundError:
            raise
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse JSON header: {exc}") from exc
        except Exception as exc:
            raise ValueError(
                f"An unexpected error occurred while reading the file: {exc}"
            ) from exc

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
                header_len_bytes = f_in.read(8)
                if len(header_len_bytes) != 8:
                    raise ValueError("Invalid safetensors file.")

                header_len = struct.unpack("<Q", header_len_bytes)[0]
                header_bytes = f_in.read(header_len)
                header_json = json.loads(header_bytes.decode("utf-8"))

                header_json["__metadata__"] = metadata

                new_header_bytes = json.dumps(
                    header_json, separators=(",", ":")
                ).encode("utf-8")
                new_header_len = len(new_header_bytes)
                f_out.write(struct.pack("<Q", new_header_len))
                f_out.write(new_header_bytes)

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
                            progress = 100
                        progress_callback(min(progress, 100))

            os.replace(temp_filepath, filepath)

            if progress_callback is not None:
                progress_callback(100)

            return filepath

        except Exception as exc:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise IOError(f"Failed to save file: {exc}") from exc
        finally:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass

    def _calculate_hash(
        self,
        filepath: str,
        header_len: Optional[int] = None,
        *,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> str:
        if header_len is None:
            with open(filepath, "rb") as f:
                header_len_bytes = f.read(8)
                if len(header_len_bytes) != 8:
                    raise ValueError("Invalid safetensors file.")
                header_len = struct.unpack("<Q", header_len_bytes)[0]

        assert header_len is not None
        hasher = hashlib.sha256()
        total_size = os.path.getsize(filepath)
        tensor_data_start = 8 + header_len
        data_size = max(total_size - tensor_data_start, 0)
        hashed_bytes = 0
        chunk_size = 4 * 1024 * 1024

        with open(filepath, "rb") as f:
            f.seek(tensor_data_start)
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
                hashed_bytes += len(chunk)
                if progress_callback and data_size > 0:
                    progress = int((hashed_bytes / data_size) * 100)
                    progress_callback(min(progress, 100))

        if progress_callback and data_size == 0:
            progress_callback(100)

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

        if progress_callback:
            self._save_worker.progress.connect(progress_callback)
        if success_callback:
            self._save_worker.finished.connect(success_callback)
        if error_callback:
            self._save_worker.error.connect(error_callback)

        self._worker_thread.started.connect(self._save_worker.run)

        self._save_worker.finished.connect(self._worker_thread.quit)
        self._save_worker.error.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._on_save_finished)

        self._worker_thread.start()
        return True

    def read_metadata_async(
        self,
        filepath: str,
        *,
        progress_callback: Optional[Callable[[int], None]] = None,
        success_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        if self.is_loading():
            return False

        if progress_callback:
            progress_callback(0)

        self._load_worker = LoadWorker(self, filepath)
        self._load_thread = QThread()
        self._load_worker.moveToThread(self._load_thread)

        if progress_callback:
            self._load_worker.progress.connect(progress_callback)
        if success_callback:
            self._load_worker.finished.connect(success_callback)
        if error_callback:
            self._load_worker.error.connect(error_callback)

        self._load_thread.started.connect(self._load_worker.run)

        self._load_worker.finished.connect(self._load_thread.quit)
        self._load_worker.error.connect(self._load_thread.quit)
        self._load_thread.finished.connect(self._on_load_finished)

        self._load_thread.start()
        return True

    def is_saving(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.isRunning()

    def is_loading(self) -> bool:
        return self._load_thread is not None and self._load_thread.isRunning()

    def _on_save_finished(self) -> None:
        if self._worker_thread:
            self._worker_thread.wait()
            self._worker_thread = None
        self._save_worker = None

    def _on_load_finished(self) -> None:
        if self._load_thread:
            self._load_thread.wait()
            self._load_thread = None
        self._load_worker = None

    def shutdown(self) -> None:
        if self._load_thread and self._load_thread.isRunning():
            self._load_thread.quit()
            self._load_thread.wait(5000)
        self._load_thread = None
        self._load_worker = None

        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(5000)
        self._worker_thread = None
        self._save_worker = None
