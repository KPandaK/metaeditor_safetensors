import unittest
import tempfile
import os
from datetime import datetime, timezone
import sys
import hashlib

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from metaeditor_safetensors.utils import compute_sha256, utc_to_local, local_to_utc
from metaeditor_safetensors.commands.set_thumbnail import SetThumbnailCommand


class MockEditor:
    """Mock editor for testing commands."""
    def update_status(self, message):
        pass
    
    def clear_status(self):
        pass


class TestUtils(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_editor = MockEditor()
        self.command = SetThumbnailCommand(self.mock_editor)
    
    def test_compute_sha256(self):
        """Test SHA256 computation on a mock safetensors file"""
        # Create a temporary file that mimics safetensors structure
        with tempfile.NamedTemporaryFile(delete=False, suffix='.safetensors') as tmp:
            # Write a minimal safetensors-like structure
            # 8 bytes for header length + some header + some tensor data
            header = b'{"test": "metadata"}'
            header_len = len(header)
            tmp.write(header_len.to_bytes(8, 'little'))  # Header length
            tmp.write(header)  # Header
            tensor_data = b'fake_tensor_data_for_testing'
            tmp.write(tensor_data)  # Tensor data
            tmp.flush()
            tmp_name = tmp.name
        
        try:
            # Compute SHA256
            result = compute_sha256(tmp_name)
            
            # Verify it starts with 0x and is the right length
            self.assertTrue(result.startswith('0x'))
            self.assertEqual(len(result), 66)  # 0x + 64 hex chars
            
            # Verify it matches manual computation
            expected_hash = hashlib.sha256(tensor_data).hexdigest()
            self.assertEqual(result, f"0x{expected_hash}")
            
        finally:
            # Clean up - file is closed now so this should work
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
    
    def test_utc_to_local_conversion(self):
        """Test UTC to local time conversion"""
        # Test with a known UTC time
        utc_str = "2024-01-15T12:30:45Z"
        local_dt = utc_to_local(utc_str)
        
        # Verify it's a datetime object
        self.assertIsInstance(local_dt, datetime)
        
        # Test with different UTC format
        utc_str2 = "2024-01-15T12:30:45+00:00"
        local_dt2 = utc_to_local(utc_str2)
        self.assertIsInstance(local_dt2, datetime)
    
    def test_local_to_utc_conversion(self):
        """Test local to UTC time conversion"""
        from datetime import date
        
        # Test conversion
        test_date = date(2024, 1, 15)
        hour = "14"
        minute = "30"
        
        result = local_to_utc(test_date, hour, minute)
        
        # Verify format
        self.assertTrue(result.endswith('Z'))
        self.assertIn('2024-01-15T', result)
    
    def test_roundtrip_time_conversion(self):
        """Test that UTC->local->UTC preserves the original time"""
        original_utc = "2024-06-15T14:30:00Z"
        
        # Convert to local
        local_dt = utc_to_local(original_utc)
        
        # Convert back to UTC
        result_utc = local_to_utc(
            local_dt.date(),
            local_dt.strftime("%H"),
            local_dt.strftime("%M")
        )
        
        # Should be close (might differ by seconds due to rounding)
        self.assertTrue(result_utc.startswith("2024-06-15T14:30:"))

    def test_resize_image(self):
        """Test image resizing while maintaining aspect ratio"""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("PIL not available for testing")
        
        # Create a test image (landscape 400x200)
        img = Image.new('RGB', (400, 200), color='red')
        
        # Resize to 100px target
        resized = self.command._resize_image(img, 100)

        # Should be 100x50 (width was the longer dimension)
        self.assertEqual(resized.size, (100, 50))
        
        # Test portrait image (200x400)
        img_portrait = Image.new('RGB', (200, 400), color='blue')
        resized_portrait = self.command._resize_image(img_portrait, 100)

        # Should be 50x100 (height was the longer dimension)
        self.assertEqual(resized_portrait.size, (50, 100))
        
        # Test square image (300x300)
        img_square = Image.new('RGB', (300, 300), color='green')
        resized_square = self.command._resize_image(img_square, 150)

        # Should be 150x150
        self.assertEqual(resized_square.size, (150, 150))

    def test_process_image_small(self):
        """Test processing a small image file that doesn't need resizing"""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("PIL not available for testing")
        
        # Create a small test image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(tmp, format='PNG')
            tmp.flush()
            tmp_name = tmp.name
        
        try:
            # Process the image
            result = self.command._process_image(tmp_name, target_size=256)
            
            # Should succeed
            self.assertTrue(result['success'])
            self.assertIn('data_uri', result)
            # PNG should stay PNG format
            self.assertTrue(result['data_uri'].startswith('data:image/png;base64,'))
            
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def test_process_image_invalid_file(self):
        """Test processing an invalid image file"""
        # Create a non-image file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp.write(b'This is not an image')
            tmp.flush()
            tmp_name = tmp.name
        
        try:
            # Process the file
            result = self.command._process_image(tmp_name)
            
            # Should fail gracefully
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def test_process_image_format_preservation(self):
        """Test that different image formats are preserved"""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("PIL not available for testing")
        
        formats_to_test = [
            ('PNG', 'data:image/png;base64,'),
            ('JPEG', 'data:image/jpeg;base64,'),
        ]
        
        for img_format, expected_mime in formats_to_test:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{img_format.lower()}') as tmp:
                img = Image.new('RGB', (50, 50), color='blue')
                img.save(tmp, format=img_format)
                tmp.flush()
                tmp_name = tmp.name
            
            try:
                result = self.command._process_image(tmp_name, target_size=256)
                
                self.assertTrue(result['success'], f"Failed for {img_format}")
                self.assertIn('data_uri', result)
                self.assertTrue(result['data_uri'].startswith(expected_mime), 
                              f"Expected {expected_mime} for {img_format}, got {result['data_uri'][:30]}")
                
            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)


if __name__ == '__main__':
    unittest.main()
