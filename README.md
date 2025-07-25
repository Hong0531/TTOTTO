# TTOTTO 프로젝트

## 개요
- 본 프로젝트는 라즈베리파이, Flutter 앱, 오디오 API, DB 서버로 구성된 통합 시스템입니다.
- 주요 기능: 날씨 정보, 회원가입/로그인, 채팅, 오디오 녹음 등

## 폴더 구조
- `DBSERVER/` : Python 기반 DB 서버 (Flask)
- `flutter/` : Flutter 앱 및 내장 Flask API 서버
- `Raspberrypi/` : 라즈베리파이용 Python 코드
- `audio_api/` : 오디오 관련 Python API 서버

## 실행 방법

### 1. 환경 변수 설정
- 각 Python 서버(`DBSERVER`, `Raspberrypi`, `audio_api`)는 `.env` 파일을 사용합니다.
- 예시 (`.env`):
  ```
  OPENWEATHER_API_KEY=여기에_키_입력
  PC_SERVER_URL=http://your.server.url
  ```
- **flutter/lib/weather_screen.dart**의 `apiKey`는 하드코딩되어 있으니, 환경변수로 분리 후 불러오도록 수정 필요

### 2. 의존성 설치
- Python 서버: `pip install -r requirements.txt` (각 폴더별)
- Flutter 앱: `flutter pub get`

### 3. 서버 실행
- 각 폴더에서 Python 서버 실행: `python main.py` 또는 `python app.py`
- Flutter 앱 실행: `flutter run`

## 보안 및 배포 시 주의사항
- `.env` 파일 및 민감 정보는 절대 깃허브에 올리지 마세요.
- 비밀번호는 반드시 해시(예: bcrypt) 후 저장/비교하세요.
- API 키, 시크릿 등은 코드에 직접 작성하지 말고 환경변수로 관리하세요.
- `.gitignore`에 `.env` 및 기타 민감 파일 추가
