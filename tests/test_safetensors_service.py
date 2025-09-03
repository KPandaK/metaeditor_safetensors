import unittest
import os
import tempfile
import shutil
import numpy as np
from unittest.mock import patch, mock_open
from safetensors.numpy import save_file, load_file
from safetensors import safe_open
from metaeditor_safetensors.services.safetensors_service import SafetensorService

class TestSafetensorsService(unittest.TestCase):
    """
    Tests that our custom SafetensorService can correctly read and write files
    compatible with the official safetensors library.
    """

    def setUp(self):
        """Set up a temporary directory and common data for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.service = SafetensorService()
        self.dummy_tensors = {
            "weight1": np.array([1, 2, 3]),
            "weight2": np.array([[4, 5], [6, 7]], dtype=np.float32)
        }
        self.dummy_metadata = {
            "author": "Test Suite",
            "license": "MIT",
            "description": "A file generated for compatibility testing."
        }
        self.test_filepath = os.path.join(self.test_dir, "format_test.safetensors")

    def tearDown(self):
        """Remove the temporary directory after tests."""
        shutil.rmtree(self.test_dir)

    def test_read_compatibility(self):
        """
        Verify metadata reader is compatible with the safetensors file format.
        """
        # Save a file using the official library
        save_file(self.dummy_tensors, self.test_filepath, metadata=self.dummy_metadata)

        # Read the metadata using our custom service
        read_metadata = self.service.read_metadata(self.test_filepath)

        # Assert that the metadata is identical
        self.assertEqual(read_metadata, self.dummy_metadata,
                         "READ FAILED: The metadata read does not match the safetensors file format.")

    def test_write_equivalency(self):
        """
        Verify metadata writer is compatible with the numpy save function.
        """
        # 1. Define paths for the two files we will compare
        their_path = os.path.join(self.test_dir, "theirs.safetensors")
        our_path = os.path.join(self.test_dir, "ours.safetensors")

        # 2. Create the first file using the official library
        save_file(self.dummy_tensors, their_path, metadata=self.dummy_metadata)

        # 3. Create the second file using our service.
        # Our service modifies an existing file, so we first create a base
        # file (it can be a copy of the official one or a new one).
        shutil.copy(their_path, our_path)
        # Now, "save" the metadata into it using our service.
        self.service.write_metadata(our_path, self.dummy_metadata)

        # 4. Load both files back using the official library
        tensors_theirs = load_file(their_path)
        tensors_ours = load_file(our_path)
        
        # Read metadata separately using safe_open
        with safe_open(their_path, framework="numpy") as f:
            metadata_theirs = f.metadata()

        with safe_open(our_path, framework="numpy") as f:
            metadata_ours = f.metadata()

        # 5. Assert that metadata is identical
        self.assertEqual(metadata_theirs, metadata_ours,
                         "WRITE FAILED: The metadata does not match the numpy library's output.")

        # 6. Assert that tensor data is identical
        self.assertEqual(len(tensors_theirs), len(tensors_ours),
                         "WRITE FAILED: The number of tensors changed between numpy's save and our save.")
        for key, their_tensor in tensors_theirs.items():
            self.assertIn(key, tensors_ours,
                          f"WRITE FAILED: Tensor '{key}' is missing from our service's output.")
            our_tensor = tensors_ours[key]
            np.testing.assert_array_equal(their_tensor, our_tensor,
                                          f"WRITE FAILED: Tensor '{key}' was corrupted by our service's save operation.")

    def test_read_metadata_file_not_found(self):
        """Test FileNotFoundError handling when file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            self.service.read_metadata("nonexistent_file.safetensors")

    def test_read_metadata_file_too_small(self):
        """Test file too small error handling."""
        # Create a file with less than 8 bytes
        tiny_file = os.path.join(self.test_dir, "tiny.safetensors")
        with open(tiny_file, 'wb') as f:
            f.write(b"tiny")  # Only 4 bytes
        
        with self.assertRaises(ValueError) as context:
            self.service.read_metadata(tiny_file)
        self.assertIn("too small", str(context.exception))

    def test_read_metadata_invalid_header_length(self):
        """Test when header length field doesn't equal 8 bytes."""
        invalid_header_file = os.path.join(self.test_dir, "invalid_header.safetensors")
        with open(invalid_header_file, 'wb') as f:
            # Write only 6 bytes instead of 8 for the header length
            f.write(b"123456")
        
        with self.assertRaises(ValueError) as context:
            self.service.read_metadata(invalid_header_file)
        self.assertIn("too small", str(context.exception))

    def test_write_metadata_invalid_header_length(self):
        """Test write_metadata when header length field doesn't equal 8 bytes during write operation."""
        invalid_header_file = os.path.join(self.test_dir, "invalid_header_write.safetensors")
        with open(invalid_header_file, 'wb') as f:
            # Write only 6 bytes instead of 8 for the header length
            f.write(b"123456")
        
        with self.assertRaises(IOError) as context:
            self.service.write_metadata(invalid_header_file, {"new": "data"})
        self.assertIn("Failed to save file", str(context.exception))
        self.assertIn("Invalid safetensors file", str(context.exception))

    def test_read_metadata_truncated_header(self):
        """Test truncated header error handling."""
        truncated_file = os.path.join(self.test_dir, "truncated.safetensors")
        with open(truncated_file, 'wb') as f:
            # Write valid 8-byte header length indicating 100 bytes
            f.write((100).to_bytes(8, 'little'))
            # But only write 10 bytes instead of 100
            f.write(b"short_data")
        
        with self.assertRaises(ValueError) as context:
            self.service.read_metadata(truncated_file)
        self.assertIn("truncated", str(context.exception))

    def test_read_metadata_invalid_json(self):
        """Test JSON decode error handling."""
        invalid_json_file = os.path.join(self.test_dir, "invalid_json.safetensors")
        invalid_json = b"invalid json content"
        
        with open(invalid_json_file, 'wb') as f:
            # Write header length
            f.write(len(invalid_json).to_bytes(8, 'little'))
            # Write invalid JSON
            f.write(invalid_json)
        
        with self.assertRaises(ValueError) as context:
            self.service.read_metadata(invalid_json_file)
        self.assertIn("Failed to parse JSON", str(context.exception))

    def test_write_metadata_with_progress_callback(self):
        """Test progress callback functionality."""
        # Create initial file
        save_file(self.dummy_tensors, self.test_filepath, metadata=self.dummy_metadata)
        
        progress_calls = []
        def progress_callback(progress):
            progress_calls.append(progress)
        
        # Test with callback
        result = self.service.write_metadata(self.test_filepath, {"new": "data"}, progress_callback)
        
        # Verify progress was called and ended at 100%
        self.assertTrue(len(progress_calls) > 0)
        self.assertEqual(progress_calls[-1], 100)
        self.assertEqual(result, self.test_filepath)

    def test_write_metadata_cleanup_on_error(self):
        """Test temp file cleanup when write fails."""
        # Create initial file
        save_file(self.dummy_tensors, self.test_filepath, metadata=self.dummy_metadata)
        temp_file = self.test_filepath + ".tmp"
        
        # Mock to cause an error during file operations
        with patch('builtins.open', side_effect=IOError("Simulated write error")):
            with self.assertRaises(IOError) as context:
                self.service.write_metadata(self.test_filepath, {"new": "data"})
            self.assertIn("Failed to save file", str(context.exception))
        
        # Verify temp file was cleaned up
        self.assertFalse(os.path.exists(temp_file))

    def test_read_metadata_unexpected_error(self):
        """Test general exception handling in read_metadata."""
        # Create valid file first
        save_file(self.dummy_tensors, self.test_filepath, metadata=self.dummy_metadata)
        
        # Mock struct.unpack to raise an unexpected error
        with patch('metaeditor_safetensors.services.safetensors_service.struct.unpack', 
                   side_effect=RuntimeError("Unexpected error")):
            with self.assertRaises(ValueError) as context:
                self.service.read_metadata(self.test_filepath)
            self.assertIn("unexpected error occurred", str(context.exception))

if __name__ == '__main__':
    unittest.main()