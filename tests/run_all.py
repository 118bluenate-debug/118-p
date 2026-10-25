"""
118 팔배개 - 전체 테스트 통합 실행기 (Python 기반, Windows 및 Linux 공용)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    print("=" * 65)
    print("  [118 팔배개] 전체 시스템 통합 테스트 러너")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 파일 검색 및 로드
    tests_dir = os.path.dirname(__file__)
    for filename in sorted(os.listdir(tests_dir)):
        if filename.startswith("test_") and filename.endswith(".py"):
            module_name = f"tests.{filename[:-3]}"
            print(f">> 테스트 모듈 로드: {module_name}")
            try:
                tests = loader.loadTestsFromName(module_name)
                suite.addTests(tests)
            except Exception as e:
                print(f"로드 실패 ({module_name}): {e}")

    print("\n" + "-" * 65)
    print(">>> 테스트 실행 중...")
    print("-" * 65)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 65)
    print(f" [테스트 결과] 실행: {result.testsRun}개 | 실패: {len(result.failures)}개 | 에러: {len(result.errors)}개")
    print("=" * 65)

    if not result.wasSuccessful():
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
