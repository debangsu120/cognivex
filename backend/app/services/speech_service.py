"""Speech-to-Text Service using Deepgram and OpenAI Whisper."""

import io
import asyncio
from typing import Optional, Dict, Any
from enum import Enum

from app.config import settings
from app.exceptions import AIException


class STTProvider(str, Enum):
    """Speech-to-text provider options."""
    DEEPGRAM = "deepgram"
    WHISPER = "whisper"


class SpeechService:
    """Service for converting audio to text using STT providers."""

    def __init__(self):
        """Initialize the speech service with available providers."""
        self.deepgram_api_key = settings.deepgram_api_key
        self.provider = STTProvider.DEEPGRAM if self.deepgram_api_key else STTProvider.WHISPER

    async def transcribe_audio(
        self,
        audio_data: Optional[bytes] = None,
        audio_url: Optional[str] = None,
        language: str = "en",
        provider: Optional[STTProvider] = None
    ) -> Dict[str, Any]:
        """Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes
            audio_url: URL to audio file
            language: Language code (default: en)
            provider: STT provider to use (auto-detected if not provided)

        Returns:
            Dictionary containing:
                - transcript: Transcribed text
                - confidence: Confidence score
                - words: List of word-level timestamps
                - provider: Provider used
        """
        if provider:
            self.provider = provider

        if self.provider == STTProvider.DEEPGRAM:
            return await self._transcribe_deepgram(audio_data, audio_url, language)
        else:
            return await self._transcribe_whisper(audio_data, audio_url, language)

    async def _transcribe_deepgram(
        self,
        audio_data: Optional[bytes],
        audio_url: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """Transcribe using Deepgram API.

        Args:
            audio_data: Raw audio bytes
            audio_url: URL to audio file
            language: Language code

        Returns:
            Transcription result
        """
        if not self.deepgram_api_key:
            # Fallback to Whisper if no Deepgram key
            return await self._transcribe_whisper(audio_data, audio_url, language)

        try:
            import json

            # Build Deepgram API request
            headers = {
                "Authorization": f"Token {self.deepgram_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "tier": "enhanced",
                "language": language,
                "punctuate": True,
                "format": "multi",
                "diarize": False,
                "utterances": False,
                "paragraphs": True
            }

            # Use URL if provided, otherwise use upload
            if audio_url:
                payload["url"] = audio_url

            import httpx
            async with httpx.AsyncClient() as client:
                if audio_url:
                    # Transcribe from URL
                    response = await client.post(
                        "https://api.deepgram.com/v1/listen",
                        headers=headers,
                        json=payload
                    )
                else:
                    # Upload audio file
                    files = {"audio": ("audio.wav", audio_data, "audio/wav")}
                    response = await client.post(
                        "https://api.deepgram.com/v1/listen",
                        headers={"Authorization": f"Token {self.deepgram_api_key}"},
                        files=files,
                        data={"tier": "enhanced", "language": language, "punctuate": True}
                    )

                if response.status_code != 200:
                    raise AIException(f"Deepgram API error: {response.text}")

                result = response.json()

                # Extract transcript
                transcript = ""
                confidence = 0.0
                words = []

                if "results" in result:
                    channels = result["results"].get("channels", [])
                    if channels:
                        alternatives = channels[0].get("alternatives", [])
                        if alternatives:
                            transcript = alternatives[0].get("transcript", "")
                            confidence = alternatives[0].get("confidence", 0.0)
                            words = alternatives[0].get("words", [])

                return {
                    "transcript": transcript,
                    "confidence": confidence,
                    "words": words,
                    "provider": STTProvider.DEEPGRAM.value
                }

        except ImportError:
            # Fallback to Whisper if httpx not available
            return await self._transcribe_whisper(audio_data, audio_url, language)
        except Exception as e:
            if "Deepgram" not in str(e):
                # Try Whisper fallback on generic errors
                return await self._transcribe_whisper(audio_data, audio_url, language)
            raise AIException(f"Deepgram transcription failed: {str(e)}")

    async def _transcribe_whisper(
        self,
        audio_data: Optional[bytes],
        audio_url: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API.

        Args:
            audio_data: Raw audio bytes
            audio_url: URL to audio file
            language: Language code

        Returns:
            Transcription result
        """
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI()

            if audio_url:
                # Transcribe from URL using Whisper
                # Note: OpenAI Whisper API doesn't support URL directly,
                # would need to download first
                # For now, raise error if only URL provided without data
                if not audio_data:
                    raise AIException("Whisper requires audio data, not URL. Use Deepgram for URL transcription.")

            if not audio_data:
                raise AIException("No audio data provided for transcription")

            # Create file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            # Transcribe using Whisper
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language if language != "en" else None
            )

            return {
                "transcript": response.text,
                "confidence": None,  # Whisper doesn't provide confidence
                "words": [],
                "provider": STTProvider.WHISPER.value
            }

        except ImportError:
            raise AIException("OpenAI package required for Whisper transcription. Install with: pip install openai")
        except Exception as e:
            raise AIException(f"Whisper transcription failed: {str(e)}")

    async def transcribe_from_file(
        self,
        file_path: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Transcribe audio from a file path.

        Args:
            file_path: Path to audio file
            language: Language code

        Returns:
            Transcription result
        """
        try:
            with open(file_path, "rb") as f:
                audio_data = f.read()
            return await self.transcribe_audio(audio_data=audio_data, language=language)
        except FileNotFoundError:
            raise AIException(f"Audio file not found: {file_path}")
        except Exception as e:
            raise AIException(f"Failed to read audio file: {str(e)}")

    async def analyze_audio_quality(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze audio quality metrics.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Audio quality analysis
        """
        # Basic audio analysis
        # In production, could use libraries like pydub or librosa
        try:
            import struct
            import wave

            # Read audio metadata
            audio_file = io.BytesIO(audio_data)
            with wave.open(audio_file, 'rb') as w:
                channels = w.getnchannels()
                sample_width = w.getsampwidth()
                frame_rate = w.getframerames()
                n_frames = w.getnframes()
                duration = n_frames / frame_rate if frame_rate else 0

            # Estimate quality metrics
            return {
                "duration_seconds": round(duration, 2),
                "channels": channels,
                "sample_width": sample_width,
                "frame_rate": frame_rate,
                "quality_score": self._calculate_quality_score(
                    channels, sample_width, frame_rate, duration
                ),
                "is_suitable_for_stt": duration > 0.5 and duration < 600  # 0.5s to 10min
            }

        except Exception:
            # Return basic info if analysis fails
            return {
                "duration_seconds": None,
                "channels": None,
                "sample_width": None,
                "frame_rate": None,
                "quality_score": None,
                "is_suitable_for_stt": True  # Assume suitable if can't analyze
            }

    def _calculate_quality_score(
        self,
        channels: int,
        sample_width: int,
        frame_rate: int,
        duration: float
    ) -> float:
        """Calculate a basic audio quality score.

        Args:
            channels: Number of audio channels
            sample_width: Sample width in bytes
            frame_rate: Frames per second
            duration: Duration in seconds

        Returns:
            Quality score 0-100
        """
        score = 0.0

        # Channel score (mono=50, stereo=100)
        score += 50 if channels == 1 else 100

        # Sample width (16-bit = good)
        score += 50 if sample_width >= 2 else 25

        # Frame rate (16kHz minimum for speech)
        if frame_rate >= 48000:
            score += 100
        elif frame_rate >= 16000:
            score += 75
        elif frame_rate >= 8000:
            score += 50
        else:
            score += 25

        return round(score / 3, 2)


# Singleton instance
speech_service = SpeechService()
