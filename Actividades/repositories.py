"""
Módulo de repositories para acceso a datos (JSON y Excel).
Sigue el principio de responsabilidad única.
"""

import os
import json
import pandas as pd
from datetime import datetime
from config import (
    CONFIG_FILE, USERS_FILE, EXCEL_FILE, TEMPLATE_EXCEL,
    ACTIVIDADES_DEFAULT, UBICACIONES_DEFAULT,
    TIPOS_SOLICITUD_DEFAULT, MEDIOS_SOLICITUD_DEFAULT,
    COLUMNAS, logger
)

class BaseJSONRepository:
    """Clase base para repositorios que manejan archivos JSON"""
    def __init__(self, file_path, default_data=None):
        self.file_path = file_path
        self.default_data = default_data or {}

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self.default_data
        except Exception as e:
            logger.error(f"Error cargando {self.file_path}: {e}")
            return self.default_data

    def _save(self, data):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error guardando {self.file_path}: {e}")
            return False

class UserRepository(BaseJSONRepository):
    """Maneja la persistencia de usuarios y sus actividades personales"""
    def __init__(self):
        super().__init__(USERS_FILE, {"usuarios": ["admin"], "actividades": {}})

    def setup(self):
        if not os.path.exists(self.file_path):
            self._save(self.default_data)

    def get_all_users(self):
        data = self._load()
        return data.get("usuarios", [])

    def add_user(self, username):
        data = self._load()
        if username not in data["usuarios"]:
            data["usuarios"].append(username)
            return self._save(data)
        return False

    def delete_user(self, username):
        data = self._load()
        if username in data["usuarios"]:
            data["usuarios"].remove(username)
            # También limpiar sus actividades y config
            if "actividades" in data and username in data["actividades"]:
                del data["actividades"][username]
            if "configuraciones" in data and username in data["configuraciones"]:
                del data["configuraciones"][username]
            return self._save(data)
        return False

    def get_user_activities(self, username):
        data = self._load()
        return data.get("actividades", {}).get(username, [])

    def save_user_activities(self, username, activities):
        data = self._load()
        if "actividades" not in data:
            data["actividades"] = {}
        data["actividades"][username] = activities
        return self._save(data)

    def get_user_config(self, username):
        data = self._load()
        configs = data.get("configuraciones", {})
        if username in configs:
            return configs[username]
        return {
            "tema": "claro",
            "columnas_visibles": ["TIPO DE ACTIVIDAD", "FECHA", "DEPENDENCIA", "SOLICITANTE", "DESCRIPCIÓN", "CUMPLIDO"],
            "orden_por": "FECHA",
            "orden_direccion": "desc"
        }

    def save_user_config(self, username, config):
        data = self._load()
        if "configuraciones" not in data:
            data["configuraciones"] = {}
        data["configuraciones"][username] = config
        return self._save(data)

class ConfigRepository(BaseJSONRepository):
    """Maneja la configuración global de la aplicación"""
    def __init__(self):
        super().__init__(CONFIG_FILE, {
            "actividades": ACTIVIDADES_DEFAULT,
            "ubicaciones": UBICACIONES_DEFAULT,
            "tipos_actividad": TIPOS_SOLICITUD_DEFAULT,
            "medios_solicitud": MEDIOS_SOLICITUD_DEFAULT,
            "dependencias": []
        })

    def setup(self):
        if not os.path.exists(self.file_path):
            self._save(self.default_data)

    def get_config(self):
        return self._load()

    def update_config(self, key, value):
        data = self._load()
        data[key] = value
        return self._save(data)

    def get_global_activities(self):
        return self.get_config().get("actividades", ACTIVIDADES_DEFAULT)

class RecordRepository:
    """Maneja los registros de actividades en el archivo Excel"""
    def __init__(self):
        self.file_path = EXCEL_FILE

    def setup(self):
        if not os.path.exists(self.file_path):
            df = pd.DataFrame(columns=COLUMNAS)
            df.to_excel(self.file_path, index=False, engine='openpyxl')

    def load_all(self, usuario=None):
        try:
            if os.path.exists(self.file_path):
                df = pd.read_excel(self.file_path, engine='openpyxl')
                if usuario and usuario != "admin" and 'USUARIO' in df.columns:
                    df = df[df['USUARIO'] == usuario]
                return df.fillna('')
            return pd.DataFrame(columns=COLUMNAS)
        except Exception as e:
            logger.error(f"Error cargando registros: {e}")
            return pd.DataFrame(columns=COLUMNAS)

    def add_record(self, record_data):
        try:
            df_existente = self.load_all()
            nuevo_df = pd.DataFrame([record_data])
            df_final = pd.concat([df_existente, nuevo_df], ignore_index=True)
            df_final.to_excel(self.file_path, index=False, engine='openpyxl')
            return True
        except Exception as e:
            logger.error(f"Error guardando registro: {e}")
            return False

class ReportRepository:
    """Maneja la generación de reportes y estadísticas"""
    def __init__(self, record_repo):
        self.record_repo = record_repo

    def get_filtered_data(self, fecha_inicio=None, fecha_fin=None, usuario=None, actividad=None):
        df = self.record_repo.load_all(usuario)
        if df.empty:
            return df

        if 'FECHA' in df.columns:
            df['FECHA_DT'] = pd.to_datetime(df['FECHA'], errors='coerce')
            
            if fecha_inicio:
                df = df[df['FECHA_DT'] >= pd.to_datetime(fecha_inicio)]
            if fecha_fin:
                df = df[df['FECHA_DT'] <= pd.to_datetime(fecha_fin)]
        
        if actividad and actividad != 'Todas' and 'TIPO DE ACTIVIDAD' in df.columns:
            df = df[df['TIPO DE ACTIVIDAD'] == actividad]
            
        return df

    def calculate_stats(self, df):
        if df.empty:
            return {}
        
        stats = {
            'total_registros': len(df),
            'fecha_inicio': df['FECHA_DT'].min().strftime('%Y-%m-%d') if 'FECHA_DT' in df.columns and not df.empty else 'N/A',
            'fecha_fin': df['FECHA_DT'].max().strftime('%Y-%m-%d') if 'FECHA_DT' in df.columns and not df.empty else 'N/A'
        }
        
        for col, key in [('TIPO DE ACTIVIDAD', 'conteo_por_actividad'), 
                         ('TIPO DE SOLICITUD', 'conteo_por_solicitud'), 
                         ('MEDIO DE SOLICITUD', 'conteo_por_medio')]:
            if col in df.columns:
                counts = df[col].value_counts().to_dict()
                stats[key] = {str(k): int(v) for k, v in counts.items()}
                
        return stats
