"""
118 팔배개 - Windows Line-in 오디오 캡처 에이전트 실행 진입점
단독 실행, 오디오 장치 테스트, STT 서버로의 스트리밍 지원
"""

import sys
import os
import argparse
import asyncio
import logging
import time

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from audio_agent.device_manager import AudioDeviceManager
from audio_agent.capture import AudioCaptureStream
from audio_agent.ws_client import AudioWebSocketClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
)
logger = logging.getLogger("AudioAgentMain")


def list_devices():
    """모든 입력 장치 목록 출력"""
    devices = AudioDeviceManager.list_input_devices()
    print("\n" + "=" * 70)
    print("  [118 팔배개] Windows 오디오 입력 장치 목록")
    print("=" * 70)
    for d in devices:
        tags = []
        if d["is_line_in_candidate"]:
            tags.append("★Line-in 후보")
        if d["is_default"]:
            tags.append("●기본장치")
        tag_str = f"[{', '.join(tags)}]" if tags else ""

        print(f"ID {d['index']:02d} | {d['name']} {tag_str}")
        print(f"      API: {d['host_api']} | 채널: {d['max_input_channels']}ch | 기본: {d['default_samplerate']}Hz")
        print(f"      지원 샘플레이트: {d['supported_sample_rates']}")
        print("-" * 70)
    print("\n사용 예시: python audio_agent/run_agent.py --device 3\n")


def test_audio_vad(device_idx: int, duration_sec: int = 5):
    """지정된 장치로 VAD 및 레벨 테스트 수행"""
    print(f"\n[오디오 수집 및 VAD 테스트 시작] 장치 ID: {device_idx}, {duration_sec}초 동안 진행...")
    print("마이크 또는 Line-in에 말을 하거나 소리를 내보세요. (실시간 VU 레벨 표시)\n")

    speech_count = 0

    def vu_callback(level: int):
        bars = "#" * (level // 4)
        print(f"\r[VU] {level:3d}% |{bars:<25}|", end="", flush=True)

    def speech_callback(segment, is_final: bool):
        nonlocal speech_count
        status = "확정 세그먼트" if is_final else "중간 구간"
        duration = len(segment) / 16000.0
        print(f"\n >>> [VAD 음성 감지] {status}: {duration:.2f}초 ({len(segment)} samples)")
        if is_final:
            speech_count += 1

    stream = AudioCaptureStream(
        device_index=device_idx,
        target_sample_rate=16000,
        energy_threshold=0.008,
        on_vu_update=vu_callback,
        on_speech_segment=speech_callback
    )

    if not stream.start():
        print("\n오디오 스트림 시작 실패!")
        return

    try:
        time.sleep(duration_sec)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()

    print(f"\n\n[테스트 완료] 총 감지된 발화 세그먼트: {speech_count}개")


def main():
    parser = argparse.ArgumentParser(description="118 팔배개 Windows Line-in 오디오 수집 에이전트")
    parser.add_argument("--list-devices", action="store_true", help="사용 가능한 오디오 입력 장치 목록 출력")
    parser.add_argument("--device", type=int, default=None, help="선택할 오디오 장치 ID 번호")
    parser.add_argument("--server-url", type=str, default="ws://127.0.0.1:8000/ws/audio", help="STT 서버 WebSocket URL")
    parser.add_argument("--test-vad", action="store_true", help="VAD 로컬 테스트 모드 실행 (5초)")
    parser.add_argument("--duration", type=int, default=5, help="테스트 실행 시간 (초)")

    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    if args.test_vad:
        dev_idx = args.device if args.device is not None else -1
        test_audio_vad(dev_idx, duration_sec=args.duration)
        return

    # WebSocket 클라이언트 모드로 서버 전송 실행
    client = AudioWebSocketClient(
        server_ws_url=args.server_url,
        device_index=args.device
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 에이전트가 종료되었습니다.")
        client.stop()


if __name__ == "__main__":
    main()
