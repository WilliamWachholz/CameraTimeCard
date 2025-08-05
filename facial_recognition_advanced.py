#!/usr/bin/env python3
"""
Sistema avançado de reconhecimento facial para controle de ponto
Versão com configurações personalizáveis e recursos adicionais
"""

import cv2
import face_recognition
import numpy as np
import requests
import json
import os
import pickle
import logging
import threading
import time
from datetime import datetime, timedelta
from collections import deque
import shutil

# Importar configurações
try:
    from advanced_config import Config, load_custom_config
    load_custom_config()
    Config.create_directories()
    Config.validate_config()
except ImportError:
    print("⚠️ Arquivo de configuração não encontrado. Usando configurações padrão.")
    # Configurações básicas como fallback
    class Config:
        BACKEND_URL = "http://localhost:5000/api"
        CAMERA_INDEX = 0
        FRAME_WIDTH = 640
        FRAME_HEIGHT = 480
        FACE_RECOGNITION_TOLERANCE = 0.6
        RECOGNITION_COOLDOWN = 10
        DATA_DIR = "data"
        LOGS_DIR = "logs"
        FACE_ENCODINGS_FILE = "data/face_encodings.pkl"
        SYSTEM_LOG_FILE = "logs/system.log"
        COLOR_RECOGNIZED = (0, 255, 0)
        COLOR_UNKNOWN = (0, 0, 255)
        SHOW_FPS = True
        DEBUG_MODE = False
        @classmethod
        def create_directories(cls):
            os.makedirs(cls.DATA_DIR, exist_ok=True)
            os.makedirs(cls.LOGS_DIR, exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=getattr(logging, getattr(Config, 'LOG_LEVEL', 'INFO')),
    format=getattr(Config, 'LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s'),
    handlers=[
        logging.FileHandler(Config.SYSTEM_LOG_FILE),
        logging.StreamHandler()
    ]
)

class AdvancedFacialRecognitionTimeCard:
    def __init__(self):
        self.config = Config
        self.logger = logging.getLogger(__name__)
        
        # Dados de reconhecimento
        self.known_faces = []
        self.known_names = []
        self.known_ids = []
        
        # Controle de estado
        self.last_recognition = {}
        self.failed_attempts = {}
        self.locked_until = {}
        
        # Performance
        self.fps_counter = deque(maxlen=30)
        self.processing_thread = None
        self.stop_processing = threading.Event()
        
        # Cache de encodings
        self.encoding_cache = {} if hasattr(Config, 'CACHE_ENCODINGS') and Config.CACHE_ENCODINGS else None
        
        # Carregar dados
        self.load_known_faces()
        
        # Inicializar câmera
        self.setup_camera()
        
        self.logger.info("Sistema avançado de reconhecimento facial inicializado")
    
    def setup_camera(self):
        """Configura a câmera com parâmetros otimizados"""
        self.camera = cv2.VideoCapture(self.config.CAMERA_INDEX)
        
        if not self.camera.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.config.CAMERA_INDEX}")
        
        # Configurar propriedades da câmera
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        
        if hasattr(self.config, 'CAMERA_FPS'):
            self.camera.set(cv2.CAP_PROP_FPS, self.config.CAMERA_FPS)
        
        # Verificar se configurações foram aplicadas
        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.logger.info(f"Câmera configurada: {actual_width}x{actual_height}")
    
    def load_known_faces(self):
        """Carrega as codificações faciais com backup automático"""
        if os.path.exists(self.config.FACE_ENCODINGS_FILE):
            try:
                with open(self.config.FACE_ENCODINGS_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.known_faces = data.get('encodings', [])
                    self.known_names = data.get('names', [])
                    self.known_ids = data.get('ids', [])
                
                self.logger.info(f"Carregados {len(self.known_faces)} funcionários")
                
                # Backup automático
                if hasattr(self.config, 'AUTO_BACKUP') and self.config.AUTO_BACKUP:
                    self.create_backup()
                    
            except Exception as e:
                self.logger.error(f"Erro ao carregar encodings: {e}")
                self.known_faces = []
                self.known_names = []
                self.known_ids = []
        else:
            self.logger.info("Nenhum arquivo de encodings encontrado. Iniciando com base vazia.")
    
    def save_known_faces(self):
        """Salva as codificações faciais"""
        try:
            data = {
                'encodings': self.known_faces,
                'names': self.known_names,
                'ids': self.known_ids,
                'saved_at': datetime.now().isoformat(),
                'version': '2.0'
            }
            
            # Salvar com backup
            temp_file = self.config.FACE_ENCODINGS_FILE + '.tmp'
            with open(temp_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Mover arquivo temporário para o definitivo
            shutil.move(temp_file, self.config.FACE_ENCODINGS_FILE)
            
            self.logger.info("Encodings salvos com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar encodings: {e}")
    
    def create_backup(self):
        """Cria backup dos encodings"""
        if not hasattr(self.config, 'BACKUP_DIR'):
            return
        
        try:
            backup_filename = f"face_encodings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            backup_path = os.path.join(self.config.BACKUP_DIR, backup_filename)
            
            if os.path.exists(self.config.FACE_ENCODINGS_FILE):
                shutil.copy2(self.config.FACE_ENCODINGS_FILE, backup_path)
                self.logger.debug(f"Backup criado: {backup_filename}")
                
                # Limpar backups antigos
                self.cleanup_old_backups()
                
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
    
    def cleanup_old_backups(self):
        """Remove backups antigos"""
        if not hasattr(self.config, 'MAX_BACKUPS'):
            return
        
        try:
            backup_files = []
            for file in os.listdir(self.config.BACKUP_DIR):
                if file.startswith('face_encodings_backup_') and file.endswith('.pkl'):
                    file_path = os.path.join(self.config.BACKUP_DIR, file)
                    backup_files.append((file_path, os.path.getctime(file_path)))
            
            # Ordenar por data de criação
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remover backups antigos
            for file_path, _ in backup_files[self.config.MAX_BACKUPS:]:
                os.remove(file_path)
                self.logger.debug(f"Backup antigo removido: {os.path.basename(file_path)}")
                
        except Exception as e:
            self.logger.error(f"Erro ao limpar backups: {e}")
    
    def is_work_hours(self):
        """Verifica se está dentro do horário de trabalho"""
        if not hasattr(self.config, 'WORK_START_TIME') or not self.config.WORK_START_TIME:
            return True
        
        if not hasattr(self.config, 'WORK_END_TIME') or not self.config.WORK_END_TIME:
            return True
        
        current_time = datetime.now().time()
        return self.config.WORK_START_TIME <= current_time <= self.config.WORK_END_TIME
    
    def is_employee_locked(self, employee_id):
        """Verifica se funcionário está bloqueado por tentativas falhadas"""
        if employee_id not in self.locked_until:
            return False
        
        if datetime.now() > self.locked_until[employee_id]:
            del self.locked_until[employee_id]
            if employee_id in self.failed_attempts:
                del self.failed_attempts[employee_id]
            return False
        
        return True
    
    def can_register_again(self, employee_id):
        """Verifica se pode registrar novamente (considerando cooldown e bloqueios)"""
        # Verificar bloqueio
        if self.is_employee_locked(employee_id):
            return False
        
        # Verificar cooldown
        if employee_id in self.last_recognition:
            time_diff = (datetime.now() - self.last_recognition[employee_id]).total_seconds()
            return time_diff >= self.config.RECOGNITION_COOLDOWN
        
        return True
    
    def register_failed_attempt(self, frame=None):
        """Registra tentativa de reconhecimento falhada"""
        if not hasattr(self.config, 'MAX_FAILED_ATTEMPTS'):
            return
        
        current_time = datetime.now()
        
        # Incrementar contador (usando 'unknown' como chave geral)
        if 'unknown' not in self.failed_attempts:
            self.failed_attempts['unknown'] = []
        
        self.failed_attempts['unknown'].append(current_time)
        
        # Limpar tentativas antigas (última hora)
        one_hour_ago = current_time - timedelta(hours=1)
        self.failed_attempts['unknown'] = [
            attempt for attempt in self.failed_attempts['unknown'] 
            if attempt > one_hour_ago
        ]
        
        # Verificar se deve bloquear
        if len(self.failed_attempts['unknown']) >= self.config.MAX_FAILED_ATTEMPTS:
            if hasattr(self.config, 'LOCKOUT_TIME'):
                lockout_until = current_time + timedelta(seconds=self.config.LOCKOUT_TIME)
                self.locked_until['unknown'] = lockout_until
                self.logger.warning(f"Sistema bloqueado até {lockout_until} por muitas tentativas falhadas")
        
        # Salvar foto da face desconhecida se configurado
        if (hasattr(self.config, 'SAVE_UNKNOWN_FACES') and 
            self.config.SAVE_UNKNOWN_FACES and frame is not None):
            self.save_unknown_face(frame)
    
    def save_unknown_face(self, frame):
        """Salva foto de face não reconhecida"""
        try:
            if not hasattr(self.config, 'UNKNOWN_FACES_DIR'):
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"unknown_face_{timestamp}.jpg"
            filepath = os.path.join(self.config.UNKNOWN_FACES_DIR, filename)
            
            cv2.imwrite(filepath, frame)
            self.logger.debug(f"Face desconhecida salva: {filename}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar face desconhecida: {e}")
    
    def send_timecard_to_backend(self, employee_id, employee_name, timestamp):
        """Envia registro de ponto para o backend com retry"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                data = {
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "timestamp": timestamp,
                    "recognition_method": "facial"
                }
                
                response = requests.post(
                    f"{self.config.BACKEND_URL}/timecard",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=getattr(self.config, 'BACKEND_TIMEOUT', 10)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"Ponto registrado: {employee_name} - {result.get('message', 'OK')}")
                    return True, result
                else:
                    self.logger.error(f"Erro no backend: {response.status_code}")
                    
            except requests.RequestException as e:
                self.logger.error(f"Tentativa {attempt + 1} falhou: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Aguardar antes da próxima tentativa
        
        return False, None
    
    def send_notification(self, event_type, data):
        """Envia notificação via webhook se configurado"""
        if not hasattr(self.config, 'WEBHOOK_URL') or not self.config.WEBHOOK_URL:
            return
        
        try:
            notification_data = {
                "event": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            response = requests.post(
                self.config.WEBHOOK_URL,
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.debug(f"Notificação enviada: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação: {e}")
    
    def process_recognition(self, face_encodings, face_locations):
        """Processa reconhecimento facial com otimizações"""
        face_names = []
        current_time = datetime.now()
        
        for face_encoding in face_encodings:
            name = "Desconhecido"
            employee_id = None
            color = self.config.COLOR_UNKNOWN
            
            if len(self.known_faces) > 0:
                # Usar cache se disponível
                if self.encoding_cache and len(self.encoding_cache) < getattr(self.config, 'MAX_CACHE_SIZE', 1000):
                    encoding_key = hash(face_encoding.tobytes())
                    if encoding_key in self.encoding_cache:
                        name, employee_id = self.encoding_cache[encoding_key]
                        color = self.config.COLOR_RECOGNIZED
                        face_names.append((name, color))
                        continue
                
                # Comparar com faces conhecidas
                matches = face_recognition.compare_faces(
                    self.known_faces, 
                    face_encoding, 
                    tolerance=self.config.FACE_RECOGNITION_TOLERANCE
                )
                
                face_distances = face_recognition.face_distance(self.known_faces, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    
                    if (matches[best_match_index] and 
                        face_distances[best_match_index] < self.config.FACE_RECOGNITION_TOLERANCE):
                        
                        name = self.known_names[best_match_index]
                        employee_id = self.known_ids[best_match_index]
                        color = self.config.COLOR_RECOGNIZED
                        
                        # Adicionar ao cache
                        if self.encoding_cache:
                            encoding_key = hash(face_encoding.tobytes())
                            self.encoding_cache[encoding_key] = (name, employee_id)
                        
                        # Verificar se pode registrar ponto
                        if self.can_register_again(employee_id):
                            # Verificar horário de trabalho
                            if not self.is_work_hours() and not getattr(self.config, 'ALLOW_AFTER_HOURS', True):
                                self.logger.warning(f"Tentativa de registro fora do horário: {name}")
                                name += " (Fora do horário)"
                                color = (0, 255, 255)  # Amarelo
                            else:
                                # Registrar ponto
                                timestamp = current_time.isoformat()
                                success, result = self.send_timecard_to_backend(employee_id, name, timestamp)
                                
                                if success:
                                    self.last_recognition[employee_id] = current_time
                                    
                                    # Enviar notificações se configurado
                                    if hasattr(self.config, 'NOTIFY_ON_FIRST_ENTRY') and self.config.NOTIFY_ON_FIRST_ENTRY:
                                        # Verificar se é primeira entrada do dia
                                        if result and result.get('data', {}).get('entry_type') == 'entrada':
                                            self.send_notification('first_entry', {
                                                'employee_id': employee_id,
                                                'employee_name': name,
                                                'timestamp': timestamp
                                            })
                        else:
                            # Em cooldown
                            remaining_time = self.config.RECOGNITION_COOLDOWN - (
                                current_time - self.last_recognition.get(employee_id, current_time)
                            ).total_seconds()
                            name += f" (Aguarde {int(remaining_time)}s)"
                            color = getattr(self.config, 'COLOR_COOLDOWN', (0, 255, 255))
            
            if name == "Desconhecido":
                self.register_failed_attempt()
            
            face_names.append((name, color))
        
        return face_names
    
    def draw_interface(self, frame, face_locations, face_names):
        """Desenha interface com informações na tela"""
        # Desenhar retângulos e nomes dos rostos
        for (top, right, bottom, left), (name, color) in zip(face_locations, face_names):
            # Escalar coordenadas de volta ao tamanho original
            if hasattr(self.config, 'PROCESSING_SCALE'):
                scale = 1.0 / self.config.PROCESSING_SCALE
                top = int(top * scale)
                right = int(right * scale)
                bottom = int(bottom * scale)
                left = int(left * scale)
            
            # Desenhar retângulo
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Desenhar label com fundo
            label_height = 35
            cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), color, cv2.FILLED)
            
            # Texto do nome
            font = getattr(self.config, 'FONT', cv2.FONT_HERSHEY_DUPLEX)
            font_scale = getattr(self.config, 'FONT_SCALE', 0.6)
            font_thickness = getattr(self.config, 'FONT_THICKNESS', 1)
            
            cv2.putText(frame, name, (left + 6, bottom - 6), 
                       font, font_scale, (255, 255, 255), font_thickness)
        
        # Informações do sistema
        y_offset = 30
        
        if getattr(self.config, 'SHOW_EMPLOYEE_COUNT', True):
            cv2.putText(frame, f"Funcionarios: {len(self.known_faces)}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += 30
        
        if getattr(self.config, 'SHOW_FPS', True) and len(self.fps_counter) > 0:
            fps = len(self.fps_counter) / (self.fps_counter[-1] - self.fps_counter[0] + 0.001)
            cv2.putText(frame, f"FPS: {fps:.1f}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += 30
        
        # Status do sistema
        if not self.is_work_hours() and hasattr(self.config, 'WORK_START_TIME'):
            cv2.putText(frame, "FORA DO HORARIO DE TRABALHO", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_offset += 25
        
        # Verificar se sistema está bloqueado
        if self.is_employee_locked('unknown'):
            lockout_time = self.locked_until.get('unknown', datetime.now())
            remaining = (lockout_time - datetime.now()).total_seconds()
            cv2.putText(frame, f"SISTEMA BLOQUEADO ({int(remaining)}s)", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_offset += 25
        
        if getattr(self.config, 'SHOW_INSTRUCTIONS', True):
            cv2.putText(frame, "Pressione 'q' para sair", 
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def recognize_faces(self):
        """Loop principal de reconhecimento facial"""
        self.logger.info("Iniciando reconhecimento facial avançado")
        
        frame_count = 0
        process_this_frame = True
        
        while True:
            start_time = time.time()
            
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("Erro ao capturar frame da câmera")
                break
            
            # Espelhar imagem
            frame = cv2.flip(frame, 1)
            
            # Salvar frame para debug se configurado
            if (getattr(self.config, 'SAVE_DEBUG_FRAMES', False) and 
                frame_count % 60 == 0):  # A cada 60 frames
                self.save_debug_frame(frame, frame_count)
            
            # Processar reconhecimento apenas em alguns frames
            process_interval = getattr(self.config, 'PROCESS_EVERY_N_FRAMES', 2)
            
            if frame_count % process_interval == 0:
                # Redimensionar para processamento mais rápido
                processing_scale = getattr(self.config, 'PROCESSING_SCALE', 0.25)
                small_frame = cv2.resize(frame, (0, 0), fx=processing_scale, fy=processing_scale)
                rgb_small_frame = small_frame[:, :, ::-1]
                
                # Detectar rostos
                detection_model = getattr(self.config, 'FACE_DETECTION_MODEL', 'hog')
                face_locations = face_recognition.face_locations(rgb_small_frame, model=detection_model)
                
                if face_locations:
                    # Codificar rostos
                    num_jitters = getattr(self.config, 'FACE_ENCODING_SAMPLES', 1)
                    face_encodings = face_recognition.face_encodings(
                        rgb_small_frame, face_locations, num_jitters=num_jitters
                    )
                    
                    # Processar reconhecimento
                    face_names = self.process_recognition(face_encodings, face_locations)
                else:
                    face_names = []
            
            # Desenhar interface
            frame = self.draw_interface(frame, face_locations if 'face_locations' in locals() else [], 
                                      face_names if 'face_names' in locals() else [])
            
            # Mostrar frame
            cv2.imshow('Sistema de Ponto - Reconhecimento Facial Avançado', frame)
            
            # Controle de FPS
            self.fps_counter.append(time.time())
            
            # Verificar saída
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):  # Screenshot
                self.save_screenshot(frame)
            elif key == ord('r'):  # Reload encodings
                self.load_known_faces()
                self.logger.info("Encodings recarregados")
            
            frame_count += 1
        
        # Limpeza
        self.camera.release()
        cv2.destroyAllWindows()
        self.logger.info("Sistema de reconhecimento encerrado")
    
    def save_debug_frame(self, frame, frame_number):
        """Salva frame para debug"""
        try:
            if not hasattr(self.config, 'DEBUG_FRAMES_DIR'):
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"debug_frame_{timestamp}_{frame_number:06d}.jpg"
            filepath = os.path.join(self.config.DEBUG_FRAMES_DIR, filename)
            
            cv2.imwrite(filepath, frame)
            self.logger.debug(f"Frame de debug salvo: {filename}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar frame de debug: {e}")
    
    def save_screenshot(self, frame):
        """Salva screenshot manual"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{timestamp}.jpg"
            filepath = os.path.join(self.config.DATA_DIR, filename)
            
            cv2.imwrite(filepath, frame)
            self.logger.info(f"Screenshot salvo: {filename}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar screenshot: {e}")
    
    def register_employee_from_camera(self, employee_id, name):
        """Registra funcionário capturando múltiplas fotos da câmera"""
        self.logger.info(f"Registrando funcionário: {name} (ID: {employee_id})")
        
        captured_encodings = []
        photos_needed = 3  # Capturar múltiplas fotos para melhor precisão
        
        while len(captured_encodings) < photos_needed:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            
            # Instruções na tela
            remaining = photos_needed - len(captured_encodings)
            cv2.putText(frame, f"Registrando: {name} (ID: {employee_id})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Fotos restantes: {remaining}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Pressione ESPACO para capturar ou ESC para cancelar", 
                       (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, "Mantenha o rosto centralizado e bem iluminado", 
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Detectar rosto para feedback visual
            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # Desenhar retângulo se rosto detectado
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            cv2.imshow('Registro de Funcionario', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Espaço para capturar
                if len(face_locations) == 1:
                    # Apenas um rosto detectado
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    if len(face_encodings) > 0:
                        captured_encodings.append(face_encodings[0])
                        self.logger.info(f"Foto {len(captured_encodings)}/{photos_needed} capturada")
                        
                        # Salvar foto se configurado
                        if hasattr(self.config, 'PHOTOS_DIR'):
                            photo_filename = f"{employee_id}_{len(captured_encodings)}.jpg"
                            photo_path = os.path.join(self.config.PHOTOS_DIR, photo_filename)
                            cv2.imwrite(photo_path, frame)
                        
                        time.sleep(1)  # Pausa entre capturas
                    else:
                        self.logger.warning("Nenhuma codificação facial gerada")
                elif len(face_locations) == 0:
                    self.logger.warning("Nenhum rosto detectado")
                else:
                    self.logger.warning("Múltiplos rostos detectados. Apenas um permitido.")
                    
            elif key == 27:  # ESC para cancelar
                self.logger.info("Registro cancelado")
                cv2.destroyWindow('Registro de Funcionario')
                return False
        
        # Calcular encoding médio para melhor precisão
        if captured_encodings:
            average_encoding = np.mean(captured_encodings, axis=0)
            
            # Adicionar funcionário
            self.known_faces.append(average_encoding)
            self.known_names.append(name)
            self.known_ids.append(employee_id)
            
            self.save_known_faces()
            self.logger.info(f"Funcionário {name} registrado com sucesso!")
            
            cv2.destroyWindow('Registro de Funcionario')
            return True
        
        cv2.destroyWindow('Registro de Funcionario')
        return False
    
    def cleanup_resources(self):
        """Limpa recursos do sistema"""
        if hasattr(self, 'camera') and self.camera.isOpened():
            self.camera.release()
        cv2.destroyAllWindows()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_processing.set()
            self.processing_thread.join()

def main():
    """Função principal"""
    system = None
    
    try:
        # Imprimir configuração se em modo debug
        if hasattr(Config, 'DEBUG_MODE') and Config.DEBUG_MODE:
            Config.print_config()
        
        # Criar instância do sistema
        system = AdvancedFacialRecognitionTimeCard()
        
        print("=== Sistema Avançado de Reconhecimento Facial para Ponto ===")
        print("1. Iniciar reconhecimento")
        print("2. Registrar novo funcionário")
        print("3. Recarregar configurações")
        print("4. Estatísticas do sistema")
        print("5. Sair")
        
        while True:
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == "1":
                system.recognize_faces()
                
            elif choice == "2":
                employee_id = input("ID do funcionário: ").strip()
                name = input("Nome do funcionário: ").strip()
                
                if employee_id and name:
                    success = system.register_employee_from_camera(employee_id, name)
                    if success:
                        print("✅ Funcionário registrado com sucesso!")
                    else:
                        print("❌ Falha no registro do funcionário")
                else:
                    print("❌ ID e nome são obrigatórios!")
                    
            elif choice == "3":
                # Recarregar configurações
                load_custom_config()
                Config.validate_config()
                system.config = Config
                print("✅ Configurações recarregadas")
                
            elif choice == "4":
                # Mostrar estatísticas
                print(f"\n📊 Estatísticas do Sistema:")
                print(f"Funcionários cadastrados: {len(system.known_faces)}")
                print(f"Última atualização dos encodings: {os.path.getmtime(Config.FACE_ENCODINGS_FILE) if os.path.exists(Config.FACE_ENCODINGS_FILE) else 'N/A'}")
                print(f"Cache de encodings: {len(system.encoding_cache) if system.encoding_cache else 'Desabilitado'}")
                print(f"Tentativas falhadas: {len(system.failed_attempts.get('unknown', []))}")
                
            elif choice == "5":
                break
                
            else:
                print("❌ Opção inválida!")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Sistema interrompido pelo usuário")
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        logging.error(f"Erro inesperado: {e}", exc_info=True)
    
    finally:
        if system:
            system.cleanup_resources()
        print("👋 Sistema encerrado")

if __name__ == "__main__":
    main()