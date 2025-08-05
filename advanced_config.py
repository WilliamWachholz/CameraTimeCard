#!/usr/bin/env python3
"""
Configuração avançada para o sistema de reconhecimento facial
"""

import os
from datetime import time

class Config:
    """Configurações do sistema"""
    
    # =================
    # BACKEND
    # =================
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000/api')
    BACKEND_TIMEOUT = int(os.getenv('BACKEND_TIMEOUT', '10'))
    
    # =================
    # CÂMERA
    # =================
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))
    FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '640'))
    FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '480'))
    CAMERA_FPS = int(os.getenv('CAMERA_FPS', '30'))
    
    # =================
    # RECONHECIMENTO FACIAL
    # =================
    # Tolerância para reconhecimento (0.0 a 1.0, menor = mais rigoroso)
    FACE_RECOGNITION_TOLERANCE = float(os.getenv('FACE_TOLERANCE', '0.6'))
    
    # Modelo de detecção: 'hog' (rápido) ou 'cnn' (preciso, requer GPU)
    FACE_DETECTION_MODEL = os.getenv('FACE_DETECTION_MODEL', 'hog')
    
    # Número de vezes para re-amostrar a face durante encoding
    FACE_ENCODING_SAMPLES = int(os.getenv('FACE_ENCODING_SAMPLES', '1'))
    
    # Processar apenas cada N frames (otimização)
    PROCESS_EVERY_N_FRAMES = int(os.getenv('PROCESS_FRAMES', '2'))
    
    # =================
    # CONTROLE DE PONTO
    # =================
    # Tempo mínimo entre registros do mesmo funcionário (segundos)
    RECOGNITION_COOLDOWN = int(os.getenv('RECOGNITION_COOLDOWN', '10'))
    
    # Horário de funcionamento (opcional - None para desabilitar)
    WORK_START_TIME = time(7, 0)   # 07:00
    WORK_END_TIME = time(19, 0)    # 19:00
    
    # Permitir registro fora do horário de trabalho
    ALLOW_AFTER_HOURS = True
    
    # =================
    # ARQUIVOS E PASTAS
    # =================
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    LOGS_DIR = os.getenv('LOGS_DIR', 'logs')
    PHOTOS_DIR = os.getenv('PHOTOS_DIR', 'employee_photos')
    
    FACE_ENCODINGS_FILE = os.path.join(DATA_DIR, 'face_encodings.pkl')
    SYSTEM_LOG_FILE = os.path.join(LOGS_DIR, 'system.log')
    DATABASE_FILE = os.path.join(DATA_DIR, 'timecard.db')
    
    # =================
    # LOGGING
    # =================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # =================
    # INTERFACE
    # =================
    # Cores para interface OpenCV (BGR)
    COLOR_RECOGNIZED = (0, 255, 0)      # Verde para reconhecido
    COLOR_UNKNOWN = (0, 0, 255)         # Vermelho para desconhecido
    COLOR_COOLDOWN = (0, 255, 255)      # Amarelo para cooldown
    
    # Fonte e tamanho do texto
    FONT = 0  # cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.6
    FONT_THICKNESS = 1
    
    # Mostrar informações na tela
    SHOW_FPS = True
    SHOW_EMPLOYEE_COUNT = True
    SHOW_INSTRUCTIONS = True
    
    # =================
    # SEGURANÇA
    # =================
    # Número máximo de tentativas de reconhecimento falhadas
    MAX_FAILED_ATTEMPTS = int(os.getenv('MAX_FAILED_ATTEMPTS', '10'))
    
    # Tempo de bloqueio após muitas tentativas falhadas (segundos)
    LOCKOUT_TIME = int(os.getenv('LOCKOUT_TIME', '300'))  # 5 minutos
    
    # Salvar fotos de tentativas não reconhecidas
    SAVE_UNKNOWN_FACES = os.getenv('SAVE_UNKNOWN_FACES', 'false').lower() == 'true'
    UNKNOWN_FACES_DIR = os.path.join(PHOTOS_DIR, 'unknown')
    
    # =================
    # BACKUP
    # =================
    # Backup automático dos encodings
    AUTO_BACKUP = True
    BACKUP_INTERVAL_HOURS = 24
    MAX_BACKUPS = 7
    BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
    
    # =================
    # NOTIFICAÇÕES
    # =================
    # Webhook para notificações (opcional)
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', None)
    
    # Notificar em eventos específicos
    NOTIFY_ON_FIRST_ENTRY = True
    NOTIFY_ON_LATE_ARRIVAL = True
    NOTIFY_ON_EARLY_DEPARTURE = True
    NOTIFY_ON_UNKNOWN_FACE = False
    
    # Horários para considerar atraso/saída antecipada
    LATE_ARRIVAL_TIME = time(9, 0)      # Depois das 09:00
    EARLY_DEPARTURE_TIME = time(17, 0)  # Antes das 17:00
    
    # =================
    # PERFORMANCE
    # =================
    # Redimensionar frame para processamento (otimização)
    PROCESSING_SCALE = 0.25  # 25% do tamanho original
    
    # Usar threading para processamento
    USE_THREADING = True
    
    # Cache de encodings em memória
    CACHE_ENCODINGS = True
    MAX_CACHE_SIZE = 1000
    
    # =================
    # DESENVOLVIMENTO
    # =================
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    SAVE_DEBUG_FRAMES = DEBUG_MODE
    DEBUG_FRAMES_DIR = os.path.join(LOGS_DIR, 'debug_frames')
    
    @classmethod
    def create_directories(cls):
        """Cria diretórios necessários"""
        dirs = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.PHOTOS_DIR,
            cls.BACKUP_DIR,
            cls.UNKNOWN_FACES_DIR
        ]
        
        if cls.SAVE_DEBUG_FRAMES:
            dirs.append(cls.DEBUG_FRAMES_DIR)
        
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Valida configurações"""
        errors = []
        
        # Validar tolerância
        if not (0.0 <= cls.FACE_RECOGNITION_TOLERANCE <= 1.0):
            errors.append("FACE_RECOGNITION_TOLERANCE deve estar entre 0.0 e 1.0")
        
        # Validar modelo de detecção
        if cls.FACE_DETECTION_MODEL not in ['hog', 'cnn']:
            errors.append("FACE_DETECTION_MODEL deve ser 'hog' ou 'cnn'")
        
        # Validar horários
        if cls.WORK_START_TIME and cls.WORK_END_TIME:
            if cls.WORK_START_TIME >= cls.WORK_END_TIME:
                errors.append("WORK_START_TIME deve ser anterior a WORK_END_TIME")
        
        # Validar cooldown
        if cls.RECOGNITION_COOLDOWN < 0:
            errors.append("RECOGNITION_COOLDOWN deve ser >= 0")
        
        if errors:
            raise ValueError("Erros de configuração:\n" + "\n".join(f"- {e}" for e in errors))
    
    @classmethod
    def print_config(cls):
        """Imprime configuração atual"""
        print("=== CONFIGURAÇÃO DO SISTEMA ===")
        print(f"Backend URL: {cls.BACKEND_URL}")
        print(f"Câmera: Índice {cls.CAMERA_INDEX}, {cls.FRAME_WIDTH}x{cls.FRAME_HEIGHT}")
        print(f"Tolerância de reconhecimento: {cls.FACE_RECOGNITION_TOLERANCE}")
        print(f"Modelo de detecção: {cls.FACE_DETECTION_MODEL}")
        print(f"Cooldown: {cls.RECOGNITION_COOLDOWN}s")
        
        if cls.WORK_START_TIME and cls.WORK_END_TIME:
            print(f"Horário de trabalho: {cls.WORK_START_TIME} às {cls.WORK_END_TIME}")
        
        print(f"Diretório de dados: {cls.DATA_DIR}")
        print(f"Debug mode: {'Ativado' if cls.DEBUG_MODE else 'Desativado'}")
        print("=" * 40)

# Arquivo de configuração personalizada (opcional)
CUSTOM_CONFIG_FILE = 'custom_config.py'

def load_custom_config():
    """Carrega configurações personalizadas se existirem"""
    if os.path.exists(CUSTOM_CONFIG_FILE):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("custom_config", CUSTOM_CONFIG_FILE)
            custom_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(custom_config)
            
            # Sobrescrever configurações
            for attr in dir(custom_config):
                if not attr.startswith('_'):
                    setattr(Config, attr, getattr(custom_config, attr))
            
            print(f"✅ Configurações personalizadas carregadas de {CUSTOM_CONFIG_FILE}")
        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações personalizadas: {e}")

def create_sample_custom_config():
    """Cria arquivo de exemplo para configurações personalizadas"""
    sample_config = '''# Configurações personalizadas do sistema de ponto
# Copie este arquivo para custom_config.py e modifique conforme necessário

# Exemplo: Configuração para empresa específica
BACKEND_URL = "https://ponto.minhaempresa.com/api"
RECOGNITION_COOLDOWN = 5  # 5 segundos ao invés de 10

# Horário de trabalho personalizado
from datetime import time
WORK_START_TIME = time(8, 0)   # 08:00
WORK_END_TIME = time(18, 0)    # 18:00

# Configurações de segurança mais rigorosas
FACE_RECOGNITION_TOLERANCE = 0.5  # Mais rigoroso
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TIME = 600  # 10 minutos

# Ativar salvamento de faces desconhecidas
SAVE_UNKNOWN_FACES = True

# Notificações via webhook
WEBHOOK_URL = "https://hooks.slack.com/services/..."
NOTIFY_ON_UNKNOWN_FACE = True

# Configurações de performance para hardware mais potente
FACE_DETECTION_MODEL = 'cnn'  # Mais preciso, requer GPU
PROCESSING_SCALE = 0.5  # Processar em resolução maior
'''
    
    with open('sample_custom_config.py', 'w') as f:
        f.write(sample_config)
    
    print(f"📄 Arquivo de exemplo criado: sample_custom_config.py")
    print("   Copie para custom_config.py e modifique conforme necessário")

if __name__ == "__main__":
    # Inicializar configuração
    load_custom_config()
    Config.create_directories()
    Config.validate_config()
    Config.print_config()
    
    # Criar arquivo de exemplo se não existir
    if not os.path.exists('sample_custom_config.py'):
        create_sample_custom_config()