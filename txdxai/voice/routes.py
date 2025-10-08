import os
import tempfile
import logging
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from txdxai.db.models import AgentInstance
from txdxai.security.keys import verify_access_key
from txdxai.common.speech_service import SpeechService
from txdxai.extensions import db
from txdxai.voice import voice_bp
from datetime import datetime

logger = logging.getLogger(__name__)

ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'flac', 'webm'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS


def get_speech_credentials(company_id, agent_access_key):
    """
    Validate agent credentials and retrieve Speech config
    
    Returns:
        Tuple of (agent_instance, speech_key, error_response)
        error_response is None if successful
    """
    instances = AgentInstance.query.filter_by(
        company_id=company_id,
        agent_type='SOPHIA',
        status='ACTIVE'
    ).all()
    
    if not instances:
        return None, None, (jsonify({'error': 'No se encontró instancia de agente activa'}), 404)
    
    instance = None
    for candidate in instances:
        if verify_access_key(agent_access_key, candidate.client_access_key_hash):
            instance = candidate
            break
    
    if not instance:
        return None, None, (jsonify({'error': 'Credenciales de acceso inválidas'}), 401)
    
    if not instance.azure_speech_endpoint or not instance.azure_speech_key_secret_id or not instance.azure_speech_region:
        return None, None, (jsonify({'error': 'Credenciales de Azure Speech no configuradas para esta empresa'}), 400)
    
    from txdxai.common.keyvault_client import get_secret
    try:
        speech_key = get_secret(instance.azure_speech_key_secret_id)
        if not speech_key:
            return None, None, (jsonify({'error': 'No se pudo recuperar la clave de Azure Speech'}), 500)
    except Exception as e:
        logger.error(f"Error retrieving Speech key from Key Vault: {str(e)}")
        return None, None, (jsonify({'error': 'Error al recuperar credenciales de Azure Speech'}), 500)
    
    instance.last_used_at = datetime.utcnow()
    db.session.commit()
    
    return instance, speech_key, None


@voice_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Speech-to-Text endpoint
    
    Multipart form data:
        - audio: Audio file (WAV, MP3, OGG, M4A, FLAC, WEBM)
        - companyId: Company ID
        - agentAccessKey: Agent access key
    
    Returns:
        JSON with transcribed text
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo de audio'}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    if not allowed_file(audio_file.filename):
        return jsonify({'error': f'Formato de audio no permitido. Formatos soportados: {", ".join(ALLOWED_AUDIO_EXTENSIONS)}'}), 400
    
    company_id = request.form.get('companyId')
    agent_access_key = request.form.get('agentAccessKey')
    
    if not company_id or not agent_access_key:
        return jsonify({'error': 'companyId y agentAccessKey son requeridos'}), 400
    
    try:
        company_id = int(company_id)
    except ValueError:
        return jsonify({'error': 'companyId debe ser un número'}), 400
    
    instance, speech_key, error = get_speech_credentials(company_id, agent_access_key)
    if error:
        return error
    
    temp_file = None
    try:
        filename = secure_filename(audio_file.filename)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        audio_file.save(temp_file.name)
        temp_file.close()
        
        result = SpeechService.transcribe_audio(
            audio_file_path=temp_file.name,
            speech_key=speech_key,
            region=instance.azure_speech_region
        )
        
        if result['status'] == 'success':
            return jsonify({
                'text': result['text'],
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': result.get('error', 'Error al transcribir el audio'),
                'status': result['status']
            }), 400
            
    except Exception as e:
        logger.error(f"Error in transcribe endpoint: {str(e)}")
        return jsonify({'error': 'Error interno al procesar el audio'}), 500
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@voice_bp.route('/speak', methods=['POST'])
def text_to_speech():
    """
    Text-to-Speech endpoint
    
    JSON body:
        - text: Text to convert to speech
        - companyId: Company ID
        - agentAccessKey: Agent access key
    
    Returns:
        Audio file (MP3)
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body vacío'}), 400
    
    text = data.get('text')
    company_id = data.get('companyId')
    agent_access_key = data.get('agentAccessKey')
    
    if not text or not company_id or not agent_access_key:
        return jsonify({'error': 'text, companyId y agentAccessKey son requeridos'}), 400
    
    try:
        company_id = int(company_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'companyId debe ser un número'}), 400
    
    instance, speech_key, error = get_speech_credentials(company_id, agent_access_key)
    if error:
        return error
    
    try:
        voice_name = instance.azure_speech_voice_name or 'es-ES-ElviraNeural'
        
        result = SpeechService.synthesize_speech(
            text=text,
            speech_key=speech_key,
            region=instance.azure_speech_region,
            voice_name=voice_name
        )
        
        if result['status'] == 'success' and result['audio_data']:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.write(result['audio_data'])
            temp_file_path = temp_file.name
            temp_file.close()
            
            try:
                response = send_file(
                    temp_file_path,
                    mimetype='audio/mpeg',
                    as_attachment=True,
                    download_name='speech.mp3'
                )
                response.call_on_close(lambda: os.unlink(temp_file_path) if os.path.exists(temp_file_path) else None)
                return response
            except Exception as e:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise e
        else:
            return jsonify({
                'error': result.get('error', 'Error al sintetizar el audio'),
                'status': result['status']
            }), 400
            
    except Exception as e:
        logger.error(f"Error in speak endpoint: {str(e)}")
        return jsonify({'error': 'Error interno al generar el audio'}), 500
