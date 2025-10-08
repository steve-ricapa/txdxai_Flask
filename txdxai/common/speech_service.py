import os
import tempfile
import logging
from typing import Optional, Dict
import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger(__name__)


class SpeechService:
    """Azure Speech Service for Speech-to-Text and Text-to-Speech"""
    
    @staticmethod
    def transcribe_audio(
        audio_file_path: str,
        speech_key: str,
        region: str
    ) -> Dict[str, str]:
        """
        Transcribe audio file to text using Azure Speech-to-Text
        
        Args:
            audio_file_path: Path to the audio file (WAV, MP3, OGG)
            speech_key: Azure Speech API key
            region: Azure region (e.g., 'eastus', 'westeurope')
            
        Returns:
            Dictionary with 'text' and 'status'
        """
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=region
            )
            
            speech_config.speech_recognition_language = "es-ES"
            
            audio_config = speechsdk.AudioConfig(filename=audio_file_path)
            
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info(f"Transcribed text: {result.text}")
                return {
                    'text': result.text,
                    'status': 'success'
                }
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return {
                    'text': '',
                    'status': 'no_match',
                    'error': 'No se pudo reconocer ningún audio'
                }
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Speech recognition canceled: {cancellation_details.reason}")
                return {
                    'text': '',
                    'status': 'error',
                    'error': f'Error de reconocimiento: {cancellation_details.error_details}'
                }
            else:
                return {
                    'text': '',
                    'status': 'error',
                    'error': 'Estado de reconocimiento desconocido'
                }
                
        except Exception as e:
            logger.error(f"Error in transcribe_audio: {str(e)}")
            return {
                'text': '',
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def synthesize_speech(
        text: str,
        speech_key: str,
        region: str,
        voice_name: str = "es-ES-ElviraNeural"
    ) -> Dict[str, any]:
        """
        Convert text to speech using Azure Text-to-Speech
        
        Args:
            text: Text to convert to speech
            speech_key: Azure Speech API key
            region: Azure region (e.g., 'eastus', 'westeurope')
            voice_name: Azure neural voice name (default: es-ES-ElviraNeural)
            
        Returns:
            Dictionary with 'audio_data', 'status', and optional 'error'
        """
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=region
            )
            
            speech_config.speech_synthesis_voice_name = voice_name
            
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
            
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None
            )
            
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Speech synthesized for text: {text[:50]}...")
                return {
                    'audio_data': result.audio_data,
                    'status': 'success'
                }
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                error_msg = 'Error de síntesis de voz'
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg = f"Error: {cancellation_details.error_details}"
                    logger.error(f"Error details: {cancellation_details.error_details}")
                return {
                    'audio_data': None,
                    'status': 'canceled',
                    'error': error_msg
                }
            else:
                logger.error(f"Unexpected synthesis result: {result.reason}")
                return {
                    'audio_data': None,
                    'status': 'error',
                    'error': 'Estado de síntesis desconocido'
                }
                
        except Exception as e:
            logger.error(f"Error in synthesize_speech: {str(e)}")
            return {
                'audio_data': None,
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def synthesize_to_file(
        text: str,
        speech_key: str,
        region: str,
        output_path: str,
        voice_name: str = "es-ES-ElviraNeural"
    ) -> Dict[str, any]:
        """
        Convert text to speech and save to file
        
        Args:
            text: Text to convert to speech
            speech_key: Azure Speech API key
            region: Azure region
            output_path: Path where to save the audio file
            voice_name: Azure neural voice name
            
        Returns:
            Dictionary with 'status' and optional 'error' or 'file_path'
        """
        try:
            result = SpeechService.synthesize_speech(
                text=text,
                speech_key=speech_key,
                region=region,
                voice_name=voice_name
            )
            
            if result['status'] == 'success' and result['audio_data']:
                with open(output_path, 'wb') as f:
                    f.write(result['audio_data'])
                logger.info(f"Audio saved to {output_path}")
                return {
                    'status': 'success',
                    'file_path': output_path
                }
            else:
                return {
                    'status': 'error',
                    'error': result.get('error', 'No se pudo generar el audio')
                }
            
        except Exception as e:
            logger.error(f"Error saving audio to file: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
