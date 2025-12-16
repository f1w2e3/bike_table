import requests
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from datetime import datetime
import pytz

# 1. 환경변수 로드
tashu_key = os.environ.get("TASHU_API_KEY")
firebase_json = os.environ.get("FIREBASE_KEY_JSON")

# 2. 파이어베이스 접속
if not firebase_admin._apps:
    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': f"https://tashu-archive-default-rtdb.firebaseio.com/"
    })

def run():
    # 3. 타슈 API 호출
    url = "https://bikeapp.tashu.or.kr:50041/v1/openapi/station"
    headers = {"api-token": tashu_key}
    
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200:
            print(f"API Error: {res.status_code}")
            return

        data = res.json()
        raw_stations = data.get("results", [])
        
        # 4. 데이터 다이어트 (중요!)
        # 모든 정보를 저장하면 용량이 폭발하므로 id와 count만 추출
        # 저장 형식: { "ST0001": 5, "ST0002": 0, ... }
        compact_data = {}
        for st in raw_stations:
            # 주차대수가 없으면 0으로 처리
            count = int(st.get('parking_count', 0))
            compact_data[st.get('id')] = count

        # 5. 시간 구하기 (한국 시간)
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
        date_str = now.strftime("%Y-%m-%d")   # 예: 2025-10-20
        time_str = now.strftime("%H:%M")      # 예: 14:10
        
        # 6. 파이어베이스 저장
        # 구조: tashu_log -> 2025-10-20 -> 14:10 -> {데이터}
        ref = db.reference(f'tashu_log/{date_str}/{time_str}')
        ref.set(compact_data)
        
        print(f"✅ 저장 완료: {date_str} {time_str} (정류장 {len(compact_data)}개)")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run()
