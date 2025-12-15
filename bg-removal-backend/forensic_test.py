#!/usr/bin/env python3
"""
Forensic Validation Test for Free Preview Background Removal
Tests 10 real-world images and logs detailed metrics for each image.

Metrics tracked:
- Image type detection
- Mask nonzero ratio AFTER recovery
- Whether emergency mask was applied
- Composite execution path
- Alpha min/max/nonzero
- Confirms no raw output_image is returned
"""

import requests
import base64
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import time

# Test images - 10 real-world images
TEST_IMAGES = [
    # Human photos
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800",
    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=800",
    
    # Product images
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800",
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800",
    
    # Document-like images
    "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800",
    "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800",
    
    # Scenic/landscape (complex backgrounds)
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
    "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=800",
    
    # Mixed content
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
]

# Alternative: Use local test images if available
LOCAL_IMAGE_PATHS = [
    "test_images/person1.jpg",
    "test_images/person2.jpg",
    "test_images/product1.jpg",
    "test_images/product2.jpg",
    "test_images/document1.jpg",
    "test_images/document2.jpg",
    "test_images/landscape1.jpg",
    "test_images/landscape2.jpg",
    "test_images/mixed1.jpg",
    "test_images/mixed2.jpg",
]

BACKEND_URL = os.environ.get('BACKEND_URL', 'https://bg-removal-birefnet-564572183797.us-central1.run.app')
ENABLE_DEBUG_STATS = True  # Request debug stats in response

# To enable debug stats in backend, set FORENSIC_MODE=1 environment variable
# Or set DEBUG_RETURN_STATS=1

def download_image(url: str, timeout: int = 30) -> Optional[bytes]:
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"  ❌ Failed to download {url}: {e}")
        return None

def load_local_image(path: str) -> Optional[bytes]:
    """Load image from local file"""
    try:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return f.read()
        return None
    except Exception as e:
        print(f"  ❌ Failed to load {path}: {e}")
        return None

def test_image(image_data: bytes, image_name: str, test_num: int) -> Dict:
    """Test a single image and return forensic data"""
    print(f"\n{'='*80}")
    print(f"TEST {test_num}/10: {image_name}")
    print(f"{'='*80}")
    
    # Prepare multipart/form-data request
    files = {'image': ('image.jpg', image_data, 'image/jpeg')}
    data = {
        'maxSize': '512',
        'imageType': 'auto'  # Let backend auto-detect
    }
    
    # Add debug flag if supported
    headers = {}
    if ENABLE_DEBUG_STATS:
        # Some backends might support this as query param or header
        pass
    
    start_time = time.time()
    
    try:
        # Send request
        response = requests.post(
            f"{BACKEND_URL}/api/free-preview-bg",
            files=files,
            data=data,
            headers=headers,
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            return {
                'test_num': test_num,
                'image_name': image_name,
                'status': 'ERROR',
                'status_code': response.status_code,
                'error': response.text[:500],
                'elapsed_time': elapsed
            }
        
        result = response.json()
        
        # Extract forensic data
        forensic_data = {
            'test_num': test_num,
            'image_name': image_name,
            'status': 'SUCCESS' if result.get('success') else 'FAILED',
            'elapsed_time': elapsed,
            'output_size_mb': result.get('outputSizeMB', 0),
            'preview_mode': result.get('previewMode', 'unknown'),
            'processed_with': result.get('processedWith', 'unknown'),
            'optimizations': result.get('optimizations', {}),
        }
        
        # Extract debug stats if available
        debug_stats = result.get('debugMask', {})
        if debug_stats:
            forensic_data['debug_stats'] = {
                # Image type detection
                'model_used': debug_stats.get('model_used', 'unknown'),
                
                # Mask stats AFTER recovery
                'mask_nonzero_ratio': debug_stats.get('mask_nonzero_ratio', 0.0),
                'mask_nonzero_ratio_recovery': debug_stats.get('recovery_nonzero_ratio', None),
                'mask_mean': debug_stats.get('mask_mean', 0.0),
                
                # Emergency mask tracking
                'used_fallback_level': debug_stats.get('used_fallback_level', 0),
                'recovery_level_2_applied': debug_stats.get('recovery_level_2_applied', False),
                'recovery_level_3_applied': debug_stats.get('recovery_level_3_applied', False),
                'emergency_mask_applied': debug_stats.get('recovery_level_3_applied', False),
                
                # Composite execution path indicators
                'mask_empty': debug_stats.get('mask_empty', False),
                'fallback_to_raw': debug_stats.get('fallback_to_raw', False),
                
                # Alpha stats
                'alpha_percent': debug_stats.get('alpha_percent', 0.0),
                'alpha_final_min': debug_stats.get('alpha_final_min', None),
                'alpha_final_max': debug_stats.get('alpha_final_max', None),
                'alpha_final_nonzero': debug_stats.get('alpha_final_nonzero', None),
                'alpha_out_min': debug_stats.get('alpha_out_min', None),
                'alpha_out_max': debug_stats.get('alpha_out_max', None),
                'alpha_out_nonzero': debug_stats.get('alpha_out_nonzero', None),
                'alpha_safety_clamp_applied': debug_stats.get('alpha_safety_clamp_applied', False),
            }
        
        # Verify result image exists
        if result.get('resultImage'):
            # Decode base64 to verify it's a valid PNG
            try:
                img_data = result['resultImage']
                if img_data.startswith('data:image'):
                    base64_part = img_data.split(',')[1]
                    img_bytes = base64.b64decode(base64_part)
                    forensic_data['result_image_valid'] = True
                    forensic_data['result_image_size'] = len(img_bytes)
                else:
                    forensic_data['result_image_valid'] = False
            except Exception as e:
                forensic_data['result_image_valid'] = False
                forensic_data['result_image_error'] = str(e)
        else:
            forensic_data['result_image_valid'] = False
        
        return forensic_data
        
    except Exception as e:
        return {
            'test_num': test_num,
            'image_name': image_name,
            'status': 'EXCEPTION',
            'error': str(e),
            'elapsed_time': time.time() - start_time
        }

def print_forensic_report(results: List[Dict]):
    """Print detailed forensic report"""
    print(f"\n\n{'='*80}")
    print("FORENSIC VALIDATION REPORT")
    print(f"{'='*80}\n")
    
    for result in results:
        print(f"\n{'─'*80}")
        print(f"Image {result['test_num']}: {result['image_name']}")
        print(f"{'─'*80}")
        print(f"Status: {result['status']}")
        print(f"Processing Time: {result.get('elapsed_time', 0):.2f}s")
        
        if result['status'] == 'SUCCESS':
            print(f"Preview Mode: {result.get('preview_mode', 'unknown')}")
            print(f"Output Size: {result.get('output_size_mb', 0):.2f} MB")
            
            optimizations = result.get('optimizations', {})
            print(f"Model: {optimizations.get('model_tuning', 'unknown')}")
            print(f"Document Mode: {optimizations.get('document_mode', False)}")
            
            debug = result.get('debug_stats', {})
            if debug:
                print(f"\n📊 FORENSIC METRICS:")
                print(f"  Model Used: {debug.get('model_used', 'unknown')}")
                print(f"  Mask Nonzero Ratio (AFTER recovery): {debug.get('mask_nonzero_ratio_recovery') or debug.get('mask_nonzero_ratio', 0.0):.6f}")
                print(f"  Mask Mean: {debug.get('mask_mean', 0.0):.2f}")
                print(f"  Fallback Level: {debug.get('used_fallback_level', 0)}")
                print(f"  Emergency Mask Applied: {debug.get('emergency_mask_applied', False)}")
                print(f"  Level 2 Recovery: {debug.get('recovery_level_2_applied', False)}")
                print(f"  Level 3 Recovery: {debug.get('recovery_level_3_applied', False)}")
                
                # Composite execution path
                mask_empty = debug.get('mask_empty', False)
                fallback_raw = debug.get('fallback_to_raw', False)
                emergency = debug.get('emergency_mask_applied', False)
                
                if emergency:
                    composite_path = "FORCED_COMPOSITE (emergency mask active)"
                elif mask_empty or fallback_raw:
                    composite_path = "RAW_OUTPUT (empty mask/low alpha fallback)"
                else:
                    composite_path = "STANDARD_COMPOSITE"
                
                print(f"  Composite Path: {composite_path}")
                
                # Alpha stats
                print(f"\n  Alpha Stats:")
                print(f"    Alpha Percent: {debug.get('alpha_percent', 0.0):.2f}%")
                if debug.get('alpha_final_min') is not None:
                    print(f"    Final Min: {debug.get('alpha_final_min')}")
                    print(f"    Final Max: {debug.get('alpha_final_max')}")
                    print(f"    Final Nonzero: {debug.get('alpha_final_nonzero')}")
                if debug.get('alpha_out_min') is not None:
                    print(f"    Output Min: {debug.get('alpha_out_min')}")
                    print(f"    Output Max: {debug.get('alpha_out_max')}")
                    print(f"    Output Nonzero: {debug.get('alpha_out_nonzero')}")
                print(f"    Safety Clamp Applied: {debug.get('alpha_safety_clamp_applied', False)}")
            
            print(f"  Result Image Valid: {result.get('result_image_valid', False)}")
            
            # CRITICAL CHECK: No raw output_image should be returned
            if debug.get('fallback_to_raw', False) and not debug.get('emergency_mask_applied', False):
                print(f"  ⚠️  WARNING: Fallback to raw detected (but emergency mask not applied)")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed = len(results) - successful
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    # Check for any blank/unprocessed PNGs
    blank_images = []
    for result in results:
        if result.get('status') == 'SUCCESS':
            debug = result.get('debug_stats', {})
            alpha_nonzero = debug.get('alpha_out_nonzero', 0)
            if alpha_nonzero == 0 or alpha_nonzero is None:
                blank_images.append((result['test_num'], result['image_name']))
    
    if blank_images:
        print(f"\n⚠️  BLANK/UNPROCESSED PNGs DETECTED:")
        for test_num, name in blank_images:
            print(f"  - Test {test_num}: {name}")
            result = results[test_num - 1]
            print(f"    Code Path: See debug stats above")
    else:
        print(f"\n✅ No blank/unprocessed PNGs detected")

def main():
    """Run forensic validation tests"""
    print("="*80)
    print("FORENSIC VALIDATION TEST - FREE PREVIEW BACKGROUND REMOVAL")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Tests: {len(TEST_IMAGES)} images")
    print("="*80)
    
    results = []
    
    # Test each image
    for i, image_source in enumerate(TEST_IMAGES, 1):
        image_data = None
        image_name = f"Image {i}"
        
        # Try to download or load local
        if image_source.startswith('http'):
            image_data = download_image(image_source)
            image_name = f"URL: {image_source[:50]}..."
        else:
            image_data = load_local_image(image_source)
            image_name = Path(image_source).name
        
        if image_data is None:
            print(f"⚠️  Skipping image {i}: Could not load")
            results.append({
                'test_num': i,
                'image_name': image_name,
                'status': 'SKIPPED',
                'error': 'Could not load image'
            })
            continue
        
        result = test_image(image_data, image_name, i)
        results.append(result)
        
        # Small delay between tests
        time.sleep(1)
    
    # Print forensic report
    print_forensic_report(results)
    
    # Save results to JSON
    output_file = 'forensic_validation_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed results saved to: {output_file}")

if __name__ == '__main__':
    main()

