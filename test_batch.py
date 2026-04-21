#!/usr/bin/env python3
"""
Test Script untuk Batch Search API
Menguji apakah parallel scraping benar-benar berjalan
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"

def test_batch_search():
    """Test batch search dengan 3 keywords"""
    print("=" * 60)
    print("Testing Batch Search - Parallel Scraping")
    print("=" * 60)
    
    payload = {
        "keywords": ["pertamina", "telkom", "bca"],
        "max_pages": 2,
        "category": "news",
        "concurrency": 3
    }
    
    print(f"\n Sending request:")
    print(json.dumps(payload, indent=2))
    
    print(f"\n Starting batch search at {datetime.now().strftime('%H:%M:%S')}...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/search/batch",
            json=payload,
            timeout=300
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\nRequest completed in {elapsed:.2f}s")
            print(f"\nSummary:")
            print(f"   Request ID: {result['request_id']}")
            print(f"   Total Keywords: {result['total_keywords']}")
            print(f"   Successful: {result['successful']}")
            print(f"   Failed: {result['failed']}")
            print(f"   Partial: {result['partial']}")
            print(f"   Total Results: {result['total_results']}")
            print(f"   Duration: {result['duration_seconds']}s")
            
            print(f"\nResults per keyword:")
            for kr in result['results']:
                status_emoji = {
                    'success': '✅',
                    'failed': '❌',
                    'partial': '⚠️'
                }.get(kr['status'], '❓')
                
                print(f"   {status_emoji} {kr['keyword']}: "
                      f"{kr['results_count']} results in "
                      f"{kr.get('duration_seconds', 0)}s")
                
                if kr.get('error'):
                    print(f"      Error: {kr['error']}")
            
            # Analisis performa
            print(f"\n Performance Analysis:")
            individual_times = [kr.get('duration_seconds', 0) for kr in result['results']]
            max_individual = max(individual_times) if individual_times else 0
            total_time = result['duration_seconds']
            
            print(f"   Longest individual search: {max_individual:.2f}s")
            print(f"   Total batch time: {total_time:.2f}s")
            
            if max_individual > 0:
                efficiency = (max_individual / total_time) * 100
                print(f"   Parallelism efficiency: {efficiency:.1f}%")
                
                if efficiency > 80:
                    print(f"   Excellent! Parallel scraping bekerja dengan baik!")
                elif efficiency > 50:
                    print(f"   Good, tapi masih bisa lebih optimal")
                else:
                    print(f"   Poor, parallel scraping mungkin tidak bekerja!")
            
            # Save hasil ke file
            output_file = f"batch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n Full result saved to: {output_file}")
            
        else:
            print(f"\n Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print(f"\n Request timeout after {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"\n Error: {e}")

def test_health():
    """Test health check endpoint"""
    print("\n Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f" Health check OK: {response.json()}")
        else:
            print(f" Health check failed: {response.status_code}")
    except Exception as e:
        print(f" Cannot connect to API: {e}")
        print(f"   Make sure server is running: uvicorn app.main:app --reload")

if __name__ == "__main__":
    test_health()
    
    # Tunggu sebentar
    time.sleep(1)
    
    # Test batch search
    test_batch_search()
    
    print("\n" + "=" * 60)
    print(" Test completed!")
    print("=" * 60)