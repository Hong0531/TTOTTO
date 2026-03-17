import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import os
import datetime

# --- 설정 ---
# DEFAULT_SAMPLE_RATE = 16000  # 샘플 속도 (Hz). Whisper는 16000Hz를 권장하지만, 마이크에서 지원하지 않을 수 있음.
DEFAULT_SAMPLE_RATE = 44100  # 표준 샘플 속도 (Hz)로 변경. 대부분의 마이크에서 지원함.
DEFAULT_CHANNELS = 1       # 채널 수 (1: 모노, 2: 스테레오)
DEFAULT_DURATION = 5       # 기본 녹음 시간 (초)
DEFAULT_OUTPUT_DIR = "recordings" # 녹음 파일 저장 디렉토리
# --- 설정 끝 ---

def ensure_dir(directory):
    """지정된 디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"디렉토리 생성: {directory}")

def record_audio(duration=DEFAULT_DURATION,
                 samplerate=DEFAULT_SAMPLE_RATE,
                 channels=DEFAULT_CHANNELS,
                 output_dir=DEFAULT_OUTPUT_DIR,
                 filename_prefix="recording"):
    """
    마이크에서 지정된 시간 동안 오디오를 녹음하고 WAV 파일로 저장합니다.

    Args:
        duration (int): 녹음할 시간 (초).
        samplerate (int): 샘플 속도 (Hz).
        channels (int): 오디오 채널 수.
        output_dir (str): 녹음 파일을 저장할 디렉토리 경로.
        filename_prefix (str): 저장될 파일 이름의 접두사.

    Returns:
        str: 저장된 WAV 파일의 전체 경로. None이면 녹음 실패.
    """
    ensure_dir(output_dir) # 저장 디렉토리 확인 및 생성

    try:
        print(f"사용 가능한 장치 확인 중...")
        print(sd.query_devices()) # 사용 가능한 장치 목록 출력 (디버깅용)
        print(f"기본 입력 장치: {sd.default.device[0]}") # 기본 입력 장치 인덱스 확인

        print(f"{duration}초 동안 오디오 녹음을 시작합니다 (샘플 속도: {samplerate} Hz)...")
        # sounddevice.rec 함수를 사용하여 녹음 시작
        # frames: 총 녹음할 프레임 수 (duration * samplerate)
        # samplerate: 샘플 속도
        # channels: 채널 수
        # dtype: 데이터 타입 (float32가 일반적)
        # blocking=True: 녹음이 끝날 때까지 대기
        recording_data = sd.rec(int(duration * samplerate),
                                samplerate=samplerate,
                                channels=channels,
                                dtype='float32',
                                blocking=True)

        # sd.wait() # blocking=True 이므로 필요 없을 수 있지만, 확실히 하기 위해 추가 가능

        print("녹음 완료.")

        # 파일 이름 생성 (타임스탬프 포함하여 중복 방지)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.wav"
        filepath = os.path.join(output_dir, filename)

        print(f"녹음된 오디오를 '{filepath}' 파일로 저장합니다...")
        # 녹음된 데이터를 WAV 파일로 저장
        # samplerate에 맞게 데이터 스케일 조정 필요 없음 (float32 사용 시)
        # write 함수는 NumPy 배열을 받아 WAV 파일로 저장합니다.
        # int16으로 변환하여 저장 (일반적인 WAV 형식)
        write(filepath, samplerate, (recording_data * 32767).astype(np.int16))
        # write(filepath, samplerate, recording_data) # float32로 직접 저장도 가능

        print("파일 저장 완료.")
        return filepath

    except sd.PortAudioError as pae:
        print(f"PortAudio 오류 발생: {pae}")
        print("샘플 속도나 장치 설정을 확인하세요.")
        return None
    except Exception as e:
        print(f"오디오 녹음 중 오류 발생: {e}")
        return None

# --- 모듈 테스트 코드 ---
if __name__ == "__main__":
    print("오디오 녹음 모듈 테스트를 시작합니다.")

    # 기본 설정으로 5초간 녹음 시도
    recorded_file = record_audio()

    if recorded_file:
        print(f"\n테스트 녹음 성공! 파일 위치: {recorded_file}")
    else:
        print("\n테스트 녹음 실패.")
