#!/usr/bin/env python3
"""
Utilitário para gerenciar o banco de dados do sistema de ponto
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
import json

class TimecardDBManager:
    def __init__(self, db_path="data/timecard.db"):
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Garante que o banco de dados existe"""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))
    
    def get_connection(self):
        """Retorna conexão com o banco"""
        return sqlite3.connect(self.db_path)
    
    def list_employees(self):
        """Lista todos os funcionários"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, created_at FROM employee ORDER BY name")
        employees = cursor.fetchall()
        
        conn.close()
        
        print("\n📋 FUNCIONÁRIOS CADASTRADOS:")
        print("-" * 50)
        print(f"{'ID':<10} {'Nome':<25} {'Cadastrado em'}")
        print("-" * 50)
        
        for emp_id, name, created_at in employees:
            print(f"{emp_id:<10} {name:<25} {created_at}")
        
        print(f"\nTotal: {len(employees)} funcionários")
        return employees
    
    def list_timecards(self, employee_id=None, days=7):
        """Lista registros de ponto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Data limite
        date_limit = (datetime.now() - timedelta(days=days)).isoformat()
        
        if employee_id:
            cursor.execute("""
                SELECT employee_id, employee_name, timestamp, entry_type, recognition_method 
                FROM time_card 
                WHERE employee_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (employee_id, date_limit))
            title = f"REGISTROS DE PONTO - {employee_id} (últimos {days} dias)"
        else:
            cursor.execute("""
                SELECT employee_id, employee_name, timestamp, entry_type, recognition_method 
                FROM time_card 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (date_limit,))
            title = f"ÚLTIMOS REGISTROS DE PONTO ({days} dias)"
        
        records = cursor.fetchall()
        conn.close()
        
        print(f"\n⏰ {title}:")
        print("-" * 80)
        print(f"{'ID':<8} {'Nome':<20} {'Data/Hora':<20} {'Tipo':<8} {'Método'}")
        print("-" * 80)
        
        for emp_id, name, timestamp, entry_type, method in records:
            # Formatar timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%d/%m/%Y %H:%M")
            except:
                formatted_time = timestamp[:16]
            
            entry_icon = "🟢" if entry_type == "entrada" else "🔴"
            print(f"{emp_id:<8} {name:<20} {formatted_time:<20} {entry_icon} {entry_type:<6} {method}")
        
        print(f"\nTotal: {len(records)} registros")
        return records
    
    def employee_report(self, employee_id, days=30):
        """Relatório detalhado de um funcionário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Informações do funcionário
        cursor.execute("SELECT id, name, created_at FROM employee WHERE id = ?", (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            print(f"❌ Funcionário {employee_id} não encontrado")
            return
        
        emp_id, name, created_at = employee
        
        # Registros de ponto
        date_limit = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT timestamp, entry_type 
            FROM time_card 
            WHERE employee_id = ? AND timestamp >= ?
            ORDER BY timestamp
        """, (employee_id, date_limit))
        
        records = cursor.fetchall()
        conn.close()
        
        print(f"\n👤 RELATÓRIO - {name} (ID: {emp_id})")
        print("=" * 60)
        print(f"Cadastrado em: {created_at}")
        print(f"Período: Últimos {days} dias")
        print(f"Total de registros: {len(records)}")
        
        # Agrupar por dia
        days_data = {}
        for timestamp, entry_type in records:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                day = dt.date()
                if day not in days_data:
                    days_data[day] = []
                days_data[day].append((dt.time(), entry_type))
            except:
                continue
        
        print(f"\nDias trabalhados: {len(days_data)}")
        print("\n📅 REGISTROS POR DIA:")
        print("-" * 60)
        
        for day in sorted(days_data.keys(), reverse=True):
            print(f"\n{day.strftime('%A, %d/%m/%Y')}:")
            
            day_records = sorted(days_data[day])
            entrada = None
            
            for time_obj, entry_type in day_records:
                time_str = time_obj.strftime("%H:%M")
                
                if entry_type == "entrada":
                    entrada = time_obj
                    print(f"  🟢 Entrada: {time_str}")
                else:
                    print(f"  🔴 Saída:   {time_str}")
                    
                    # Calcular horas trabalhadas
                    if entrada:
                        worked = datetime.combine(day, time_obj) - datetime.combine(day, entrada)
                        hours = worked.total_seconds() / 3600
                        print(f"     ⏱️ Trabalhou: {hours:.1f}h")
                        entrada = None
    
    def cleanup_old_records(self, days=90):
        """Remove registros antigos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        date_limit = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Contar registros a serem removidos
        cursor.execute("SELECT COUNT(*) FROM time_card WHERE timestamp < ?", (date_limit,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"✅ Nenhum registro anterior a {days} dias encontrado")
            conn.close()
            return
        
        print(f"⚠️ Encontrados {count} registros anteriores a {days} dias")
        confirm = input("Deseja removê-los? (s/N): ").lower().strip()
        
        if confirm in ['s', 'sim', 'y', 'yes']:
            cursor.execute("DELETE FROM time_card WHERE timestamp < ?", (date_limit,))
            conn.commit()
            print(f"✅ {count} registros removidos")
        else:
            print("❌ Operação cancelada")
        
        conn.close()
    
    def export_data(self, filename=None):
        """Exporta dados para JSON"""
        if not filename:
            filename = f"backup_ponto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Exportar funcionários
        cursor.execute("SELECT id, name, created_at FROM employee")
        employees = [{"id": row[0], "name": row[1], "created_at": row[2]} 
                    for row in cursor.fetchall()]
        
        # Exportar registros
        cursor.execute("""
            SELECT employee_id, employee_name, timestamp, entry_type, recognition_method, created_at 
            FROM time_card ORDER BY timestamp
        """)
        timecards = [{"employee_id": row[0], "employee_name": row[1], "timestamp": row[2], 
                     "entry_type": row[3], "recognition_method": row[4], "created_at": row[5]} 
                    for row in cursor.fetchall()]
        
        conn.close()
        
        data = {
            "export_date": datetime.now().isoformat(),
            "employees": employees,
            "timecards": timecards
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Dados exportados para: {filename}")
        print(f"   Funcionários: {len(employees)}")
        print(f"   Registros: {len(timecards)}")
    
    def stats(self):
        """Estatísticas do sistema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Estatísticas básicas
        cursor.execute("SELECT COUNT(*) FROM employee")
        total_employees = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM time_card")
        total_records = cursor.fetchone()[0]
        
        # Registros por dia (últimos 7 dias)
        date_limit = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("""
            SELECT DATE(timestamp) as day, COUNT(*) 
            FROM time_card 
            WHERE timestamp >= ? 
            GROUP BY DATE(timestamp) 
            ORDER BY day DESC
        """, (date_limit,))
        daily_stats = cursor.fetchall()
        
        # Funcionário mais ativo
        cursor.execute("""
            SELECT employee_name, COUNT(*) as registros 
            FROM time_card 
            WHERE timestamp >= ? 
            GROUP BY employee_id, employee_name 
            ORDER BY registros DESC 
            LIMIT 5
        """, (date_limit,))
        top_employees = cursor.fetchall()
        
        conn.close()
        
        print("\n📊 ESTATÍSTICAS DO SISTEMA")
        print("=" * 50)
        print(f"Total de funcionários: {total_employees}")
        print(f"Total de registros: {total_records}")
        
        print(f"\n📅 Registros por dia (últimos 7 dias):")
        for day, count in daily_stats:
            print(f"  {day}: {count} registros")
        
        print(f"\n🏆 Funcionários mais ativos (últimos 7 dias):")
        for name, count in top_employees:
            print(f"  {name}: {count} registros")

def main():
    if len(sys.argv) < 2:
        print("=== GERENCIADOR DO BANCO DE DADOS - SISTEMA DE PONTO ===")
        print("\nComandos disponíveis:")
        print("  employees                    - Listar funcionários")
        print("  timecards [employee_id]      - Listar registros de ponto")
        print("  report <employee_id>         - Relatório de funcionário")
        print("  stats                        - Estatísticas do sistema")
        print("  export [filename]            - Exportar dados para JSON")
        print("  cleanup [days]               - Remover registros antigos")
        print("\nExemplos:")
        print("  python db_manager.py employees")
        print("  python db_manager.py timecards 12345")
        print("  python db_manager.py report 12345")
        print("  python db_manager.py cleanup 90")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    db = TimecardDBManager()
    
    try:
        if command == "employees":
            db.list_employees()
        
        elif command == "timecards":
            employee_id = sys.argv[2] if len(sys.argv) > 2 else None
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
            db.list_timecards(employee_id, days)
        
        elif command == "report":
            if len(sys.argv) < 3:
                print("❌ Usage: python db_manager.py report <employee_id>")
                sys.exit(1)
            employee_id = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            db.employee_report(employee_id, days)
        
        elif command == "stats":
            db.stats()
        
        elif command == "export":
            filename = sys.argv[2] if len(sys.argv) > 2 else None
            db.export_data(filename)
        
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
            db.cleanup_old_records(days)
        
        else:
            print(f"❌ Comando desconhecido: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()