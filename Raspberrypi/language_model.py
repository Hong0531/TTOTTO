import requests
import os
import json
from dotenv import load_dotenv

# --- 설정 ---
# .env 파일 로드 시도
load_dotenv()

# LM Studio API 엔드포인트 URL (.env 파일 우선, 없으면 기본값 사용)
# 기본값은 OpenAI 호환 엔드포인트인 /v1/chat/completions 를 가정합니다.
# 사용자의 LM Studio 설정에 따라 경로(/v1/...)가 다를 수 있습니다.
DEFAULT_LM_STUDIO_BASE_URL = "http://121.139.20.242:15160/v1" # 사용자가 알려준 주소 기반
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", DEFAULT_LM_STUDIO_BASE_URL)
CHAT_ENDPOINT = f"{LM_STUDIO_URL}/chat/completions" # 채팅 완료 엔드포인트

# API 요청 타임아웃 (초)
REQUEST_TIMEOUT = 120 # LLM 응답은 시간이 걸릴 수 있으므로 길게 설정
# --- 설정 끝 ---

def get_llm_response(prompt, max_tokens=150, temperature=0.7):
    """
    LM Studio API에 프롬프트를 보내고 LLM의 응답을 받아옵니다.

    Args:
        prompt (str): 사용자 입력 또는 LLM에게 전달할 프롬프트.
        max_tokens (int): 생성할 최대 토큰 수.
        temperature (float): 샘플링 온도 (창의성 조절).

    Returns:
        str: LLM이 생성한 텍스트 응답. 오류 발생 시 None 반환.
    """
    if not LM_STUDIO_URL or "your_lm_studio_url" in LM_STUDIO_URL: # URL 설정 확인
         print("오류: LM Studio URL이 설정되지 않았습니다.")
         return None

    # OpenAI 호환 API 요청 헤더
    headers = {"Content-Type": "application/json"}

    # 요청 본문 (Payload) 구성
    # 시스템 메시지 등을 추가하여 LLM의 역할이나 응답 스타일을 지정할 수 있습니다.
    payload = {
        "model": "loaded-model", # LM Studio에서 로드된 모델 이름 (보통 지정 안해도 됨)
        "messages": [
            # {"role": "system", "content": "You are a helpful AI assistant."}, # 시스템 메시지 예시
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        # "stream": False # 스트리밍 응답 사용 안 함
    }

    try:
        print(f"LM Studio 요청 시작 (Endpoint: {CHAT_ENDPOINT})...")
        print(f"  - 프롬프트: {prompt[:50]}...") # 프롬프트 일부만 출력
        response = requests.post(CHAT_ENDPOINT, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # HTTP 오류 발생 시 예외 처리

        # 응답 JSON 파싱
        response_data = response.json()
        print("LM Studio 응답 수신 완료.")

        # 생성된 텍스트 추출
        # 응답 구조는 LM Studio 설정이나 모델에 따라 약간 다를 수 있습니다.
        # 일반적인 OpenAI 호환 응답 구조 기준:
        if "choices" in response_data and len(response_data["choices"]) > 0:
            message = response_data["choices"][0].get("message", {})
            content = message.get("content")
            if content:
                print(f"  - LLM 응답: {content[:50]}...") # 응답 일부만 출력
                return content.strip()
            else:
                print("오류: 응답 데이터에서 'content'를 찾을 수 없습니다.")
                print(f"  - 전체 응답: {response_data}")
                return None
        else:
            print("오류: 응답 데이터에서 'choices'를 찾을 수 없거나 비어 있습니다.")
            print(f"  - 전체 응답: {response_data}")
            return None

    except requests.exceptions.Timeout:
        print(f"오류: LM Studio API 요청 시간 초과 ({REQUEST_TIMEOUT}초)")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"LM Studio API 요청 오류 발생: {req_err}")
        print("LM Studio 서버가 실행 중이고 URL이 올바른지 확인하세요.")
        return None
    except json.JSONDecodeError as json_err:
        print(f"LM Studio 응답 JSON 파싱 오류: {json_err}")
        print(f"  - 수신된 응답 내용: {response.text}")
        return None
    except Exception as e:
        print(f"LLM 응답 처리 중 예상치 못한 오류 발생: {e}")
        return None

# --- 모듈 테스트 코드 ---
if __name__ == "__main__":
    # .env 파일 사용을 위해 python-dotenv 설치 필요
    print("LM Studio 연동 모듈 테스트를 시작합니다.")
    print(f"API 엔드포인트: {CHAT_ENDPOINT}")

    # LM Studio 서버가 실행 중이어야 합니다.
    test_prompt = "한국의 수도는 어디인가요?"
    print(f"\n테스트 프롬프트: '{test_prompt}'")

    llm_answer = get_llm_response(test_prompt)

    if llm_answer:
        print(f"\nLLM 응답 결과:\n{llm_answer}")
    else:
        print("\nLLM으로부터 응답을 받지 못했습니다.")

    print("\nLM Studio 연동 모듈 테스트 완료.")

