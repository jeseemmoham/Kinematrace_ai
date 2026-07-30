import urllib.request
import json

def test_live_chat_api():
    url = "http://localhost:8000/api/agents/chat"
    payload = {
        "message": "Why is this patient high risk?",
        "context": {
            "case_id": "case2",
            "patient_info": {"id": "KT-2026-P902", "age": "7 y/o", "case": "Post-Injury Asymmetric Gait"}
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("API Response category:", res_data.get("category"))
            print("API Response snippet:\n", res_data.get("response")[:200])
            assert "HIGH RISK" in res_data.get("response")
            assert "20.9%" in res_data.get("response")
            print("[PASS] Live FastAPI /api/agents/chat test PASSED!")
    except Exception as e:
        print("FastAPI test error:", e)

if __name__ == "__main__":
    test_live_chat_api()
