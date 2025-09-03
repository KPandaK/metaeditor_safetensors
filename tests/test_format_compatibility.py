import unittest
import os
import tempfile
import shutil
import numpy as np
from safetensors.numpy import save_file, load_file
from safetensors import safe_open
from metaeditor_safetensors.services.safetensor_service import SafetensorService

class TestFormatCompatibility(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()