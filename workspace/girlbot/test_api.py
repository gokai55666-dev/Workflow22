#!/usr/bin/env python3
"""
test_api.py - Test Girlbot API from command line
Usage: python3 test_api.py "your prompt here"
"""
import requests
import sys
import time
import argparse

def test_generation(prompt, mode="basic", api_url="http://localhost:8000"):
    """Test the queue API"""
    print(f"🚀 Testing: '{prompt}'")
    print(f"   API: {api_url}")
    print(f"   Mode: {mode}")
    
    # Submit job
    print("\n📤 Submitting...")
    try:
        r = requests.post(
            f"{api_url}/gen",
            json={"prompt": prompt, "mode": mode},
            timeout=10
        )
        r.raise_for_status()
        result = r.json()
        job_id = result["job_id"]
        print(f"   ✅ Job ID: {job_id}")
        print(f"   📊 Queue position: {result.get('position', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Poll for result
    print("\n⏳ Polling (max 5 minutes)...")
    for i in range(150):
        try:
            r = requests.get(f"{api_url}/res/{job_id}", timeout=5)
            status = r.json()
            
            if status.get("status") == "done":
                print(f"\n   ✅ Complete!")
                print(f"   📁 File: {status['file']}")
                print(f"   🌐 View: http://localhost:8188/view?filename={status['file']}&type=output")
                return True
            elif status.get("status") == "error":
                print(f"\n   ❌ Error: {status.get('message', 'Unknown')}")
                return False
            
            # Progress
            print(f"   ... {i*2}s elapsed", end="\r")
            
        except Exception as e:
            print(f"   ⚠️  Poll error: {e}")
        
        time.sleep(2)
    
    print("\n   ⏱️ Timeout after 5 minutes")
    return False

def main():
    parser = argparse.ArgumentParser(description="Test Girlbot API")
    parser.add_argument("prompt", nargs="?", default="a beautiful sunset", help="Generation prompt")
    parser.add_argument("--mode", default="basic", choices=["basic", "hq"], help="Quality mode")
    parser.add_argument("--api", default="http://localhost:8000", help="API URL")
    
    args = parser.parse_args()
    
    success = test_generation(args.prompt, args.mode, args.api)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
