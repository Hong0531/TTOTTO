# -*- coding: utf-8 -*-
# 필요한 라이브러리를 가져옵니다.
import requests
import os
from dotenv import load_dotenv # .env 파일 사용을 위해 추가

# --- 설정 ---
# .env 파일 로드 시도
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
DEFAULT_CITY_KO = "군포" # 기본 도시 한국어 이름

# IP Geolocation 서비스 URL
IPINFO_URL = "https://ipinfo.io/json"
# --- 설정 끝 ---

# 도시 이름을 영어로 변환하는 딕셔너리 (확장 가능)
CITY_NAME_MAP_KO_EN = {
    "안양": "Anyang",
    "군포": "Gunpo",
    "서울": "Seoul",
    "부산": "Busan",
    "인천": "Incheon",
    # 필요한 도시 추가
}
# 영어 이름을 한국어로 변환하는 딕셔너리 (결과 출력용, 확장 가능)
CITY_NAME_MAP_EN_KO = {v: k for k, v in CITY_NAME_MAP_KO_EN.items()}


def get_location_from_ip():
    """
    IP 주소를 기반으로 현재 위치(도시 이름)를 추정합니다.

    Returns:
        tuple: (영어 도시 이름, 한국어 도시 이름) 또는 (None, None) 반환.
               한국어 이름 매핑이 없으면 영어 이름을 사용.
    """
    try:
        print("IP 주소 기반 현재 위치 조회 중...")
        response = requests.get(IPINFO_URL, timeout=5) # 5초 타임아웃 설정
        response.raise_for_status()
        data = response.json()
        city_en = data.get('city')

        if city_en:
            # 영어 도시 이름으로 한국어 이름 찾기 시도
            city_ko = CITY_NAME_MAP_EN_KO.get(city_en, city_en) # 없으면 영어 이름 그대로 사용
            print(f"현재 위치 추정 성공: {city_en} ({city_ko})")
            return city_en, city_ko
        else:
            print("오류: IP 정보에서 도시 이름을 찾을 수 없습니다.")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"IP 위치 조회 오류: {e}")
        return None, None
    except Exception as e:
        print(f"IP 위치 조회 중 예상치 못한 오류: {e}")
        return None, None

def get_weather(city_ko=DEFAULT_CITY_KO):
    """
    지정된 도시 또는 현재 위치('auto')의 날씨 정보를 가져옵니다.

    Args:
        city_ko (str): 날씨를 조회할 도시 이름 (한국어) 또는 'auto' (현재 위치).

    Returns:
        str: 날씨 정보 요약 문자열. 오류 발생 시 오류 메시지 반환.
    """
    # API 키 확인
    if not API_KEY or API_KEY == "your_api_key_here":
        return "오류: OpenWeatherMap API 키가 설정되지 않았습니다."

    city_en = None
    display_city_name = city_ko # 최종 출력에 사용할 도시 이름

    # 현재 위치 조회 요청인지 확인
    if city_ko.lower() == 'auto' or city_ko == '현재위치' or city_ko == '여기':
        print("현재 위치 날씨 조회 요청 감지됨.")
        city_en, display_city_name = get_location_from_ip()
        if not city_en:
            print("현재 위치 조회 실패. 기본 도시로 조회합니다.")
            city_en = CITY_NAME_MAP_KO_EN.get(DEFAULT_CITY_KO, DEFAULT_CITY_KO)
            display_city_name = DEFAULT_CITY_KO # 출력 이름도 기본값으로
    else:
        # 지정된 도시 이름 처리
        city_en = CITY_NAME_MAP_KO_EN.get(city_ko, city_ko)
        display_city_name = city_ko # 입력받은 한국어 이름 사용

    # 날씨 API 호출
    if not city_en: # city_en 결정에 실패한 경우
         return f"오류: 날씨를 조회할 도시를 결정할 수 없습니다 ({city_ko})."

    complete_url = f"{BASE_URL}appid={API_KEY}&q={city_en}&units=metric&lang=kr"

    try:
        print(f"날씨 정보 요청 ({display_city_name} / {city_en}): {complete_url}")
        response = requests.get(complete_url)
        response.raise_for_status()
        data = response.json()

        if data["cod"] != 404 and data["cod"] != "404":
            main_data = data["main"]
            weather_data = data["weather"][0]
            temperature = main_data["temp"]
            feels_like = main_data["feels_like"]
            humidity = main_data["humidity"]
            description = weather_data["description"]

            # 결과 문자열 생성 (display_city_name 사용)
            result_str = (
                f"{display_city_name}의 현재 날씨는 {description}이며, "
                f"온도는 {temperature:.1f}°C (체감온도: {feels_like:.1f}°C), "
                f"습도는 {humidity}% 입니다."
            )
            print(f"날씨 정보 수신 성공: {result_str}")
            return result_str
        else:
            print(f"오류: 도시 '{city_en}'(으)로 날씨 정보를 찾을 수 없습니다 (API 응답 코드: {data.get('cod', 'N/A')}).")
            return f"오류: '{display_city_name}' 도시의 날씨 정보를 찾을 수 없습니다."

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
             print(f"오류: 도시 '{city_en}'(으)로 날씨 정보를 찾을 수 없습니다 (HTTP 404).")
             return f"오류: '{display_city_name}' 도시의 날씨 정보를 찾을 수 없습니다."
        else:
             print(f"HTTP 오류 발생: {http_err}")
             return "오류: 날씨 정보를 가져오는 중 서버 문제가 발생했습니다."
    except requests.exceptions.RequestException as req_err:
        print(f"API 요청 오류 발생: {req_err}")
        return "오류: 날씨 정보를 가져오는 중 네트워크 문제가 발생했습니다."
    except KeyError as key_err:
        print(f"JSON 데이터 처리 오류: 필요한 키 '{key_err}'를 찾을 수 없습니다.")
        return "오류: 날씨 정보 형식이 올바르지 않습니다."
    except Exception as e:
        print(f"날씨 정보 조회 중 예상치 못한 오류 발생: {e}")
        return "오류: 날씨 정보를 가져오는 중 문제가 발생했습니다."

# --- 모듈 테스트 코드 ---
if __name__ == "__main__":
    print("날씨 정보 모듈 테스트를 시작합니다 (IP 위치 감지 기능 포함).")

    print("\n현재 위치 날씨 조회:")
    # 'auto' 또는 '현재위치' 또는 '여기'를 인자로 전달하여 테스트
    weather_info_current = get_weather('auto')
    print(weather_info_current)

    print("\n기본 도시(군포) 날씨 조회:")
    weather_info_gunpo = get_weather() # 인자 없으면 기본값(군포) 사용
    print(weather_info_gunpo)

    print("\n서울 날씨 조회:")
    weather_info_seoul = get_weather("서울")
    print(weather_info_seoul)

    print("\n없는 도시 조회 테스트:")
    weather_info_none = get_weather("없는도시")
    print(weather_info_none)

    print("\n날씨 정보 모듈 테스트 완료.")

