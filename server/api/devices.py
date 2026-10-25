"""
118 팔배개 - 오디오 입력 장치 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from audio_agent.device_manager import AudioDeviceManager

router = APIRouter(prefix="/api/devices", tags=["Audio Devices"])


class DeviceSelectRequest(BaseModel):
    device_index: int


@router.get("", response_model=List[Dict[str, Any]])
def list_devices():
    """Windows에서 사용 가능한 모든 오디오 입력 장치 검색 및 반환"""
    try:
        return AudioDeviceManager.list_input_devices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오디오 장치 목록 조회 실패: {str(e)}")


@router.get("/{device_index}")
def get_device(device_index: int):
    """특정 오디오 장치 정보 조회"""
    dev = AudioDeviceManager.get_device_info(device_index)
    if not dev:
        raise HTTPException(status_code=404, detail="오디오 장치를 찾을 수 없습니다.")
    return dev
