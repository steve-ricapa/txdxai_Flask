from datetime import datetime
import uuid
from txdxai.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='company', lazy=True, cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', backref='company', lazy=True, cascade='all, delete-orphan')
    integrations = db.relationship('Integration', backref='company', lazy=True, cascade='all, delete-orphan')
    agent_sessions = db.relationship('AgentSession', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='USER')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tickets_created = db.relationship('Ticket', foreign_keys='Ticket.created_by_user_id', backref='creator', lazy=True)
    audit_logs = db.relationship('AuditLog', foreign_keys='AuditLog.actor_user_id', backref='actor', lazy=True)
    agent_sessions = db.relationship('AgentSession', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_company=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_company and self.company:
            data['company'] = self.company.to_dict()
        return data


class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    subject = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='PENDING')
    executed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, include_creator=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'created_by_user_id': self.created_by_user_id,
            'subject': self.subject,
            'description': self.description,
            'status': self.status,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_creator and self.creator:
            data['creator'] = self.creator.to_dict()
        return data


class Integration(db.Model):
    __tablename__ = 'integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    provider = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    capabilities = db.Column(db.JSON, nullable=True)
    config = db.Column(db.JSON, nullable=True)
    keyvault_secret_id = db.Column(db.String(500), nullable=False)
    extra_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'provider': self.provider,
            'type': self.type,
            'capabilities': self.capabilities,
            'config': self.config,
            'keyvault_secret_id': self.keyvault_secret_id,
            'extra_json': self.extra_json,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentSession(db.Model):
    __tablename__ = 'agent_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    external_thread_id = db.Column(db.String(500), nullable=True)
    purpose = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    memory_refs = db.relationship('AgentMemoryRef', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'user_id': self.user_id,
            'external_thread_id': self.external_thread_id,
            'purpose': self.purpose,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None
        }


class AgentMemoryRef(db.Model):
    __tablename__ = 'agent_memory_refs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('agent_sessions.id', ondelete='CASCADE'), nullable=False)
    vector_store_id = db.Column(db.String(500), nullable=False)
    scope = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'vector_store_id': self.vector_store_id,
            'scope': self.scope,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(255), nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'actor_user_id': self.actor_user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'payload': self.payload,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class System(db.Model):
    __tablename__ = 'systems'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='online')
    health_score = db.Column(db.Float, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    meta_info = db.Column(db.JSON, nullable=True)
    last_check = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'integration_id': self.integration_id,
            'name': self.name,
            'type': self.type,
            'status': self.status,
            'health_score': self.health_score,
            'meta_info': self.meta_info,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=True)
    external_id = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    meta_info = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'integration_id': self.integration_id,
            'external_id': self.external_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'source': self.source,
            'status': self.status,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by_user_id': self.resolved_by_user_id,
            'meta_info': self.meta_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Vulnerability(db.Model):
    __tablename__ = 'vulnerabilities'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=True)
    cve_id = db.Column(db.String(50), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False)
    cvss_score = db.Column(db.Float, nullable=True)
    affected_systems = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='open')
    patch_status = db.Column(db.String(50), nullable=True)
    patched_at = db.Column(db.DateTime, nullable=True)
    meta_info = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'integration_id': self.integration_id,
            'cve_id': self.cve_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'cvss_score': self.cvss_score,
            'affected_systems': self.affected_systems,
            'status': self.status,
            'patch_status': self.patch_status,
            'patched_at': self.patched_at.isoformat() if self.patched_at else None,
            'meta_info': self.meta_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentInstance(db.Model):
    __tablename__ = 'agent_instances'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    agent_type = db.Column(db.String(50), nullable=False, default='SOPHIA')
    
    azure_project_id = db.Column(db.String(255), nullable=True)
    azure_agent_id = db.Column(db.String(255), nullable=True)
    azure_vector_store_id = db.Column(db.String(255), nullable=True)
    
    azure_openai_endpoint = db.Column(db.String(500), nullable=True)
    azure_openai_key_secret_id = db.Column(db.String(255), nullable=True)
    azure_openai_deployment = db.Column(db.String(100), nullable=True)
    
    azure_search_endpoint = db.Column(db.String(500), nullable=True)
    azure_search_key_secret_id = db.Column(db.String(255), nullable=True)
    
    azure_speech_endpoint = db.Column(db.String(500), nullable=True)
    azure_speech_key_secret_id = db.Column(db.String(255), nullable=True)
    azure_speech_region = db.Column(db.String(100), nullable=True)
    azure_speech_voice_name = db.Column(db.String(100), nullable=True, default='es-ES-ElviraNeural')
    
    keyvault_secret_id = db.Column(db.String(255), nullable=True)
    client_access_key_hash = db.Column(db.String(255), nullable=False)
    client_access_key_encrypted = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    settings = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self, show_key_hint=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'agent_type': self.agent_type,
            'azure_project_id': self.azure_project_id,
            'azure_agent_id': self.azure_agent_id,
            'azure_vector_store_id': self.azure_vector_store_id,
            'azure_openai_endpoint': self.azure_openai_endpoint,
            'azure_openai_deployment': self.azure_openai_deployment,
            'azure_search_endpoint': self.azure_search_endpoint,
            'azure_speech_endpoint': self.azure_speech_endpoint,
            'azure_speech_region': self.azure_speech_region,
            'azure_speech_voice_name': self.azure_speech_voice_name,
            'status': self.status,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }
        return data
