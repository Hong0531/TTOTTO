# -*- coding: utf-8 -*-
import os
import requests # PC 서버 API 호출용
import subprocess # 외부 명령어(arecord, aplay) 실행용
import json      # JSON 데이터 처리용
import time      # 시간 관련 함수 사용 (sleep 추가)
from dotenv import load_dotenv # .env 파일 로드용
import traceback # 오류 상세 출력을 위해 추가

# --- 사용자 정의 모듈 임포트 ---
led_controller = None
weather_module = None
language_model = None

print("모듈 로드 시도...")
# (모듈 임포트 로직 - led_controller)
try:
    import led_controller
    print("  - led_controller 모듈 임포트 성공.")

    # --- led_controller 초기화 호출 및 결과 확인 ---
    print("  - led_controller.initialize() 호출 시도...")
    initialization_result = led_controller.initialize() # 결과를 변수에 저장
    print(f"  - led_controller.initialize() 반환값: {initialization_result}") # 반환값 직접 출력

    if initialization_result:
        print("  - led_controller 초기화 성공 (main.py에서 확인). LED 기능 활성화됨.")
    else:
        print("  - 오류: led_controller.initialize() 호출 실패. LED 기능 비활성화됨.")
        led_controller = None

except ImportError:
    print("  - 경고: led_controller.py 파일을 찾거나 임포트할 수 없습니다. LED 기능이 비활성화됩니다.")
    led_controller = None
except Exception as e:
    print(f"  - 경고: led_controller 모듈 로드/초기화 중 예외 발생 ({e}). LED 기능 비활성화됨.")
    traceback.print_exc()
    led_controller = None

# (weather_module, language_model 임포트 로직은 그대로)
try:
    import weather_module
    print("  - weather_module 모듈 로드 성공.")
except ImportError:
    print("  - 경고: weather_module.py 파일을 찾거나 임포트할 수 없습니다. 날씨 기능이 비활성화됩니다.")
    weather_module = None
except Exception as e:
    print(f"  - 경고: weather_module 모듈 로드 중 오류 발생 ({e}). 날씨 기능이 비활성화됩니다.")
    traceback.print_exc()
    weather_module = None

try:
    import language_model
    print("  - language_model 모듈 로드 성공.")
except ImportError:
    print("  - 경고: language_model.py 파일을 찾거나 임포트할 수 없습니다. LLM 기능이 비활성화됩니다.")
    language_model = None
except Exception as e:
    print(f"  - 경고: language_model 모듈 로드 중 오류 발생 ({e}). LLM 기능이 비활성화됩니다.")
    traceback.print_exc()
    language_model = None
print("모듈 로드 시도 완료.")


# --- .env 파일 로드 ---
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(".env 파일 로드 완료.")
else:
    print("경고: .env 파일을 찾을 수 없습니다. 환경 변수 또는 기본값을 사용합니다.")


# --- 설정 ---
PC_SERVER_URL = os.getenv("PC_SERVER_URL", "http://192.168.137.116:5001")
print(f"PC 서버 URL: {PC_SERVER_URL}")
AUDIO_RECORD_DEVICE = os.getenv("AUDIO_RECORD_DEVICE", "plughw:3,0")
print(f"오디오 녹음 장치: {AUDIO_RECORD_DEVICE}")
AUDIO_RECORD_FORMAT = "S16_LE"
# --- ★★★ 샘플 레이트 설정 수정 (44100Hz 기본값) ★★★ ---
AUDIO_RECORD_RATE = int(os.getenv("AUDIO_RECORD_RATE", 44100))
print(f"오디오 녹음 샘플 레이트: {AUDIO_RECORD_RATE} Hz")
# -------------------------------------------------------
RECORD_DURATION = int(os.getenv("RECORD_DURATION", 5))
print(f"오디오 녹음 시간: {RECORD_DURATION} 초")
RECORDED_AUDIO_FILENAME = "recorded_audio.wav"
RESPONSE_AUDIO_FILENAME = "response.wav"

# --- 함수 정의들 ---
def record_audio(filename=RECORDED_AUDIO_FILENAME, duration=RECORD_DURATION, device=AUDIO_RECORD_DEVICE, format=AUDIO_RECORD_FORMAT, rate=AUDIO_RECORD_RATE): # rate 파라미터 추가
    """arecord 명령어를 사용하여 오디오를 녹음합니다."""
    print(f"{duration}초 동안 음성 녹음을 시작합니다... ('{device}', {rate}Hz 사용)") # rate 정보 추가
    print("[main.py] 녹음 시작 전 LED 파란색 변경 시도...")
    if led_controller: led_controller.set_led_color(led_controller.COLOR_BLUE)
    # --- ★★★ 명령어에 rate 와 채널(-c 1) 명시적으로 포함 ★★★ ---
    command = ['arecord', '-D', device, '-f', format, '-r', str(rate), '-c', '1', '-d', str(duration), filename]
    try:
        # 파일 삭제 로직
        if os.path.exists(filename):
            print(f"[record_audio] 이전 파일 '{filename}' 삭제 시도...")
            os.remove(filename)
            print(f"[record_audio] 이전 파일 삭제 완료.")
        else:
             print(f"[record_audio] 이전 파일 '{filename}' 없음. 바로 녹음 시작.")

        print(f"[record_audio] 실행 명령어: {' '.join(command)}") # 실행 명령어 확인
        result = subprocess.run(command, check=True, capture_output=True, text=True) # arecord 실행
        print(f"녹음 완료: {filename}")

        # 파일 크기 확인
        if os.path.exists(filename):
            print(f"  -> 녹음된 파일 크기: {os.path.getsize(filename)} bytes")
        else:
            print("  -> 경고: 녹음 후 파일이 생성되지 않았습니다!")

        print("[main.py] 녹음 완료 후 LED 흰색 변경 시도...")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_WHITE)
        return True
    except FileNotFoundError:
        print("오류: 'arecord' 명령어를 찾을 수 없습니다. 'alsa-utils' 패키지가 설치되어 있나요?")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False
    except subprocess.CalledProcessError as e:
        print(f"오류: 녹음 중 오류 발생 (종료 코드: {e.returncode})")
        print(f"arecord 오류 출력:\n{e.stderr}")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False
    except Exception as e:
        print(f"오류: 예상치 못한 녹음 오류 발생: {e}")
        traceback.print_exc()
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False

def get_stt_from_server(audio_filename):
    """녹음된 오디오 파일을 PC 서버 /stt 로 보내 텍스트를 받습니다."""
    stt_url = f"{PC_SERVER_URL}/stt"
    print(f"오디오 파일 '{audio_filename}'을 STT 서버({stt_url})로 전송 중...")
    print("[main.py] STT 요청 시 LED 노란색 변경 시도...")
    if led_controller: led_controller.set_led_color(led_controller.COLOR_YELLOW)
    try:
        if not os.path.exists(audio_filename):
            print(f"오류: STT 요청 실패 - 오디오 파일 '{audio_filename}' 없음")
            if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
            return None

        print(f"  -> 전송할 파일 크기: {os.path.getsize(audio_filename)} bytes")

        with open(audio_filename, 'rb') as f_audio:
            files = {'audio_file': (os.path.basename(audio_filename), f_audio)}
            response = requests.post(stt_url, files=files, timeout=30)
        response.raise_for_status()
        result_json = response.json()
        transcribed_text = result_json.get("text")
        if transcribed_text is not None:
            print(f"STT 결과 수신: '{transcribed_text}'")
            print("[main.py] STT 결과 수신 후 LED 흰색 변경 시도...")
            if led_controller: led_controller.set_led_color(led_controller.COLOR_WHITE)
            return transcribed_text
        else:
            print(f"오류: STT 결과 JSON에 'text' 필드가 없습니다. 서버 응답: {result_json}")
            if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
            return None
    except FileNotFoundError:
        print(f"오류: 오디오 파일 '{audio_filename}'을 열 수 없습니다.")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return None
    except requests.exceptions.Timeout:
        print(f"오류: STT 서버({stt_url}) 연결 시간 초과 (30초)")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return None
    except requests.exceptions.RequestException as e:
        print(f"오류: STT 서버({stt_url}) 통신 오류: {e}")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return None
    except json.JSONDecodeError:
        print(f"오류: STT 서버 응답이 유효한 JSON 형식이 아닙니다. 응답 내용:\n{response.text}")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return None
    except Exception as e:
        print(f"오류: 예상치 못한 STT 처리 오류: {e}")
        traceback.print_exc()
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return None

def get_tts_audio_from_server(text_to_speak, output_filename=RESPONSE_AUDIO_FILENAME):
    """텍스트를 PC 서버 /generate_tts 로 보내 WAV 오디오를 받아 저장합니다."""
    tts_url = f"{PC_SERVER_URL}/generate_tts"
    print(f"텍스트 '{text_to_speak[:30]}...'를 TTS 서버({tts_url})로 전송 중...")
    print("[main.py] TTS 요청 시 LED 노란색 변경 시도...")
    if led_controller: led_controller.set_led_color(led_controller.COLOR_YELLOW)
    payload = {"text": text_to_speak, "lang": "ko"}
    try:
        response = requests.post(tts_url, json=payload, timeout=30, stream=True)
        response.raise_for_status()
        if 'audio/wav' in response.headers.get('Content-Type', ''):
            if os.path.exists(output_filename): os.remove(output_filename)
            with open(output_filename, 'wb') as f_out:
                for chunk in response.iter_content(chunk_size=8192):
                    f_out.write(chunk)
            print(f"TTS 오디오 저장 완료: {output_filename}")
            print("[main.py] TTS 완료 후 LED 흰색 변경 시도...")
            if led_controller: led_controller.set_led_color(led_controller.COLOR_WHITE)
            return True
        else:
            print(f"오류: TTS 서버가 오디오 파일을 반환하지 않았습니다.")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            try: print(f"서버 응답: {response.text}")
            except Exception: pass
            if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
            return False
    except requests.exceptions.Timeout:
        print(f"오류: TTS 서버({tts_url}) 연결 시간 초과 (30초)")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False
    except requests.exceptions.RequestException as e:
        print(f"오류: TTS 서버({tts_url}) 통신 오류: {e}")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False
    except Exception as e:
        print(f"오류: 예상치 못한 TTS 처리 오류: {e}")
        traceback.print_exc()
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False

def play_audio(filename=RESPONSE_AUDIO_FILENAME):
    """aplay 명령어를 사용하여 오디오 파일을 재생합니다."""
    print(f"오디오 파일 재생 시작: {filename}")
    print("[main.py] 오디오 재생 시 LED 초록색 변경 시도...")
    if led_controller: led_controller.set_led_color(led_controller.COLOR_GREEN)
    command = ['aplay', filename]
    try:
        if not os.path.exists(filename):
            print(f"오류: 재생할 오디오 파일 '{filename}' 없음")
            if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
            return False
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("오디오 파일 재생 완료.")
        print("[main.py] 오디오 재생 완료 후 LED 흰색 변경 시도...")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_WHITE)
        return True
    except FileNotFoundError:
        print("오류: 'aplay' 명령어를 찾을 수 없습니다. 'alsa-utils' 패키지가 설치되어 있나요?")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False
    except subprocess.CalledProcessError as e:
        print(f"오류: 오디오 재생 중 오류 발생 (종료 코드: {e.returncode})")
        print(f"aplay 오류 출력:\n{e.stderr}")
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False
    except Exception as e:
        print(f"오류: 예상치 못한 오디오 재생 오류: {e}")
        traceback.print_exc()
        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
        return False

def analyze_emotion_and_set_led(text):
    """입력된 텍스트에서 감정 키워드를 찾아 LED 색상을 설정하고, 감지된 경우 잠시 해당 색상을 유지합니다."""
    if led_controller is None:
        print("[main.py] 감정 분석: LED 컨트롤러 없음.")
        return

    emotion_detected = False
    target_color = None

    if "우울" in text:
        print("[main.py] 감정 감지: 우울 -> 파란색 설정 시도")
        target_color = led_controller.COLOR_BLUE
        emotion_detected = True
    elif "예민" in text or "짜증" in text:
        print("[main.py] 감정 감지: 예민/짜증 -> 빨간색 설정 시도")
        target_color = led_controller.COLOR_RED
        emotion_detected = True
    elif "안정" in text or "차분" in text or "평온" in text:
        print("[main.py] 감정 감지: 안정/차분 -> 초록색 설정 시도")
        target_color = led_controller.COLOR_GREEN
        emotion_detected = True
    elif "기뻐" in text or "행복" in text or "신나" in text:
        print("[main.py] 감정 감지: 기쁨/행복 -> 노란색 설정 시도")
        target_color = led_controller.COLOR_YELLOW
        emotion_detected = True
    else:
        print("[main.py] 감정 감지: 특정 감정 키워드 없음")

    if emotion_detected and target_color:
        led_controller.set_led_color(target_color)
        print("감정 LED 색상 1초간 유지...")
        time.sleep(1)

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    print("\n========================================")
    print("      음성 대화 시스템 시작")
    print("========================================")

    power_on_success = False
    if led_controller:
        print("LED 컨트롤러 활성화됨. LED 전원 켜기 시도...")
        power_on_result = led_controller.power_on()
        print(f"  -> led_controller.power_on() 반환값: {power_on_result}")
        if power_on_result:
             print("LED 전원 켜기 성공. (대기: 흰색 설정 시도)")
             led_controller.set_led_color(led_controller.COLOR_WHITE)
             power_on_success = True
        else:
             print("경고: LED 전원을 켜지 못했습니다. LED가 작동하지 않을 수 있습니다.")
    else:
        print("LED 기능이 비활성화된 상태로 실행됩니다.")

    if led_controller and power_on_success:
         print("\n--- [테스트] 직접 LED 색상 변경 시작 ---")
         try:
             print("  -> 빨간색 설정 시도...")
             led_controller.set_led_color(led_controller.COLOR_RED)
             time.sleep(2)
             print("  -> 초록색 설정 시도...")
             led_controller.set_led_color(led_controller.COLOR_GREEN)
             time.sleep(2)
             print("  -> 파란색 설정 시도...")
             led_controller.set_led_color(led_controller.COLOR_BLUE)
             time.sleep(2)
             print("  -> 색상 OFF 시도...")
             led_controller.turn_off_leds_only()
             time.sleep(1)
             print("  -> 테스트 후 대기 색상(흰색) 설정 시도...")
             led_controller.set_led_color(led_controller.COLOR_WHITE)
             print("--- [테스트] 직접 LED 색상 변경 완료 ---\n")
         except Exception as led_test_err:
             print(f"!!! 직접 LED 테스트 중 오류 발생: {led_test_err}")
             traceback.print_exc()

    first_run = True
    while True:
        try:
            print("\n----------------------------------------")
            if first_run:
                print("시스템 준비 완료. 잠시 후 첫 녹음을 시작합니다...")
                time.sleep(2)
                first_run = False
            print("음성 입력을 기다립니다...")

            # 1. 음성 녹음 (수정된 rate 사용)
            if record_audio():
                # 2. STT 요청 및 결과 처리
                stt_text = get_stt_from_server(RECORDED_AUDIO_FILENAME)

                # --- ★★★ STT 결과 유효성 검사 추가 ★★★ ---
                if stt_text is not None and len(stt_text.strip()) > 1: # 비어있지 않고, 최소 2글자 이상일 때만 처리 (예시 조건)
                    print(f"인식된 텍스트: '{stt_text}' (처리 진행)")
                    response_text = ""
                    analyze_emotion_and_set_led(stt_text)

                    # 3. 텍스트 처리 (날씨 또는 LLM)
                    if ("날씨" in stt_text or "기온" in stt_text or "온도" in stt_text) and weather_module:
                        print("날씨 관련 키워드 감지됨. 날씨 정보 조회 시도...")
                        target_city = weather_module.DEFAULT_CITY_KO
                        words = stt_text.split()
                        for city_ko in weather_module.CITY_NAME_MAP_KO_EN.keys():
                            if city_ko in words:
                                target_city = city_ko; print(f"-> 대상 도시 감지: {target_city}"); break
                        if "여기" in words or "현재" in words or "지금" in words:
                            target_city = 'auto'; print("-> 현재 위치 날씨 요청 감지")
                        response_text = weather_module.get_weather(target_city)
                        print(f"-> 날씨 정보 조회 결과: {response_text if response_text else '정보 없음'}")
                    elif language_model:
                        print("LLM 응답 생성 시도...")
                        print("[main.py] LLM 요청 시 LED 노란색 변경 시도...")
                        if led_controller: led_controller.set_led_color(led_controller.COLOR_YELLOW)
                        response_text = language_model.get_llm_response(stt_text)
                        print("[main.py] LLM 완료 후 LED 흰색 변경 시도...")
                        if led_controller: led_controller.set_led_color(led_controller.COLOR_WHITE)
                    else:
                        response_text = "죄송합니다. 날씨나 일반 대화 기능을 사용할 수 없습니다."

                    # 4. 응답 생성 확인 및 TTS/재생
                    if not response_text:
                        response_text = "죄송합니다. 요청을 처리하지 못했습니다."
                    print(f"생성된 응답: '{response_text}'")
                    if get_tts_audio_from_server(response_text):
                        play_audio()
                    else:
                        print("TTS 오디오 생성에 실패하여 재생할 수 없습니다.")
                        if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)

                # --- ★★★ STT 결과가 짧거나 비어있는 경우 처리 ★★★ ---
                elif stt_text is not None:
                    print(f"인식된 텍스트가 너무 짧거나 비어있습니다: '{stt_text}' (처리 건너<0xEB><0x85>).")
                    if led_controller: led_controller.set_led_color(led_controller.COLOR_WHITE) # 대기 상태로
                # --- ★★★ STT 실패 경우 ★★★ ---
                else:
                    print("STT 변환 실패. (처리 건너<0xEB><0x85>).")
                    # 오류 시 RED는 get_stt_from_server 에서 처리됨

            # 음성 녹음 실패 시
            else:
                print("오디오 녹음에 실패했습니다. 마이크 연결 및 설정을 확인하세요.")

            # --- 루프 마지막 정리 ---
            if os.path.exists(RECORDED_AUDIO_FILENAME):
                print(f"[main loop] 임시 녹음 파일 '{RECORDED_AUDIO_FILENAME}' 삭제 시도...")
                try:
                    os.remove(RECORDED_AUDIO_FILENAME)
                    print(f"[main loop] 임시 녹음 파일 삭제 완료.")
                except OSError as e:
                    print(f"경고: 임시 녹음 파일 삭제 오류: {e}")
                    traceback.print_exc()
            else:
                 print(f"[main loop] 임시 녹음 파일 '{RECORDED_AUDIO_FILENAME}' 이미 없음.")

            print("다음 사이클까지 3초 대기...")
            time.sleep(3)

        except KeyboardInterrupt:
            print("\nCtrl+C 입력 감지. 프로그램을 종료합니다.")
            break
        except Exception as main_loop_error:
            print(f"\n!!! 메인 루프에서 심각한 오류 발생: {main_loop_error} !!!")
            traceback.print_exc()
            if led_controller: led_controller.set_led_color(led_controller.COLOR_RED)
            print("5초 후 다음 사이클을 시도합니다...")
            time.sleep(5)

    # --- 프로그램 종료 처리 ---
    print("\n========================================")
    print("      음성 대화 시스템 종료")
    print("========================================")
    if led_controller:
        print("LED 컨트롤러 정리 작업 수행...")
        led_controller.cleanup()
    else:
        print("LED 컨트롤러가 없어 정리 작업을 건너<0xEB><0x85>니다.")
    print("안녕히 가세요!")
