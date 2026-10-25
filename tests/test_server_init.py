"""
118 팔배개 - FastAPI 서버 및 라우트 초기화 테스트
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.main import app
from fastapi.testclient import TestClient


class TestServerInit(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_routes_exist(self):
        # 라우트 경로 점검
        paths = [getattr(r, "path", None) for r in app.routes]
        paths = [p for p in paths if p is not None]
        self.assertIn("/api/health", paths)
        print(f"\n[등록된 라우트 목록] {paths}")

        # 헬스체크 API 호출
        with TestClient(app) as client:
            resp = client.get("/api/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "HEALTHY")
            self.assertEqual(data["system"], "118 팔배개 (118 PAL-BEGAE)")
            print(f"[헬스체크 응답] {data}")


if __name__ == "__main__":
    unittest.main()
