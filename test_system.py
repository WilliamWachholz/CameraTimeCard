#!/usr/bin/env python3
"""
Script de teste para verificar se o sistema de reconhecimento facial está funcionando
"""

import cv2
import requests
import json
import time
import sys
import os
from datetime import datetime

def test_camera():
    """Testa se a câmera está funcionando"""
    print("🎥 Testando câmera...")
    
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ Erro: Câmera não encontrada ou não pode ser acessada")
        return False
    
    # Tentar capturar um frame
    ret, frame = camera.read()
    if not ret:
        print("❌ Erro: Não foi possível capturar frame da câmera")
        camera.release()
        return False
    
    print(f"✅ Câmera OK - Resolução: {frame.shape[1]}x{frame.shape[0]}")
    
    # Mostrar preview por 3 segundos
    print("📸 Mostrando preview da câmera por 3 segundos...")
    start_time = time.time()
    while time.time() - start_time < 3:
        ret, frame = camera.read()
        if ret:
            cv2.putText(frame, "Teste da Camera - Pressione ESC para sair", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Teste da Camera', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break
    
    camera.release()
    cv2.destroyAllWindows()
    return True

def test_dependencies():
    """Testa se todas as dependências estão instaladas"""
    print("📦 Testando dependências...")
    
    dependencies = {
        'cv2': 'opencv-python',
        'face_recognition': 'face-recognition',
        'requests': 'requests',
        'numpy': 'numpy',
        'pickle': 'built-in',
        'flask': 'flask',
        'flask_sqlalchemy': 'flask-sqlalchemy'
    }
    
    missing = []
    for module, package in dependencies.items():
        try:
            if module == 'flask_sqlalchemy':
                import flask_sqlalchemy
            else:
                __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (instale: pip install {package})")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Dependências faltando: {', '.join(missing)}")
        print("Execute: pip install " + " ".join(missing))
        return False
    
    return True

def test_backend(url="http://localhost:5000"):
    """Testa se o backend está rodando"""
    print(f"🔗 Testando backend em {url}...")
    
    try:
        # Teste health check
        response = requests.get(f"{url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend respondendo")
            
            # Teste de registro de ponto
            test_data = {
                "employee_id": "TEST001",
                "employee_name": "Teste Usuario",
                "timestamp": datetime.now().isoformat(),
                "recognition_method": "test"
            }
            
            response = requests.post(f"{url}/api/timecard", 
                                   json=test_data, timeout=5)
            
            if response.status_code == 200:
                print("✅ Endpoint de registro funcionando")
                result = response.json()
                print(f"   Resposta: {result.get('message', 'OK')}")
                return True
            else:
                print(f"❌ Erro no endpoint de registro: {response.status_code}")
                return False
                
        else:
            print(f"❌ Backend retornou status {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print("❌ Não foi possível conectar ao backend")
        print("   Certifique-se de que o backend está rodando: python backend.py")
        return False
    except requests.Timeout:
        print("❌ Timeout ao conectar com backend")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_face_recognition():
    """Testa o reconhecimento facial básico"""
    print("👤 Testando reconhecimento facial...")
    
    try:
        import face_recognition
        import numpy as np
        
        # Criar uma imagem de teste simples
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Tentar encontrar rostos (não deve encontrar nenhum)
        face_locations = face_recognition.face_locations(test_image)
        print(f"✅ face_recognition funcionando - Rostos encontrados: {len(face_locations)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no reconhecimento facial: {e}")
        return False

def test_file_permissions():
    """Testa permissões de arquivo"""
    print("📁 Testando permissões de arquivo...")
    
    test_files = [
        "data/face_encodings.pkl",
        "logs/system.log",
        "data/timecard.db"
    ]
    
    # Criar diretórios se não existirem
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    for file_path in test_files:
        try:
            # Tentar criar/escrever arquivo
            with open(file_path, 'a') as f:
                f.write("")
            print(f"✅ {file_path}")
        except PermissionError:
            print(f"❌ Sem permissão para escrever: {file_path}")
            return False
        except Exception as e:
            print(f"⚠️ Aviso em {file_path}: {e}")
    
    return True

def main():
    """Executa todos os testes"""
    print("=== TESTE DO SISTEMA DE RECONHECIMENTO FACIAL ===\n")
    
    tests = [
        ("Dependências", test_dependencies),
        ("Permissões de arquivo", test_file_permissions),
        ("Câmera", test_camera),
        ("Reconhecimento facial", test_face_recognition),
        ("Backend", test_backend)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name.upper()} ---")
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print("\n❌ Teste interrompido pelo usuário")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erro inesperado no teste {test_name}: {e}")
            results[test_name] = False
    
    # Resumo dos resultados
    print("\n" + "="*50)
    print("RESUMO DOS TESTES:")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema pronto para uso")
        print("\nPara iniciar o sistema:")
        print("1. ./start_system.sh (tudo junto)")
        print("2. python backend.py + python facial_recognition_system.py (separado)")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("❌ Corrija os problemas antes de usar o sistema")
        print("\nVerifique:")
        print("- Dependências instaladas: pip install -r requirements.txt")
        print("- Câmera conectada e funcionando")
        print("- Backend rodando: python backend.py")
        print("- Permissões de arquivo")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Teste cancelado pelo usuário")
        sys.exit(1)