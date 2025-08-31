import os
import sys
import tempfile
import shutil
import unittest
import json

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from metaeditor_safetensors.metadata import update_safetensors_metadata

class TestMetadataOptimizer(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create a minimal valid safetensors file for testing
        self.test_file = os.path.join(self.test_dir, "test.safetensors")
        
        # Create a simple safetensors file structure
        # Header with basic tensor info
        header_data = {
            "tensor1": {"dtype": "F32", "shape": [2, 3], "data_offsets": [0, 24]},
            "__metadata__": {"test_key": "original_value"}
        }
        header_json = json.dumps(header_data, separators=(',', ':'))
        header_bytes = header_json.encode('utf-8')
        header_len = len(header_bytes)
        
        # Dummy tensor data (24 bytes for a 2x3 float32 tensor)
        tensor_data = b'\x00' * 24
        
        with open(self.test_file, 'wb') as f:
            f.write(header_len.to_bytes(8, byteorder='little'))
            f.write(header_bytes)
            f.write(tensor_data)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_update_metadata_optimized(self):
        """Test that metadata update works correctly."""
        # New metadata to add
        new_metadata = {
            "modelspec.architecture": "test_model",
            "modelspec.author": "test_author"
        }
        
        tmp_file = os.path.join(self.test_dir, "test_updated.safetensors")
        
        # Update metadata
        method_used = update_safetensors_metadata(
            self.test_file,
            new_metadata,
            tmp_file
        )
        
        # Should use optimized method
        self.assertEqual(method_used, "optimized")
        
        # Verify the file was created
        self.assertTrue(os.path.exists(tmp_file))
        
        # Verify the metadata was updated correctly
        with open(tmp_file, 'rb') as f:
            # Read header length
            header_len = int.from_bytes(f.read(8), byteorder='little')
            
            # Read header
            header_bytes = f.read(header_len)
            header_data = json.loads(header_bytes.decode('utf-8'))
            
            # Check that metadata was merged correctly
            metadata = header_data.get('__metadata__', {})
            self.assertEqual(metadata['test_key'], 'original_value')  # Original should be preserved
            self.assertEqual(metadata['modelspec.architecture'], 'test_model')
            self.assertEqual(metadata['modelspec.author'], 'test_author')
    
    def test_progress_callback(self):
        """Test that progress callback is called during operation."""
        progress_messages = []
        
        def capture_progress(message):
            progress_messages.append(message)
        
        new_metadata = {"test_progress": "value"}
        tmp_file = os.path.join(self.test_dir, "test_progress.safetensors")
        
        update_safetensors_metadata(
            self.test_file,
            new_metadata,
            tmp_file,
            progress_callback=capture_progress
        )
        
        # Should have received progress messages
        self.assertGreater(len(progress_messages), 0)
        self.assertTrue(any("Reading file header" in msg for msg in progress_messages))
        self.assertTrue(any("Creating file" in msg for msg in progress_messages))
        self.assertTrue(any("File update complete" in msg for msg in progress_messages))
    
    def test_metadata_merge_preserves_existing(self):
        """Test that existing metadata is preserved when adding new fields."""
        # Add more metadata to existing
        existing_metadata = {
            "existing_field": "should_remain",
            "another_field": "also_remain"
        }
        
        # Create file with existing metadata
        header_data = {
            "tensor1": {"dtype": "F32", "shape": [2, 3], "data_offsets": [0, 24]},
            "__metadata__": existing_metadata
        }
        header_json = json.dumps(header_data, separators=(',', ':'))
        header_bytes = header_json.encode('utf-8')
        header_len = len(header_bytes)
        
        test_file_with_metadata = os.path.join(self.test_dir, "test_with_metadata.safetensors")
        with open(test_file_with_metadata, 'wb') as f:
            f.write(header_len.to_bytes(8, byteorder='little'))
            f.write(header_bytes)
            f.write(b'\x00' * 24)  # tensor data
        
        # Add new metadata
        new_metadata = {"new_field": "new_value"}
        tmp_file = os.path.join(self.test_dir, "test_merged.safetensors")
        
        update_safetensors_metadata(test_file_with_metadata, new_metadata, tmp_file)
        
        # Verify all metadata is present
        with open(tmp_file, 'rb') as f:
            header_len = int.from_bytes(f.read(8), byteorder='little')
            header_bytes = f.read(header_len)
            header_data = json.loads(header_bytes.decode('utf-8'))
            metadata = header_data.get('__metadata__', {})
            
            # All fields should be present
            self.assertEqual(metadata['existing_field'], 'should_remain')
            self.assertEqual(metadata['another_field'], 'also_remain')
            self.assertEqual(metadata['new_field'], 'new_value')
    
    def test_file_size_unchanged_for_tensor_data(self):
        """Test that tensor data remains unchanged in size."""
        new_metadata = {"test": "value"}
        tmp_file = os.path.join(self.test_dir, "test_updated.safetensors")
        
        update_safetensors_metadata(self.test_file, new_metadata, tmp_file)
        
        # The tensor data portion should be exactly the same
        with open(self.test_file, 'rb') as orig:
            orig_header_len = int.from_bytes(orig.read(8), byteorder='little')
            orig.seek(8 + orig_header_len)
            orig_tensor_data = orig.read()
        
        with open(tmp_file, 'rb') as new:
            new_header_len = int.from_bytes(new.read(8), byteorder='little')
            new.seek(8 + new_header_len)
            new_tensor_data = new.read()
        
        # Tensor data should be identical
        self.assertEqual(orig_tensor_data, new_tensor_data)
    
    def test_empty_metadata_creation(self):
        """Test that __metadata__ section is created if it doesn't exist."""
        # Create file without __metadata__
        header_data = {
            "tensor1": {"dtype": "F32", "shape": [2, 3], "data_offsets": [0, 24]}
            # No __metadata__ section
        }
        header_json = json.dumps(header_data, separators=(',', ':'))
        header_bytes = header_json.encode('utf-8')
        header_len = len(header_bytes)
        
        no_metadata_file = os.path.join(self.test_dir, "no_metadata.safetensors")
        with open(no_metadata_file, 'wb') as f:
            f.write(header_len.to_bytes(8, byteorder='little'))
            f.write(header_bytes)
            f.write(b'\x00' * 24)
        
        # Add metadata to file without __metadata__
        new_metadata = {"first_metadata": "first_value"}
        tmp_file = os.path.join(self.test_dir, "first_metadata.safetensors")
        
        update_safetensors_metadata(no_metadata_file, new_metadata, tmp_file)
        
        # Verify metadata was added
        with open(tmp_file, 'rb') as f:
            header_len = int.from_bytes(f.read(8), byteorder='little')
            header_bytes = f.read(header_len)
            header_data = json.loads(header_bytes.decode('utf-8'))
            
            self.assertIn('__metadata__', header_data)
            metadata = header_data['__metadata__']
            self.assertEqual(metadata['first_metadata'], 'first_value')


if __name__ == '__main__':
    unittest.main()
