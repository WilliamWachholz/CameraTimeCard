import cv2
import face_recognition
import numpy as np
import requests
import json
import os
from datetime import datetime
import pickle
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FacialRecognitionTimeCard:
    def __init__(self, backend_url="http://localhost:8000/api"):
        self.backend_url = backend_url
        self.known_faces = []
        self.known_names = []
        self.known_ids = []
        self.face_encodings_file = "face_encodings.pkl"
        
        # Carregar rostos conhecidos
        self.load_known_faces()
        
        # Configurações da câmera
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Configurações de reconhecimento
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_this_frame = True
        
        # Controle de cooldown para evitar registros duplicados
        self.last_recognition = {}
        self.recognition_cooldown = 10  # segundos

    def load_known_faces(self):
        """Carrega as codificações faciais salvas"""
        if os.path.exists(self.face_encodings_file):
            try:
                with open(self.face_encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_faces = data['encodings']
                    self.known_names = data['names']
                    self.known_ids = data['ids']
                logging.info(f"Carregados {len(self.known_faces)} rostos conhecidos")
            except Exception as e:
                logging.error(f"Erro ao carregar rostos: {e}")
        else:
            logging.info("Arquivo de rostos não encontrado. Iniciando com base vazia.")

    def save_known_faces(self):
        """Salva as codificações faciais"""
        try:
            data = {
                'encodings': self.known_faces,
                'names': self.known_names,
                'ids': self.known_ids
            }
            with open(self.face_encodings_file, 'wb') as f:
                pickle.dump(data, f)
            logging.info("Rostos salvos com sucesso")
        except Exception as e:
            logging.error(f"Erro ao salvar rostos: {e}")

    def register_new_employee(self, employee_id, name, image_path):
        """Registra um novo funcionário no sistema"""
        try:
            # Carregar imagem
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                logging.error("Nenhum rosto encontrado na imagem")
                return False
            
            if len(face_encodings) > 1:
                logging.warning("Múltiplos rostos encontrados. Usando o primeiro.")
            
            # Adicionar à base de dados
            self.known_faces.append(face_encodings[0])
            self.known_names.append(name)
            self.known_ids.append(employee_id)
            
            # Salvar
            self.save_known_faces()
            
            logging.info(f"Funcionário {name} (ID: {employee_id}) registrado com sucesso")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao registrar funcionário: {e}")
            return False

    def send_timecard_to_backend(self, employee_id, employee_name, timestamp):
        """Envia registro de ponto para o backend"""
        try:
            data = {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "timestamp": timestamp,
                "recognition_method": "facial"
            }
            
            response = requests.post(
                f"{self.backend_url}/timecard",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"Ponto registrado: {result}")
                return True, result
            else:
                logging.error(f"Erro no backend: {response.status_code} - {response.text}")
                return False, None
                
        except requests.RequestException as e:
            logging.error(f"Erro de conexão com backend: {e}")
            return False, None

    def can_register_again(self, employee_id):
        """Verifica se pode registrar novamente (cooldown)"""
        now = datetime.now()
        if employee_id in self.last_recognition:
            time_diff = (now - self.last_recognition[employee_id]).total_seconds()
            return time_diff >= self.recognition_cooldown
        return True

    def recognize_faces(self):
        """Loop principal de reconhecimento facial"""
        logging.info("Iniciando reconhecimento facial. Pressione 'q' para sair.")
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                logging.error("Erro ao capturar frame da câmera")
                break
            
            # Espelhar imagem para melhor usabilidade
            frame = cv2.flip(frame, 1)
            
            # Processar apenas a cada 2 frames para otimização
            if self.process_this_frame:
                # Redimensionar frame para processamento mais rápido
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = small_frame[:, :, ::-1]
                
                # Encontrar rostos
                self.face_locations = face_recognition.face_locations(rgb_small_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
                
                self.face_names = []
                for face_encoding in self.face_encodings:
                    matches = face_recognition.compare_faces(self.known_faces, face_encoding, tolerance=0.6)
                    name = "Desconhecido"
                    employee_id = None
                    
                    face_distances = face_recognition.face_distance(self.known_faces, face_encoding)
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                            name = self.known_names[best_match_index]
                            employee_id = self.known_ids[best_match_index]
                            
                            # Registrar ponto se passou do cooldown
                            if employee_id and self.can_register_again(employee_id):
                                timestamp = datetime.now().isoformat()
                                success, result = self.send_timecard_to_backend(employee_id, name, timestamp)
                                
                                if success:
                                    self.last_recognition[employee_id] = datetime.now()
                                    logging.info(f"Ponto registrado para {name} (ID: {employee_id})")
                    
                    self.face_names.append(name)
            
            self.process_this_frame = not self.process_this_frame
            
            # Desenhar retângulos e nomes
            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                # Escalar de volta para o tamanho original
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Cor do retângulo baseada no reconhecimento
                color = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)
                
                # Desenhar retângulo
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Desenhar label
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
            
            # Adicionar informações na tela
            cv2.putText(frame, f"Funcionarios cadastrados: {len(self.known_faces)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Pressione 'q' para sair", 
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostrar frame
            cv2.imshow('Sistema de Ponto - Reconhecimento Facial', frame)
            
            # Verificar se deve sair
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Limpeza
        self.camera.release()
        cv2.destroyAllWindows()

    def register_employee_from_camera(self, employee_id, name):
        """Registra funcionário capturando foto da câmera"""
        logging.info(f"Posicione o funcionário {name} na frente da câmera e pressione ESPAÇO para capturar")
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            
            # Mostrar instruções
            cv2.putText(frame, f"Registrando: {name} (ID: {employee_id})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Pressione ESPACO para capturar ou ESC para cancelar", 
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Registro de Funcionario', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Espaço para capturar
                # Processar o frame atual
                rgb_frame = frame[:, :, ::-1]
                face_encodings = face_recognition.face_encodings(rgb_frame)
                
                if len(face_encodings) == 0:
                    logging.error("Nenhum rosto detectado. Tente novamente.")
                    continue
                
                if len(face_encodings) > 1:
                    logging.warning("Múltiplos rostos detectados. Usando o primeiro.")
                
                # Adicionar funcionário
                self.known_faces.append(face_encodings[0])
                self.known_names.append(name)
                self.known_ids.append(employee_id)
                
                self.save_known_faces()
                logging.info(f"Funcionário {name} registrado com sucesso!")
                break
                
            elif key == 27:  # ESC para cancelar
                logging.info("Registro cancelado")
                break
        
        cv2.destroyWindow('Registro de Funcionario')


def main():
    # Configuração do backend - ajuste a URL conforme necessário
    backend_url = "http://localhost:8000/api"
    
    # Criar instância do sistema
    system = FacialRecognitionTimeCard(backend_url)
    
    print("=== Sistema de Reconhecimento Facial para Ponto ===")
    print("1. Iniciar reconhecimento")
    print("2. Registrar novo funcionário")
    print("3. Sair")
    
    while True:
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            system.recognize_faces()
            
        elif choice == "2":
            employee_id = input("ID do funcionário: ").strip()
            name = input("Nome do funcionário: ").strip()
            
            if employee_id and name:
                system.register_employee_from_camera(employee_id, name)
            else:
                print("ID e nome são obrigatórios!")
                
        elif choice == "3":
            break
            
        else:
            print("Opção inválida!")
    
    system.camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()