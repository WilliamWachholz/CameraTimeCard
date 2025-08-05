    elif command -v pacman &> /dev/null; then
        print_status "Detectado Arch Linux"
        sudo pacman -S --noconfirm python python-pip cmake opencv boost python-numpy
    fi
    
elif [[ "$OS" == "macos" ]]; then
    print_status "Detectado macOS"
    
    # Verificar se Homebrew está instalado
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew não encontrado. Instalando..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Instalar dependências via Homebrew
    brew install cmake opencv python3
fi

# Criar ambiente virtual
print_status "Criando ambiente virtual Python..."
$PYTHON_CMD -m venv venv

# Ativar ambiente virtual
print_status "Ativando ambiente virtual..."
if [[ "$OS" == "windows" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Verificar se ativação funcionou
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_success "Ambiente virtual ativado: $VIRTUAL_ENV"
else
    print_error "Falha ao ativar ambiente virtual"
    exit 1
fi

# Atualizar pip no ambiente virtual
print_status "Atualizando pip..."
pip install --upgrade pip

# Instalar wheel para evitar problemas de compilação
pip install wheel

# Instalar dependências Python
print_status "Instalando dependências Python..."

# Instalar dlib primeiro (pode demorar)
print_status "Instalando dlib (isso pode demorar alguns minutos)..."
pip install dlib

# Instalar outras dependências
pip install -r requirements.txt

# Verificar instalações críticas
print_status "Verificando instalações..."

CRITICAL_PACKAGES=("opencv-python" "face-recognition" "numpy" "requests" "flask")
for package in "${CRITICAL_PACKAGES[@]}"; do
    if python -c "import ${package//-/_}" 2>/dev/null; then
        print_success "$package instalado"
    else
        print_error "Falha na instalação de $package"
        exit 1
    fi
done

# Criar estrutura de diretórios
print_status "Criando estrutura de diretórios..."
mkdir -p data logs employee_photos data/backups employee_photos/unknown logs/debug_frames

# Criar arquivo de configuração inicial
print_status "Criando arquivo de configuração..."
cat > config_inicial.py << 'EOF'
# Configuração inicial do sistema de ponto
# Copie este arquivo para custom_config.py e modifique conforme necessário

# URL do backend (ajuste conforme sua instalação)
BACKEND_URL = "http://localhost:5000/api"

# Configurações da câmera
CAMERA_INDEX = 0  # Normalmente 0 para câmera padrão
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Reconhecimento facial
FACE_RECOGNITION_TOLERANCE = 0.6  # 0.0 a 1.0 (menor = mais rigoroso)
RECOGNITION_COOLDOWN = 10  # segundos entre registros do mesmo funcionário

# Horário de trabalho (opcional)
from datetime import time
WORK_START_TIME = time(7, 0)   # 07:00
WORK_END_TIME = time(19, 0)    # 19:00
ALLOW_AFTER_HOURS = True

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Recursos avançados
SAVE_UNKNOWN_FACES = False  # Salvar fotos de pessoas não reconhecidas
AUTO_BACKUP = True  # Backup automático dos dados
EOF

# Criar scripts de inicialização
print_status "Criando scripts de inicialização..."

# Script para iniciar apenas o backend
cat > start_backend.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "🚀 Iniciando backend do sistema de ponto..."
python backend.py
EOF

# Script para iniciar apenas o reconhecimento
cat > start_recognition.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "👁️ Iniciando sistema de reconhecimento facial..."
python facial_recognition_advanced.py
EOF

# Script para iniciar sistema completo
cat > start_complete_system.sh << 'EOF'
#!/bin/bash

echo "=== SISTEMA DE PONTO - RECONHECIMENTO FACIAL ==="

# Ativar ambiente virtual
source venv/bin/activate

# Verificar se backend já está rodando
if ! curl -s http://localhost:5000/api/health > /dev/null; then
    echo "🚀 Iniciando backend..."
    python backend.py &
    BACKEND_PID=$!
    echo "Backend iniciado com PID: $BACKEND_PID"
    
    # Aguardar backend inicializar
    echo "⏳ Aguardando backend inicializar..."
    sleep 5
    
    # Verificar se backend está respondendo
    for i in {1..10}; do
        if curl -s http://localhost:5000/api/health > /dev/null; then
            echo "✅ Backend está respondendo"
            break
        fi
        echo "⏳ Tentativa $i/10..."
        sleep 2
    done
else
    echo "✅ Backend já está rodando"
    BACKEND_PID=""
fi

# Iniciar sistema de reconhecimento
echo "👁️ Iniciando reconhecimento facial..."
python facial_recognition_advanced.py

# Cleanup quando sair
cleanup() {
    echo "🧹 Limpando processos..."
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🛑 Parando backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM
EOF

# Tornar scripts executáveis
chmod +x start_backend.sh start_recognition.sh start_complete_system.sh

# Script para registrar funcionários
cat > register_employee.sh << 'EOF'
#!/bin/bash
source venv/bin/activate

if [ $# -ne 2 ]; then
    echo "Uso: $0 <id_funcionario> '<nome_funcionario>'"
    echo "Exemplo: $0 12345 'João Silva'"
    exit 1
fi

echo "📝 Registrando funcionário: $2 (ID: $1)"
python -c "
from facial_recognition_advanced import AdvancedFacialRecognitionTimeCard
system = AdvancedFacialRecognitionTimeCard()
success = system.register_employee_from_camera('$1', '$2')
print('✅ Funcionário registrado com sucesso!' if success else '❌ Falha no registro')
"
EOF

chmod +x register_employee.sh

# Executar testes do sistema
print_status "Executando testes do sistema..."
python test_system.py

TEST_RESULT=$?

# Criar arquivo de documentação rápida
print_status "Criando documentação..."
cat > INICIO_RAPIDO.md << 'EOF'
# 🚀 INÍCIO RÁPIDO - Sistema de Ponto por Reconhecimento Facial

## 📋 Comandos Principais

### Iniciar Sistema Completo
```bash
./start_complete_system.sh
```

### Iniciar Apenas Backend
```bash
./start_backend.sh
```

### Iniciar Apenas Reconhecimento
```bash
./start_recognition.sh
```

### Registrar Novo Funcionário
```bash
./register_employee.sh 12345 "João Silva"
```

### Testar Sistema
```bash
python test_system.py
```

### Gerenciar Banco de Dados
```bash
# Listar funcionários
python db_manager.py employees

# Ver registros de ponto
python db_manager.py timecards

# Relatório de funcionário específico
python db_manager.py report 12345

# Estatísticas
python db_manager.py stats
```

## ⚙️ Configuração

1. Copie `config_inicial.py` para `custom_config.py`
2. Edite `custom_config.py` conforme sua necessidade
3. Reinicie o sistema

## 🔧 Troubleshooting

### Câmera não funciona
- Verifique se está conectada: `ls /dev/video*`
- Teste outros índices: altere `CAMERA_INDEX` em `custom_config.py`

### Backend não conecta
- Verifique se porta 5000 está livre: `lsof -i :5000`
- Teste manualmente: `curl http://localhost:5000/api/health`

### Reconhecimento impreciso
- Ajuste `FACE_RECOGNITION_TOLERANCE` (menor = mais rigoroso)
- Melhore iluminação do ambiente
- Re-registre funcionários com melhor qualidade

## 📞 Suporte

- Logs do sistema: `logs/system.log`
- Logs de debug: `logs/debug_frames/` (se habilitado)
- Teste completo: `python test_system.py`
EOF

# Resultado final
echo ""
echo "========================================================================"
if [ $TEST_RESULT -eq 0 ]; then
    print_success "INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
    echo ""
    print_success "✅ Todos os testes passaram"
    print_success "✅ Scripts de inicialização criados"
    print_success "✅ Estrutura de diretórios configurada"
    print_success "✅ Dependências instaladas"
    echo ""
    echo "🚀 PRÓXIMOS PASSOS:"
    echo "1. Teste a câmera: python test_system.py"
    echo "2. Configure o sistema: cp config_inicial.py custom_config.py"
    echo "3. Inicie o sistema: ./start_complete_system.sh"
    echo "4. Registre funcionários: ./register_employee.sh <ID> '<Nome>'"
    echo ""
    echo "📖 Documentação completa: README.md"
    echo "🚀 Início rápido: INICIO_RAPIDO.md"
else
    print_warning "INSTALAÇÃO CONCLUÍDA COM AVISOS"
    echo ""
    print_warning "⚠️ Alguns testes falharam, mas a instalação foi concluída"
    print_warning "⚠️ Verifique os logs antes de usar o sistema"
    echo ""
    echo "🔧 PARA RESOLVER PROBLEMAS:"
    echo "1. Execute novamente os testes: python test_system.py"
    echo "2. Verifique os logs: tail -f logs/system.log"
    echo "3. Consulte o README.md para troubleshooting"
fi

echo ""
echo "📁 ARQUIVOS CRIADOS:"
echo "- start_complete_system.sh  (iniciar sistema completo)"
echo "- start_backend.sh          (apenas backend)"
echo "- start_recognition.sh      (apenas reconhecimento)"
echo "- register_employee.sh      (registrar funcionários)"
echo "- config_inicial.py         (configuração exemplo)"
echo "- INICIO_RAPIDO.md          (documentação rápida)"
echo ""
echo "📂 DIRETÓRIOS CRIADOS:"
echo "- data/                     (banco de dados e encodings)"
echo "- logs/                     (logs do sistema)"
echo "- employee_photos/          (fotos dos funcionários)"
echo "- data/backups/             (backups automáticos)"
echo ""

# Mostrar informações do ambiente
echo "🔍 INFORMAÇÕES DO AMBIENTE:"
echo "- Python: $PYTHON_VERSION"
echo "- Sistema: $OS"
echo "- Ambiente virtual: $VIRTUAL_ENV"
echo "- Diretório atual: $(pwd)"
echo ""

print_success "Instalação finalizada! 🎉"
echo "========================================================================"#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir com cores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Verificar se está rodando como root (não recomendado)
if [ "$EUID" -eq 0 ]; then
    print_warning "Não é recomendado executar como root. Continue por sua conta e risco."
    read -p "Pressione Enter para continuar ou Ctrl+C para cancelar..."
fi

echo "========================================================================"
echo "    INSTALADOR DO SISTEMA DE RECONHECIMENTO FACIAL PARA PONTO"
echo "========================================================================"
echo ""

# Verificar sistema operacional
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    print_status "Sistema operacional: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    print_status "Sistema operacional: macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    print_status "Sistema operacional: Windows"
else
    print_error "Sistema operacional não identificado: $OSTYPE"
    exit 1
fi

# Verificar Python
print_status "Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 7 ]]; then
        print_success "Python $PYTHON_VERSION encontrado"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.7 ou superior é necessário. Encontrado: $PYTHON_VERSION"
        exit 1
    fi
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    if [[ $PYTHON_VERSION == 3.* ]]; then
        print_success "Python $PYTHON_VERSION encontrado"
        PYTHON_CMD="python"
    else
        print_error "Python 3.7 ou superior é necessário"
        exit 1
    fi
else
    print_error "Python não encontrado. Por favor, instale Python 3.7 ou superior."
    
    if [[ "$OS" == "linux" ]]; then
        print_status "Para instalar no Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    elif [[ "$OS" == "macos" ]]; then
        print_status "Para instalar no macOS: brew install python3"
    fi
    exit 1
fi

# Verificar pip
print_status "Verificando pip..."
if $PYTHON_CMD -m pip --version &> /dev/null; then
    print_success "pip encontrado"
else
    print_error "pip não encontrado"
    
    if [[ "$OS" == "linux" ]]; then
        print_status "Instalando pip..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        fi
    fi
fi

# Instalar dependências do sistema
print_status "Instalando dependências do sistema..."

if [[ "$OS" == "linux" ]]; then
    if command -v apt-get &> /dev/null; then
        print_status "Detectado sistema baseado em Debian/Ubuntu"
        
        # Atualizar lista de pacotes
        sudo apt-get update
        
        # Dependências essenciais
        PACKAGES=(
            "python3-dev"
            "python3-pip"
            "python3-venv"
            "cmake"
            "build-essential"
            "libopencv-dev"
            "python3-opencv"
            "libboost-python-dev"
            "libboost-system-dev"
            "libatlas-base-dev"
            "liblapack-dev"
            "libjpeg-dev"
            "libpng-dev"
            "libtiff-dev"
            "libgtk-3-dev"
            "libavcodec-dev"
            "libavformat-dev"
            "libswscale-dev"
            "libv4l-dev"
        )
        
        for package in "${PACKAGES[@]}"; do
            print_status "Instalando $package..."
            sudo apt-get install -y "$package"
        done
        
    elif command -v yum &> /dev/null; then
        print_status "Detectado sistema baseado em Red Hat/CentOS"
        
        # Grupo de desenvolvimento
        sudo yum groupinstall -y "Development Tools"
        
        # Pacotes específicos
        sudo yum install -y python3-devel cmake opencv-devel boost-python3-devel atlas-devel lapack-devel
        
    elif command -v pacman &> /dev/null;