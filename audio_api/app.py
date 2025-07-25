# -*- coding: utf-8 -*-
import os
import whisper # STT
from gtts import gTTS # TTS
from pydub import AudioSegment # Audio conversion
from flask import Flask, request, jsonify, send_file # Web framework
import tempfile # For temporary files
import io # For sending file data from memory

# --- 설정 ---
WHISPER_MODEL_NAME = "large"
# --- 추가: 표준 오디오 샘플 레이트 설정 ---
TARGET_SAMPLE_RATE = 44100 # 또는 16000
# ------------------------------------

# --- Flask 앱 초기화 ---
app = Flask(__name__)

# --- Whisper 모델 로드 ---
print(f"Whisper 모델 로딩 중: {WHISPER_MODEL_NAME}...")
whisper_model = None
try:
    if os.system("ffmpeg -version > nul 2>&1" if os.name == 'nt' else "ffmpeg -version > /dev/null 2>&1") != 0:
         print("경고: ffmpeg가 설치되지 않았거나 PATH에 없습니다. Whisper/Pydub 작동에 실패할 수 있습니다.")
         print("ffmpeg를 설치하고 환경 변수 PATH에 추가해주세요. (https://ffmpeg.org/download.html)")

    whisper_model = whisper.load_model(WHISPER_MODEL_NAME)
    print(f"Whisper 모델 '{WHISPER_MODEL_NAME}' 로드 완료.")
except Exception as e:
    print(f"Whisper 모델 로딩 오류: {e}")
    print("torch 등 관련 라이브러리가 올바르게 설치되었는지 확인하세요.")

# --- API 엔드포인트 ---

@app.route('/')
def index():
    return jsonify({"status": "Audio API 서버 실행 중!"})

@app.route('/generate_tts', methods=['POST'])
def generate_tts():
    """
    텍스트를 입력받아 gTTS와 Pydub을 이용해 TTS 오디오(WAV) 생성.
    WAV 파일을 표준 샘플 레이트(예: 44100Hz)로 변환하여 반환.
    """
    if not request.is_json:
        return jsonify({"error": "JSON 형식 요청이 필요합니다"}), 400

    data = request.get_json()
    text = data.get('text')
    lang = data.get('lang', 'ko')

    if not text:
        return jsonify({"error": "텍스트가 없습니다"}), 400

    print(f"TTS 요청 수신: lang='{lang}', text='{text[:50]}...'")

    try:
        # 1. gTTS로 MP3 오디오를 메모리에 생성
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang=lang)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # 2. Pydub으로 MP3를 WAV로 변환 (샘플 레이트 지정 추가!)
        audio = AudioSegment.from_mp3(mp3_fp)
        wav_fp = io.BytesIO()
        # --- 수정된 부분: parameters=["-ar", str(TARGET_SAMPLE_RATE)] 추가 ---
        # frame_rate=TARGET_SAMPLE_RATE 로 직접 지정해도 됩니다.
        audio.export(wav_fp, format="wav", parameters=["-ar", str(TARGET_SAMPLE_RATE)])
        # 또는: audio.export(wav_fp, format="wav", frame_rate=TARGET_SAMPLE_RATE)
        # -------------------------------------------------------------------
        wav_fp.seek(0)

        print(f"TTS 생성 완료 (Sample Rate: {TARGET_SAMPLE_RATE} Hz).")

        # 3. WAV 파일 응답 전송
        return send_file(
            wav_fp,
            mimetype='audio/wav',
            as_attachment=False
        )

    except Exception as e:
        print(f"TTS 생성 중 오류 발생: {e}")
        return jsonify({"error": f"TTS 생성 실패: {e}"}), 500

@app.route('/stt', methods=['POST'])
def speech_to_text():
    """
    오디오 파일을 입력받아 Whisper를 이용해 STT 수행.
    """
    if whisper_model is None:
         return jsonify({"error": "Whisper 모델이 로드되지 않았습니다"}), 500

    if 'audio_file' not in request.files:
        return jsonify({"error": "요청에 'audio_file' 파트가 없습니다"}), 400

    file = request.files['audio_file']

    if file.filename == '':
        return jsonify({"error": "오디오 파일이 선택되지 않았습니다"}), 400

    print(f"STT 요청 수신: filename='{file.filename}'")

    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(file.filename)[1]) as temp_audio:
            file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
            print(f"오디오 파일 임시 저장: {temp_audio_path}")

            # --- 수정된 부분: language='ko' 추가 ---
            result = whisper_model.transcribe(temp_audio_path, language='ko')
            # ------------------------------------
            transcribed_text = result["text"]

            print(f"STT 변환 완료. Text: {transcribed_text[:100]}...")

            return jsonify({"text": transcribed_text})

    except Exception as e:
        print(f"STT 처리 중 오류 발생: {e}")
        return jsonify({"error": f"STT 처리 실패: {e}"}), 500

# --- 앱 실행 ---
if __name__ == '__main__':
    print("Flask 서버 시작 (host: 0.0.0.0, port: 5001)...")
    app.run(host='0.0.0.0', port=5001, debug=False)

