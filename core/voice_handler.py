"""
음성 인식(STT) 및 음성 합성(TTS) 모듈 (core 패키지)
Whisper를 사용한 STT와 pyttsx3를 사용한 TTS를 제공합니다.
"""
from typing import Optional
import threading

# 선택적 의존성 import
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    pyttsx3 = None


class VoiceHandler:
    """음성 인식 및 합성 핸들러"""
    
    def __init__(self):
        """VoiceHandler 초기화"""
        # Whisper 모델 로드 (base 모델 사용, 필요시 변경 가능)
        self.whisper_model = None
        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
            except Exception as e:
                print(f"Whisper 모델 로드 실패: {e}")
        else:
            print("⚠️ Whisper가 설치되지 않았습니다. STT 기능을 사용할 수 없습니다.")
        
        # TTS 엔진 초기화
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                # 한국어 음성 설정 (시스템에 한국어 음성이 설치되어 있어야 함)
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'korean' in voice.name.lower() or 'ko' in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                # 속도 설정 (기본값: 200)
                self.tts_engine.setProperty('rate', 150)
            except Exception as e:
                print(f"TTS 엔진 초기화 실패: {e}")
        else:
            print("⚠️ pyttsx3가 설치되지 않았습니다. TTS 기능을 사용할 수 없습니다.")
    
    def speech_to_text(self, audio_file_path: str) -> Optional[str]:
        """
        음성 파일을 텍스트로 변환 (STT)
        
        Args:
            audio_file_path: 음성 파일 경로
            
        Returns:
            인식된 텍스트 또는 None
        """
        if not self.whisper_model:
            return None
        
        try:
            result = self.whisper_model.transcribe(audio_file_path, language="ko")
            return result["text"].strip()
        except Exception as e:
            print(f"STT 오류: {e}")
            return None
    
    def text_to_speech(self, text: str, async_mode: bool = True):
        """
        텍스트를 음성으로 변환 (TTS)
        
        Args:
            text: 변환할 텍스트
            async_mode: 비동기 모드 (기본값: True)
        """
        if not self.tts_engine:
            return
        
        try:
            if async_mode:
                # 비동기로 실행하여 UI 블로킹 방지
                thread = threading.Thread(target=self._speak, args=(text,))
                thread.daemon = True
                thread.start()
            else:
                self._speak(text)
        except Exception as e:
            print(f"TTS 오류: {e}")
    
    def _speak(self, text: str):
        """내부 TTS 실행 메서드"""
        if self.tts_engine:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
    
    def set_tts_rate(self, rate: int):
        """
        TTS 속도 설정
        
        Args:
            rate: 속도 (50-300, 기본값: 150)
        """
        if self.tts_engine:
            self.tts_engine.setProperty('rate', max(50, min(300, rate)))
    
    def set_tts_volume(self, volume: float):
        """
        TTS 볼륨 설정
        
        Args:
            volume: 볼륨 (0.0-1.0)
        """
        if self.tts_engine:
            self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))


