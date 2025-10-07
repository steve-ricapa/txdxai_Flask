from flask import jsonify

class TxDxAIError(Exception):
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


class UnauthorizedError(TxDxAIError):
    status_code = 401


class ForbiddenError(TxDxAIError):
    status_code = 403


class NotFoundError(TxDxAIError):
    status_code = 404


class ConflictError(TxDxAIError):
    status_code = 409


class ValidationError(TxDxAIError):
    status_code = 422


def handle_error(error):
    if isinstance(error, TxDxAIError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    response = jsonify({'error': str(error)})
    response.status_code = 500
    return response
