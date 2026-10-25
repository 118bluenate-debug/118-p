"""
118 팔배개 - Windows 오디오 입력 장치 관리 모듈
오디오 장치 검색, Line-in 장치 식별, 지원 샘플레이트 및 채널 수 조회 기능 제공
"""

from typing import List, Dict, Any, Optional
import sounddevice as sd


class AudioDeviceManager:
    """Windows 오디오 장치 검색 및 검증 클래스"""

    LINE_IN_KEYWORDS = [
        "line", "line-in", "line in", "라인", "라인 입력",
        "stereo mix", "스테레오 믹스", "what u hear", "혼합", "mixed"
    ]

    @classmethod
    def list_input_devices(cls) -> List[Dict[str, Any]]:
        """사용 가능한 모든 오디오 입력 장치 목록 반환"""
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        input_devices: List[Dict[str, Any]] = []

        default_input_idx = sd.default.device[0]

        for idx, dev in enumerate(devices):
            # 입력 채널이 1개 이상인 장치만 필터링
            max_in = dev.get("max_input_channels", 0)
            if max_in <= 0:
                continue

            hostapi_idx = dev.get("hostapi", 0)
            hostapi_name = (
                hostapis[hostapi_idx].get("name", "Unknown")
                if hostapi_idx < len(hostapis)
                else "Unknown"
            )

            name = dev.get("name", f"Device #{idx}")
            is_line_in = any(kw in name.lower() for kw in cls.LINE_IN_KEYWORDS)

            input_devices.append({
                "index": idx,
                "name": name,
                "host_api": hostapi_name,
                "max_input_channels": max_in,
                "default_samplerate": int(dev.get("default_samplerate", 44100)),
                "is_default": (idx == default_input_idx),
                "is_line_in_candidate": is_line_in,
                "supported_sample_rates": cls._check_supported_sample_rates(idx, max_in)
            })

        return input_devices

    @classmethod
    def _check_supported_sample_rates(cls, device_idx: int, channels: int) -> List[int]:
        """장치가 지원하는 표준 샘플레이트 확인"""
        standard_rates = [8000, 16000, 22050, 32000, 44100, 48000, 96000]
        supported = []
        for rate in standard_rates:
            try:
                sd.check_input_settings(
                    device=device_idx,
                    channels=min(channels, 2),
                    samplerate=rate
                )
                supported.append(rate)
            except Exception:
                pass
        return supported

    @classmethod
    def get_device_info(cls, device_idx: int) -> Optional[Dict[str, Any]]:
        """특정 장치의 상세 정보 반환"""
        try:
            dev = sd.query_devices(device_idx)
            if dev.get("max_input_channels", 0) <= 0:
                return None
            return {
                "index": device_idx,
                "name": dev.get("name", f"Device #{device_idx}"),
                "max_input_channels": dev.get("max_input_channels", 1),
                "default_samplerate": int(dev.get("default_samplerate", 44100)),
            }
        except Exception:
            return None


if __name__ == "__main__":
    import json
    print("=== 118 팔배개 - Windows 오디오 입력 장치 목록 ===")
    devs = AudioDeviceManager.list_input_devices()
    for d in devs:
        line_tag = "[Line-in 후보]" if d["is_line_in_candidate"] else ""
        def_tag = "[기본 장치]" if d["is_default"] else ""
        print(f"[{d['index']:02d}] {d['name']} {line_tag} {def_tag}")
        print(f"     API: {d['host_api']} | 채널: {d['max_input_channels']}ch | 기본Hz: {d['default_samplerate']}Hz")
        print(f"     지원Hz: {d['supported_sample_rates']}")
