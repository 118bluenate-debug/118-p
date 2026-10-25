"""
118 팔배개 - VAD (Voice Activity Detection) 단위 테스트
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from audio_agent.vad import EnergyVAD, VadState


class TestEnergyVAD(unittest.TestCase):

    def setUp(self):
        self.vad = EnergyVAD(
            sample_rate=16000,
            frame_ms=30,
            energy_threshold=0.01,
            silence_timeout_ms=100
        )

    def test_silence_detection(self):
        # 30ms 무음 프레임 (480 samples, 진폭 0.0)
        silent_frame = np.zeros(480, dtype=np.float32)
        state, vu, segment = self.vad.process_frame(silent_frame)
        self.assertEqual(state, VadState.SILENCE)
        self.assertEqual(vu, 0)
        self.assertIsNone(segment)

    def test_speech_start_and_end(self):
        # 1. 무음 구간 통과
        silent_frame = np.zeros(480, dtype=np.float32)
        for _ in range(5):
            self.vad.process_frame(silent_frame)

        # 2. 음성 프레임 생성 (440Hz 사인파, 진폭 0.3)
        t = np.linspace(0, 0.03, 480, endpoint=False)
        voice_frame = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        # 발화 시작
        state1, vu1, seg1 = self.vad.process_frame(voice_frame)
        self.assertEqual(state1, VadState.SPEECH_START)
        self.assertGreater(vu1, 10)
        self.assertTrue(self.vad.is_speaking)

        # 발화 지속
        for _ in range(4):
            state, vu, seg = self.vad.process_frame(voice_frame)
            self.assertEqual(state, VadState.SPEECH)

        # 3. 묵음으로 발화 종료 유도 (silence_timeout_ms=100, 즉 4프레임 = 120ms 무음)
        completed = None
        for _ in range(5):
            state, vu, seg = self.vad.process_frame(silent_frame)
            if state == VadState.SPEECH_END:
                completed = seg
                break

        self.assertIsNotNone(completed)
        self.assertFalse(self.vad.is_speaking)


if __name__ == "__main__":
    unittest.main()
