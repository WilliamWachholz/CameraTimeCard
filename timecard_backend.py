from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configuração do banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "timecard.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo do banco de dados
class Employee(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

class TimeCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employee.id'), nullable=False)
    employee_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    recognition_method = db.Column(db.String(20), default='facial')
    entry_type = db.Column(db.String(10))  # 'entrada' ou 'saida'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('timecards', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'timestamp': self.timestamp.isoformat(),
            'recognition_method': self.recognition_method,
            'entry_type': self.entry_type,
            'created_at': self.created_at.isoformat()
        }

# Criar tabelas
with app.app_context():
    db.create_all()

def determine_entry_type(employee_id):
    """Determina se é entrada ou saída baseado no último registro"""
    last_record = TimeCard.query.filter_by(employee_id=employee_id)\
                                .order_by(TimeCard.timestamp.desc()).first()
    
    if not last_record or last_record.entry_type == 'saida':
        return 'entrada'
    else:
        return 'saida'

@app.route('/api/timecard', methods=['POST'])
def register_timecard():
    """Registra um ponto do funcionário"""
    try:
        data = request.get_json()
        
        # Validação dos dados
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        required_fields = ['employee_id', 'employee_name', 'timestamp']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        employee_id = data['employee_id']
        employee_name = data['employee_name']
        timestamp_str = data['timestamp']
        recognition_method = data.get('recognition_method', 'facial')
        
        # Converter timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Formato de timestamp inválido'}), 400
        
        # Verificar se funcionário existe, se não criar
        employee = Employee.query.get(employee_id)
        if not employee:
            employee = Employee(id=employee_id, name=employee_name)
            db.session.add(employee)
            logging.info(f"Novo funcionário criado: {employee_name} (ID: {employee_id})")
        
        # Determinar tipo de entrada
        entry_type = determine_entry_type(employee_id)
        
        # Criar registro de ponto
        timecard = TimeCard(
            employee_id=employee_id,
            employee_name=employee_name,
            timestamp=timestamp,
            recognition_method=recognition_method,
            entry_type=entry_type
        )
        
        db.session.add(timecard)
        db.session.commit()
        
        logging.info(f"Ponto registrado: {employee_name} - {entry_type} - {timestamp}")
        
        return jsonify({
            'success': True,
            'message': f'Ponto registrado com sucesso - {entry_type.upper()}',
            'data': timecard.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao registrar ponto: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/employee/<employee_id>/timecards', methods=['GET'])
def get_employee_timecards(employee_id):
    """Busca registros de ponto de um funcionário"""
    try:
        # Parâmetros de query
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', type=int, default=50)
        
        query = TimeCard.query.filter_by(employee_id=employee_id)
        
        # Filtrar por data se fornecido
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(TimeCard.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(TimeCard.timestamp <= end_dt)
        
        timecards = query.order_by(TimeCard.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'employee_id': employee_id,
            'timecards': [tc.to_dict() for tc in timecards]
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao buscar registros: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/timecards', methods=['GET'])
def get_all_timecards():
    """Busca todos os registros de ponto"""
    try:
        # Parâmetros de query
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', type=int, default=100)
        
        query = TimeCard.query
        
        # Filtrar por data se fornecido
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(TimeCard.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(TimeCard.timestamp <= end_dt)
        
        timecards = query.order_by(TimeCard.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'total': len(timecards),
            'timecards': [tc.to_dict() for tc in timecards]
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao buscar registros: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Lista todos os funcionários"""
    try:
        employees = Employee.query.all()
        return jsonify({
            'employees': [emp.to_dict() for emp in employees]
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao buscar funcionários: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/employee/<employee_id>/status', methods=['GET'])
def get_employee_status(employee_id):
    """Verifica status atual do funcionário (dentro/fora)"""
    try:
        last_record = TimeCard.query.filter_by(employee_id=employee_id)\
                                   .order_by(TimeCard.timestamp.desc()).first()
        
        if not last_record:
            status = 'nunca_registrou'
            last_entry = None
        else:
            status = 'dentro' if last_record.entry_type == 'entrada' else 'fora'
            last_entry = last_record.to_dict()
        
        return jsonify({
            'employee_id': employee_id,
            'status': status,
            'last_entry': last_entry
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao verificar status: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de saúde da API"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Sistema de ponto funcionando'
    }), 200

if __name__ == '__main__':
    print("=== Backend do Sistema de Ponto ===")
    print("API rodando em: http://localhost:5000")
    print("Endpoints disponíveis:")
    print("- POST /api/timecard - Registrar ponto")
    print("- GET /api/timecards - Listar todos os pontos")
    print("- GET /api/employees - Listar funcionários")
    print("- GET /api/employee/<id>/timecards - Pontos de um funcionário")
    print("- GET /api/employee/<id>/status - Status atual do funcionário")
    print("- GET /api/health - Status da API")
    
    app.run(debug=True, host='0.0.0.0', port=5000)