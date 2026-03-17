import board
import neopixel
import time
# RPi.GPIO 라이브러리 추가
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("오류: RPi.GPIO 라이브러리를 import할 수 없습니다. sudo로 실행했는지, 라이브러리가 설치되었는지 확인하세요.")
    # 개발 환경 등에서 GPIO 라이브러리 없이 테스트할 경우를 위해 더미 클래스 정의 가능
    # 예: class GPIO: BCM=0; OUT=0; LOW=0; HIGH=1; setmode=lambda *_:None; setup=lambda *_:None; output=lambda *_:None; cleanup=lambda *_:None;
    exit() # 실제 라즈베리파이 환경에서는 종료하는 것이 좋음

# --- 설정 ---
# NeoPixel 설정
LED_COUNT = 60       # 1미터 스트립의 LED 개수
LED_PIN = board.D10  # NeoPixel 데이터 핀 (BCM 10) - 주석과 일치하도록 수정
BRIGHTNESS = 0.3     # 밝기 (0.0 ~ 1.0)
ORDER = neopixel.GRB # 네오픽셀 색상 순서

# MOSFET 제어 설정
MOSFET_PIN = 21      # MOSFET 게이트에 연결된 라즈베리파이 GPIO 핀 번호 (BCM 모드 기준)

# --- 전역 변수 ---
pixels = None        # NeoPixel 객체
is_initialized = False # 초기화 성공 여부 플래그
is_power_on = False   # 현재 LED 전원 상태 (MOSFET 기준)

# --- 색상 상수 정의 ---
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_OFF = (0, 0, 0)
# 필요한 다른 색상도 추가 가능

# --- 초기화 함수 ---
def initialize():
    """ 하드웨어(GPIO for MOSFET, NeoPixel)를 초기화합니다. """
    global pixels, is_initialized, is_power_on
    if is_initialized:
        print("이미 초기화되었습니다.")
        return True

    try:
        # 1. MOSFET 제어용 GPIO 초기화
        print(f"MOSFET 제어 핀(GPIO {MOSFET_PIN}) 초기화 시도...")
        # 경고 메시지 비활성화 (선택 사항)
        # GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM) # BCM 핀 번호 모드 사용
        GPIO.setup(MOSFET_PIN, GPIO.OUT) # 출력 모드로 설정
        GPIO.output(MOSFET_PIN, GPIO.LOW) # 초기 상태: 전원 OFF
        print(f"MOSFET 제어 핀 초기화 완료 (초기 전원 OFF 상태)")
        is_power_on = False # 전원 상태 초기화

        # 2. NeoPixel 초기화
        print(f"NeoPixel(GPIO {LED_PIN}, {LED_COUNT}개) 초기화 시도...")
        pixels = neopixel.NeoPixel(
            LED_PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False, pixel_order=ORDER
        )
        pixels.fill(COLOR_OFF) # 초기 색상 OFF
        pixels.show()
        print("NeoPixel 초기화 성공!")

        is_initialized = True
        print("LED 컨트롤러 초기화 완료.")
        return True

    except Exception as e:
        print(f"오류: 초기화 실패 - {e}")
        pixels = None
        is_initialized = False
        # 부분적으로 성공했을 수 있으므로 cleanup 시도
        try:
            GPIO.cleanup()
        except Exception: # cleanup 실패는 무시
            pass
        return False

# --- 전원 제어 함수 ---
def power_on():
    """ MOSFET을 통해 LED 스트립의 주 전원을 켭니다. """
    global is_power_on
    if not is_initialized:
        print("경고: 초기화되지 않아 전원을 켤 수 없습니다.")
        return False
    if is_power_on:
        # print("이미 전원이 켜져 있습니다.") # 필요하면 주석 해제
        return True

    try:
        print("LED 전원 ON")
        GPIO.output(MOSFET_PIN, GPIO.HIGH) # MOSFET 게이트에 HIGH 신호 인가
        is_power_on = True
        time.sleep(0.1) # 전원 안정화 대기 시간
        return True
    except Exception as e:
        print(f"오류: LED 전원 켜기 실패 - {e}")
        is_power_on = False # 실패 시 상태 업데이트
        return False

def power_off():
    """ MOSFET을 통해 LED 스트립의 주 전원을 끕니다. """
    global is_power_on
    if not is_initialized:
        # print("경고: 초기화되지 않았습니다.") # 필요하면 주석 해제
        # 안전을 위해 혹시 모를 GPIO 출력을 LOW로 설정 시도 (선택 사항)
        # try:
        #     GPIO.output(MOSFET_PIN, GPIO.LOW)
        # except Exception: pass
        return False
    if not is_power_on:
        # print("이미 전원이 꺼져 있습니다.") # 필요하면 주석 해제
        return True

    try:
        print("LED 전원 OFF")
        # 전원 끄기 전에 LED 색상도 OFF (선택 사항)
        if pixels:
            pixels.fill(COLOR_OFF)
            pixels.show()
            time.sleep(0.05) # show() 반영 시간

        GPIO.output(MOSFET_PIN, GPIO.LOW) # MOSFET 게이트에 LOW 신호 인가
        is_power_on = False
        time.sleep(0.1) # 상태 변경 시간
        return True
    except Exception as e:
        print(f"오류: LED 전원 끄기 실패 - {e}")
        # 전원 상태는 불확실해질 수 있으나, OFF 시도했으므로 False로 설정
        is_power_on = False
        return False

# --- LED 색상 제어 함수 ---
def set_led_color(color):
    """
    LED 스트립 전체를 지정된 색상으로 변경합니다.
    LED 전원이 켜져 있어야 실제로 반영됩니다. (power_on() 호출 필요)
    """
    if not is_initialized or pixels is None:
        print("경고: LED가 초기화되지 않아 색상을 설정할 수 없습니다.")
        return
    if not is_power_on:
        print("경고: LED 전원이 꺼져있어 색상이 반영되지 않습니다. power_on()을 먼저 호출하세요.")
        # 전원이 꺼져있어도 내부 버퍼에는 색상 값을 써 놓을 수는 있음 (선택)
        # pixels.fill(color)
        return

    try:
        pixels.fill(color)
        pixels.show()
    except Exception as e:
        print(f"오류: LED 색상 설정 중 문제 발생 - {e}")

def turn_off_leds_only():
    """ 전원은 유지한 채 LED 색상만 끕니다 (검정색으로 설정). """
    set_led_color(COLOR_OFF)

# --- 정리 함수 ---
def cleanup():
    """ 모든 리소스를 정리하고 전원을 차단합니다. 프로그램 종료 시 호출해주세요. """
    global is_initialized, pixels, is_power_on
    print("정리 작업 시작...")
    if is_initialized:
        try:
            # 1. LED 색상 끄기 (전원이 켜져 있다면)
            if is_power_on and pixels:
                print("LED 색상 OFF 설정...")
                pixels.fill(COLOR_OFF)
                pixels.show()
                time.sleep(0.05)
        except Exception as e:
            print(f"경고: LED 색상 끄는 중 오류 - {e}")

        # 2. 전원 끄기 (MOSFET)
        print("MOSFET 전원 OFF 시도...")
        power_off() # 내부적으로 전원 OFF 처리 및 is_power_on 업데이트

        # 3. GPIO 정리
        try:
            print("GPIO 정리...")
            GPIO.cleanup()
            print("GPIO 정리 완료.")
        except Exception as e:
            print(f"경고: GPIO 정리 중 오류 - {e}")

        pixels = None # 객체 참조 해제
        is_initialized = False
        print("LED 컨트롤러 리소스 정리 완료.")
    else:
        # 초기화 안 됐어도 혹시 모르니 cleanup 시도 (주로 GPIO)
        try:
            GPIO.cleanup()
            print("GPIO 정리 시도 완료 (초기화 안됨 상태).")
        except RuntimeError: # 이미 cleanup 되었거나 setup 안 된 경우
             pass
        except Exception as e:
            print(f"경고: GPIO 정리 중 오류 (초기화 안됨 상태) - {e}")
        print("정리 작업 완료 (초기화되지 않은 상태).")

# --- 메인 스크립트에서 사용 예시 (이 파일 자체를 직접 실행할 경우) ---
if __name__ == "__main__":
    print("--- led_controller.py 직접 실행 테스트 ---")

    # 테스트를 위해 초기화 시도
    if initialize():
        try:
            # 전원 켜기 필수!
            print("\n[테스트] LED 전원 켜기")
            if power_on():

                print("\n[테스트] 빨간색 설정")
                set_led_color(COLOR_RED)
                time.sleep(2)

                print("\n[테스트] 초록색 설정")
                set_led_color(COLOR_GREEN)
                time.sleep(2)

                print("\n[테스트] LED 색상만 끄기 (전원은 유지)")
                turn_off_leds_only()
                time.sleep(2)

                print("\n[테스트] 흰색 설정")
                set_led_color(COLOR_WHITE)
                time.sleep(2)

                print("\n[테스트] LED 전원 끄기")
                power_off()
                time.sleep(1)

                print("\n[테스트] 전원 꺼진 상태에서 색상 설정 시도 (경고 메시지 확인)")
                set_led_color(COLOR_BLUE) # 전원이 꺼져있어 반영 안됨
                time.sleep(1)

                print("\n[테스트] 다시 전원 켜고 파란색 설정")
                power_on()
                set_led_color(COLOR_BLUE)
                time.sleep(2)

            else:
                print("오류: 전원을 켤 수 없어 테스트 중단.")

        except KeyboardInterrupt:
            print("\n사용자에 의해 테스트 중단됨")
        finally:
            # 프로그램 종료 시 반드시 cleanup 호출!
            print("\n[테스트] 최종 정리 작업 호출")
            cleanup()
    else:
        print("오류: LED 컨트롤러 초기화 실패로 테스트를 진행할 수 없습니다.")

    print("--- 테스트 종료 ---")
