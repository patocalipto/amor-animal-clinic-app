"""
Módulo de Gestión y Conexión a Base de Datos MySQL (XAMPP)
Clínica Veterinaria "Amor Animal"
Adaptado con exactitud a la estructura relacional de la clínica:
Rol -> Usuario -> Mascotas -> Servicio -> Horario_Disponible -> Cita -> Historial_Medico
"""

import mysql.connector
from mysql.connector import errorcode
import pandas as pd
from datetime import date, datetime, timedelta
import warnings

# Silenciar advertencia de pandas con conexiones DBAPI2 puras
warnings.filterwarnings('ignore', category=UserWarning)

CONFIG_DB_DEFAULT = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "clinica_amor_animal",
    "port": 3306
}

def obtener_conexion(config=None, include_database=True):
    """
    Crea y retorna una nueva conexión a MySQL.
    """
    cfg = config.copy() if config else CONFIG_DB_DEFAULT.copy()
    if not include_database:
        cfg.pop("database", None)
    return mysql.connector.connect(**cfg)

def probar_conexion(config=None):
    """
    Verifica si el servidor MySQL y la base de datos están disponibles.
    Retorna (True, "Mensaje de éxito") o (False, "Detalle del error").
    """
    try:
        conn = obtener_conexion(config=config, include_database=True)
        conn.close()
        return True, "Conexión exitosa a la base de datos 'clinica_amor_animal'."
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            return False, "El servidor MySQL está en línea pero la base de datos 'clinica_amor_animal' aún no ha sido creada."
        elif err.errno == 2003:
            return False, "No se puede conectar a MySQL (XAMPP). Verifica que el módulo 'MySQL' esté en 'Running' en el panel de control de XAMPP."
        elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return False, "Usuario o contraseña de MySQL incorrectos."
        else:
            return False, f"Error al conectar con MySQL: {err}"

def traducir_error_mysql(err):
    """
    Convierte errores técnicos de MySQL en explicaciones claras en español.
    """
    if isinstance(err, mysql.connector.Error):
        if err.errno == 1062:
            return "El registro ya existe. Se detectó una duplicidad en un campo único (por ejemplo: correo electrónico duplicado)."
        elif err.errno == 1451:
            return "No se puede eliminar o modificar este registro porque tiene otros datos asociados vinculados por Llave Foránea (Integridad Referencial)."
        elif err.errno == 1452:
            return "Error de Llave Foránea: El elemento relacionado (Propietario, Mascota, Horario o Servicio) no existe en la base de datos."
        elif err.errno == 2003:
            return "No se puede establecer conexión con el servidor MySQL. Verifica que XAMPP esté activo."
        return f"Error de MySQL [{err.errno}]: {err.msg}"
    return str(err)

def inicializar_base_datos(config=None):
    """
    Crea la base de datos, todas las tablas requeridas y los datos iniciales
    asegurando el correcto manejo de llaves foráneas.
    """
    cfg = config.copy() if config else CONFIG_DB_DEFAULT.copy()
    
    try:
        # 1. Conectar al servidor MySQL para asegurar la creación de la base de datos
        conn_server = obtener_conexion(cfg, include_database=False)
        cursor_server = conn_server.cursor()
        cursor_server.execute("CREATE DATABASE IF NOT EXISTS clinica_amor_animal CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
        cursor_server.close()
        conn_server.close()
        
        # 2. Conectar a la base de datos para crear tablas con sus constraints
        conn = obtener_conexion(cfg, include_database=True)
        cursor = conn.cursor()
        
        ddl_tables = [
            """
            CREATE TABLE IF NOT EXISTS Rol (
              id_rol INT(11) NOT NULL AUTO_INCREMENT,
              nombre_rol VARCHAR(50) NOT NULL,
              PRIMARY KEY (id_rol)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS Usuario (
              id_usuario INT(11) NOT NULL AUTO_INCREMENT,
              nombre VARCHAR(100) NOT NULL,
              telefono VARCHAR(15) NOT NULL,
              correo VARCHAR(100) NOT NULL,
              contrasena VARCHAR(255) NOT NULL,
              id_rol INT(11) DEFAULT NULL,
              PRIMARY KEY (id_usuario),
              UNIQUE KEY correo (correo),
              KEY id_rol (id_rol),
              CONSTRAINT usuario_ibfk_1 FOREIGN KEY (id_rol) REFERENCES Rol (id_rol) ON UPDATE CASCADE ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS Mascotas (
              id_mascota INT(11) NOT NULL AUTO_INCREMENT,
              nombre_mascota VARCHAR(50) NOT NULL,
              especie VARCHAR(50) NOT NULL,
              raza VARCHAR(50) DEFAULT NULL,
              edad_aprox INT(11) DEFAULT NULL,
              peso DECIMAL(5,2) DEFAULT NULL,
              id_usuario INT(11) DEFAULT NULL,
              PRIMARY KEY (id_mascota),
              KEY id_usuario (id_usuario),
              CONSTRAINT mascotas_ibfk_1 FOREIGN KEY (id_usuario) REFERENCES Usuario (id_usuario) ON UPDATE CASCADE ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS Servicio (
              id_servicio INT(11) NOT NULL AUTO_INCREMENT,
              nombre_servicio VARCHAR(100) NOT NULL,
              descripcion TEXT DEFAULT NULL,
              costo DECIMAL(10,2) DEFAULT NULL,
              PRIMARY KEY (id_servicio)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS Horario_Disponible (
              id_horario INT(11) NOT NULL AUTO_INCREMENT,
              fecha DATE NOT NULL,
              hora_inicio TIME NOT NULL,
              estado_horario VARCHAR(20) DEFAULT 'Disponible',
              PRIMARY KEY (id_horario)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS Cita (
              id_cita INT(11) NOT NULL AUTO_INCREMENT,
              id_mascota INT(11) DEFAULT NULL,
              id_horario INT(11) DEFAULT NULL,
              id_servicio INT(11) DEFAULT NULL,
              estado_cita VARCHAR(30) DEFAULT 'Programada',
              PRIMARY KEY (id_cita),
              KEY id_mascota (id_mascota),
              KEY id_horario (id_horario),
              KEY id_servicio (id_servicio),
              CONSTRAINT cita_ibfk_1 FOREIGN KEY (id_mascota) REFERENCES Mascotas (id_mascota) ON UPDATE CASCADE ON DELETE CASCADE,
              CONSTRAINT cita_ibfk_2 FOREIGN KEY (id_horario) REFERENCES Horario_Disponible (id_horario) ON UPDATE CASCADE ON DELETE RESTRICT,
              CONSTRAINT cita_ibfk_3 FOREIGN KEY (id_servicio) REFERENCES Servicio (id_servicio) ON UPDATE CASCADE ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS Historial_Medico (
              id_historial INT(11) NOT NULL AUTO_INCREMENT,
              id_cita INT(11) DEFAULT NULL,
              peso_actual DECIMAL(5,2) DEFAULT NULL,
              temperatura DECIMAL(4,2) DEFAULT NULL,
              sintomas TEXT DEFAULT NULL,
              diagnostico TEXT DEFAULT NULL,
              tratamiento TEXT DEFAULT NULL,
              PRIMARY KEY (id_historial),
              KEY id_cita (id_cita),
              CONSTRAINT historial_medico_ibfk_1 FOREIGN KEY (id_cita) REFERENCES Cita (id_cita) ON UPDATE CASCADE ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """
        ]
        
        for ddl in ddl_tables:
            cursor.execute(ddl)
            
        # 3. Poblar Roles si están vacíos
        cursor.execute("SELECT COUNT(*) FROM Rol")
        if cursor.fetchone()[0] == 0:
            roles_seed = [
                (1, 'Administrador'),
                (2, 'Veterinario'),
                (3, 'Propietario')
            ]
            cursor.executemany("INSERT INTO Rol (id_rol, nombre_rol) VALUES (%s, %s)", roles_seed)
            conn.commit()

        # 4. Poblar Usuarios si están vacíos
        cursor.execute("SELECT COUNT(*) FROM Usuario")
        if cursor.fetchone()[0] == 0:
            usuarios_seed = [
                (1, 'Administrador General', '555-0100', 'admin@amoranimal.com', 'admin123', 1),
                (2, 'Dr. Roberto Mendoza', '555-0201', 'roberto.mendoza@amoranimal.com', 'vet123', 2),
                (3, 'Carlos Fuentes Hernández', '555-0301', 'carlos.fuentes@correo.com', 'cliente123', 3),
                (4, 'Mariana Gómez Lozano', '555-0302', 'mariana.gomez@correo.com', 'cliente123', 3),
                (5, 'Sofía Ramírez Díaz', '555-0303', 'sofia.ramirez@correo.com', 'cliente123', 3)
            ]
            cursor.executemany("INSERT INTO Usuario (id_usuario, nombre, telefono, correo, contrasena, id_rol) VALUES (%s, %s, %s, %s, %s, %s)", usuarios_seed)
            conn.commit()

        # 5. Poblar Servicios si están vacíos
        cursor.execute("SELECT COUNT(*) FROM Servicio")
        if cursor.fetchone()[0] == 0:
            servicios_seed = [
                (1, 'Consulta General Veterinaria', 'Revisión médica completa, toma de constantes vitales y valoración física.', 250.00),
                (2, 'Vacunación y Desparasitación', 'Aplicación de esquemas preventivos de vacunas y desparasitante interno/externo.', 350.00),
                (3, 'Esterilización / Cirugía Menor', 'Procedimiento quirúrgico con anestesia segura y monitoreo constante.', 1200.00),
                (4, 'Limpieza Dental (Profilaxis)', 'Remoción de sarro por ultrasonido y pulido dental para salud bucal.', 600.00),
                (5, 'Estética Canina y Felina', 'Baño terapéutico, corte de pelo especializado, limpieza de oídos y uñas.', 300.00),
                (6, 'Urgencias Médicas', 'Atención inmediata por cuadros críticos, traumatismos o intoxicaciones.', 500.00)
            ]
            cursor.executemany("INSERT INTO Servicio (id_servicio, nombre_servicio, descripcion, costo) VALUES (%s, %s, %s, %s)", servicios_seed)
            conn.commit()

        # 6. Poblar Horarios Disponibles si están vacíos
        cursor.execute("SELECT COUNT(*) FROM Horario_Disponible")
        if cursor.fetchone()[0] == 0:
            hoy = date.today()
            manana = hoy + timedelta(days=1)
            pasado = hoy + timedelta(days=2)
            horarios_seed = [
                (1, hoy, '09:00:00', 'Ocupado'),
                (2, hoy, '10:00:00', 'Disponible'),
                (3, hoy, '11:00:00', 'Disponible'),
                (4, hoy, '12:00:00', 'Disponible'),
                (5, hoy, '16:00:00', 'Disponible'),
                (6, manana, '09:30:00', 'Disponible'),
                (7, manana, '10:30:00', 'Disponible'),
                (8, manana, '11:30:00', 'Disponible'),
                (9, pasado, '10:00:00', 'Disponible'),
                (10, pasado, '11:00:00', 'Disponible')
            ]
            cursor.executemany("INSERT INTO Horario_Disponible (id_horario, fecha, hora_inicio, estado_horario) VALUES (%s, %s, %s, %s)", horarios_seed)
            conn.commit()

        # 7. Poblar Mascotas si están vacías
        cursor.execute("SELECT COUNT(*) FROM Mascotas")
        if cursor.fetchone()[0] == 0:
            mascotas_seed = [
                (1, 'Max', 'Perro', 'Golden Retriever', 4, 30.50, 3),
                (2, 'Luna', 'Gato', 'Siamés', 2, 4.20, 3),
                (3, 'Rocky', 'Perro', 'Bulldog Francés', 3, 12.80, 4),
                (4, 'Pelusa', 'Conejo', 'Cabeza de León', 1, 1.85, 5)
            ]
            cursor.executemany("INSERT INTO Mascotas (id_mascota, nombre_mascota, especie, raza, edad_aprox, peso, id_usuario) VALUES (%s, %s, %s, %s, %s, %s, %s)", mascotas_seed)
            conn.commit()

        # 8. Poblar Citas si están vacías
        cursor.execute("SELECT COUNT(*) FROM Cita")
        if cursor.fetchone()[0] == 0:
            citas_seed = [
                (1, 1, 1, 1, 'Atendida')
            ]
            cursor.executemany("INSERT INTO Cita (id_cita, id_mascota, id_horario, id_servicio, estado_cita) VALUES (%s, %s, %s, %s, %s)", citas_seed)
            conn.commit()

        # 9. Poblar Historial Médico si está vacío
        cursor.execute("SELECT COUNT(*) FROM Historial_Medico")
        if cursor.fetchone()[0] == 0:
            historial_seed = [
                (1, 1, 30.50, 38.4, 'Decaimiento leve tras caminatas largas y ligera claudicación en miembro posterior derecho.', 'Leve esguince articular en corvejón derecho. Sin compromiso óseo.', 'Reposo relativo durante 5 días. Crioterapia local (10 min c/8 hrs) y Meloxicam 0.1 mg/kg vía oral cada 24 horas con comida.')
            ]
            cursor.executemany("INSERT INTO Historial_Medico (id_historial, id_cita, peso_actual, temperatura, sintomas, diagnostico, tratamiento) VALUES (%s, %s, %s, %s, %s, %s, %s)", historial_seed)
            conn.commit()

        cursor.close()
        conn.close()
        return True, "Base de datos y tablas inicializadas con éxito. Datos semilla cargados correctamente."
    except Exception as e:
        return False, f"Error al inicializar la base de datos: {traducir_error_mysql(e)}"

def ejecutar_consulta(query, params=None, config=None):
    """
    Ejecuta una consulta SELECT y retorna un DataFrame de pandas.
    """
    try:
        conn = obtener_conexion(config=config)
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        raise RuntimeError(traducir_error_mysql(e))

def ejecutar_escritura(query, params=None, config=None, return_last_id=False):
    """
    Ejecuta una consulta INSERT, UPDATE o DELETE con manejo transaccional.
    """
    conn = None
    try:
        conn = obtener_conexion(config=config)
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        rowcount = cursor.rowcount
        cursor.close()
        conn.close()
        return last_id if return_last_id else rowcount
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        raise RuntimeError(traducir_error_mysql(e))

def obtener_metricas_dashboard(config=None):
    """
    Obtiene las métricas clave para el panel de control.
    """
    metricas = {
        "total_propietarios": 0,
        "total_mascotas": 0,
        "total_citas": 0,
        "citas_pendientes": 0,
        "total_consultas": 0,
        "horarios_disponibles": 0
    }
    try:
        conn = obtener_conexion(config=config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Usuario WHERE id_rol = 3")
        metricas["total_propietarios"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Mascotas")
        metricas["total_mascotas"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Cita")
        metricas["total_citas"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Cita WHERE estado_cita IN ('Programada', 'Confirmada')")
        metricas["citas_pendientes"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Historial_Medico")
        metricas["total_consultas"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Horario_Disponible WHERE estado_horario = 'Disponible' AND fecha >= CURDATE()")
        metricas["horarios_disponibles"] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
    except Exception:
        pass
    return metricas
