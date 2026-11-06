"""
==============================================================================
Clínica Veterinaria "Amor Animal"
Backend API & Servidor Web con FastAPI y MySQL (XAMPP)
==============================================================================
"""

import os
from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn

from db import (
    CONFIG_DB_DEFAULT,
    probar_conexion,
    inicializar_base_datos,
    ejecutar_consulta,
    ejecutar_escritura,
    obtener_metricas_dashboard,
    traducir_error_mysql
)

app = FastAPI(
    title="Clínica Veterinaria Amor Animal API",
    description="Backend profesional y API REST conectada a MySQL en XAMPP",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# MODELOS PYDANTIC PARA VALIDACIÓN DE ENTRADAS
# ------------------------------------------------------------------------------
class UsuarioCreate(BaseModel):
    nombre: str
    telefono: str
    correo: str
    contrasena: str
    id_rol: int = 3  # Por defecto Propietario

class MascotaCreate(BaseModel):
    nombre_mascota: str
    especie: str
    raza: Optional[str] = "No especificada"
    edad_aprox: Optional[int] = 0
    peso: Optional[float] = 0.0
    id_usuario: int

class ServicioCreate(BaseModel):
    nombre_servicio: str
    descripcion: Optional[str] = ""
    costo: float

class HorarioCreate(BaseModel):
    fecha: str
    hora_inicio: str
    estado_horario: str = "Disponible"

class CitaCreate(BaseModel):
    id_mascota: int
    id_horario: int
    id_servicio: int
    estado_cita: str = "Programada"

class CitaEstadoUpdate(BaseModel):
    nuevo_estado: str

class HistorialCreate(BaseModel):
    id_cita: int
    peso_actual: float
    temperatura: float
    sintomas: str
    diagnostico: str
    tratamiento: str

# ------------------------------------------------------------------------------
# RUTAS DE API REST
# ------------------------------------------------------------------------------

@app.get("/api/status")
def get_system_status():
    """Retorna estado de conexión y métricas clave del sistema"""
    ok, msg = probar_conexion()
    metricas = obtener_metricas_dashboard() if ok else {}
    return {
        "conectado": ok,
        "mensaje": msg,
        "metricas": metricas
    }

@app.post("/api/init-db")
def post_init_database():
    """Inicializa la base de datos, tablas y datos semilla de prueba"""
    ok, msg = inicializar_base_datos()
    if not ok:
        raise HTTPException(status_code=500, detail=msg)
    return {"status": "ok", "message": msg}

# --- ROLES Y USUARIOS ---
@app.get("/api/roles")
def get_roles():
    """Obtiene los roles disponibles"""
    try:
        df = ejecutar_consulta("SELECT id_rol, nombre_rol FROM Rol ORDER BY id_rol ASC")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/usuarios")
def get_usuarios(rol_id: Optional[int] = None, search: Optional[str] = None):
    """Directorio de usuarios con filtros opcionales"""
    try:
        query = """
            SELECT 
                u.id_usuario, 
                u.nombre, 
                u.telefono, 
                u.correo, 
                u.id_rol,
                r.nombre_rol,
                (SELECT COUNT(*) FROM Mascotas m WHERE m.id_usuario = u.id_usuario) AS total_mascotas
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            WHERE 1=1
        """
        params = []
        if rol_id:
            query += " AND u.id_rol = %s"
            params.append(rol_id)
        if search:
            query += " AND (u.nombre LIKE %s OR u.correo LIKE %s OR u.telefono LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
            
        query += " ORDER BY u.id_usuario DESC"
        df = ejecutar_consulta(query, params=params if params else None)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/usuarios", status_code=status.HTTP_201_CREATED)
def create_usuario(usuario: UsuarioCreate):
    """Registra un nuevo usuario asegurando la integridad referencial con Rol"""
    try:
        query = "INSERT INTO Usuario (nombre, telefono, correo, contrasena, id_rol) VALUES (%s, %s, %s, %s, %s)"
        new_id = ejecutar_escritura(
            query, 
            (usuario.nombre.strip(), usuario.telefono.strip(), usuario.correo.strip(), usuario.contrasena, usuario.id_rol),
            return_last_id=True
        )
        return {"status": "ok", "id_usuario": new_id, "message": f"Usuario '{usuario.nombre}' registrado con éxito."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- PACIENTES (MASCOTAS) ---
@app.get("/api/mascotas")
def get_mascotas(especie: Optional[str] = None, search: Optional[str] = None):
    """Lista todos los pacientes vinculados con su propietario"""
    try:
        query = """
            SELECT 
                m.id_mascota,
                m.nombre_mascota,
                m.especie,
                m.raza,
                m.edad_aprox,
                m.peso,
                m.id_usuario,
                u.nombre AS nombre_propietario,
                u.telefono AS tel_propietario,
                u.correo AS correo_propietario,
                (SELECT COUNT(*) FROM Cita c WHERE c.id_mascota = m.id_mascota) AS total_citas
            FROM Mascotas m
            JOIN Usuario u ON m.id_usuario = u.id_usuario
            WHERE 1=1
        """
        params = []
        if especie and especie != "Todas":
            query += " AND m.especie = %s"
            params.append(especie)
        if search:
            query += " AND (m.nombre_mascota LIKE %s OR u.nombre LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
            
        query += " ORDER BY m.id_mascota DESC"
        df = ejecutar_consulta(query, params=params if params else None)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mascotas", status_code=status.HTTP_201_CREATED)
def create_mascota(mascota: MascotaCreate):
    """Registra una mascota vinculándola con un propietario existente"""
    try:
        query = """
            INSERT INTO Mascotas (nombre_mascota, especie, raza, edad_aprox, peso, id_usuario)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        new_id = ejecutar_escritura(
            query,
            (mascota.nombre_mascota.strip(), mascota.especie, mascota.raza.strip(), mascota.edad_aprox, mascota.peso, mascota.id_usuario),
            return_last_id=True
        )
        return {"status": "ok", "id_mascota": new_id, "message": f"Mascota '{mascota.nombre_mascota}' registrada con éxito."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- SERVICIOS ---
@app.get("/api/servicios")
def get_servicios():
    """Catálogo de servicios disponibles"""
    try:
        df = ejecutar_consulta("SELECT id_servicio, nombre_servicio, descripcion, costo FROM Servicio ORDER BY id_servicio ASC")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/servicios", status_code=status.HTTP_201_CREATED)
def create_servicio(servicio: ServicioCreate):
    """Crea un nuevo servicio en el catálogo"""
    try:
        query = "INSERT INTO Servicio (nombre_servicio, descripcion, costo) VALUES (%s, %s, %s)"
        new_id = ejecutar_escritura(query, (servicio.nombre_servicio.strip(), servicio.descripcion.strip(), servicio.costo), return_last_id=True)
        return {"status": "ok", "id_servicio": new_id, "message": f"Servicio '{servicio.nombre_servicio}' registrado con éxito."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- HORARIOS ---
@app.get("/api/horarios")
def get_horarios(solo_disponibles: bool = False):
    """Lista de horarios disponibles o todos"""
    try:
        query = "SELECT id_horario, fecha, TIME_FORMAT(hora_inicio, '%H:%i') AS hora_inicio, estado_horario FROM Horario_Disponible"
        if solo_disponibles:
            query += " WHERE estado_horario = 'Disponible' AND fecha >= CURDATE()"
        query += " ORDER BY fecha ASC, hora_inicio ASC"
        df = ejecutar_consulta(query)
        # Convertir fecha a string
        if not df.empty and "fecha" in df.columns:
            df["fecha"] = df["fecha"].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/horarios", status_code=status.HTTP_201_CREATED)
def create_horario(horario: HorarioCreate):
    """Abre un nuevo horario de atención"""
    try:
        query = "INSERT INTO Horario_Disponible (fecha, hora_inicio, estado_horario) VALUES (%s, %s, %s)"
        new_id = ejecutar_escritura(query, (horario.fecha, horario.hora_inicio, horario.estado_horario), return_last_id=True)
        return {"status": "ok", "id_horario": new_id, "message": "Horario registrado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- CITAS ---
@app.get("/api/citas")
def get_citas(estado: Optional[str] = None):
    """Listado completo de citas con JOIN a Mascotas, Propietario, Servicio y Horario"""
    try:
        query = """
            SELECT 
                c.id_cita,
                c.id_mascota,
                c.id_horario,
                c.id_servicio,
                c.estado_cita,
                m.nombre_mascota,
                m.especie,
                m.peso AS peso_mascota,
                u.nombre AS nombre_propietario,
                u.telefono AS tel_propietario,
                u.correo AS correo_propietario,
                s.nombre_servicio,
                s.costo,
                hd.fecha,
                TIME_FORMAT(hd.hora_inicio, '%H:%i') AS hora_inicio
            FROM Cita c
            JOIN Mascotas m ON c.id_mascota = m.id_mascota
            JOIN Usuario u ON m.id_usuario = u.id_usuario
            JOIN Servicio s ON c.id_servicio = s.id_servicio
            JOIN Horario_Disponible hd ON c.id_horario = hd.id_horario
            WHERE 1=1
        """
        params = []
        if estado and estado != "Todas":
            query += " AND c.estado_cita = %s"
            params.append(estado)
            
        query += " ORDER BY hd.fecha DESC, hd.hora_inicio DESC"
        df = ejecutar_consulta(query, params=params if params else None)
        if not df.empty and "fecha" in df.columns:
            df["fecha"] = df["fecha"].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/citas", status_code=status.HTTP_201_CREATED)
def create_cita(cita: CitaCreate):
    """Agenda una cita bloqueando el turno a Ocupado de forma transaccional"""
    try:
        query_ins = "INSERT INTO Cita (id_mascota, id_horario, id_servicio, estado_cita) VALUES (%s, %s, %s, %s)"
        new_id = ejecutar_escritura(
            query_ins,
            (cita.id_mascota, cita.id_horario, cita.id_servicio, cita.estado_cita),
            return_last_id=True
        )
        # Marcar horario como ocupado
        ejecutar_escritura("UPDATE Horario_Disponible SET estado_horario = 'Ocupado' WHERE id_horario = %s", (cita.id_horario,))
        return {"status": "ok", "id_cita": new_id, "message": "Cita programada con éxito y horario reservado."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/citas/{id_cita}/estado")
def update_estado_cita(id_cita: int, body: CitaEstadoUpdate):
    """Actualiza el estado de una cita y libera el horario si es cancelada"""
    try:
        nuevo = body.nuevo_estado
        ejecutar_escritura("UPDATE Cita SET estado_cita = %s WHERE id_cita = %s", (nuevo, id_cita))
        if nuevo == "Cancelada":
            # Liberar el horario asignado
            ejecutar_escritura(
                "UPDATE Horario_Disponible SET estado_horario = 'Disponible' WHERE id_horario = (SELECT id_horario FROM Cita WHERE id_cita = %s)",
                (id_cita,)
            )
        return {"status": "ok", "message": f"Cita #{id_cita} actualizada a '{nuevo}'."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- HISTORIAL MÉDICO ---
@app.get("/api/historial/{id_mascota}")
def get_historial_por_mascota(id_mascota: int):
    """Obtiene el historial clínico completo de una mascota ordenado cronológicamente"""
    try:
        query = """
            SELECT 
                h.id_historial,
                h.id_cita,
                h.peso_actual,
                h.temperatura,
                h.sintomas,
                h.diagnostico,
                h.tratamiento,
                c.estado_cita,
                s.nombre_servicio,
                hd.fecha,
                TIME_FORMAT(hd.hora_inicio, '%H:%i') AS hora_inicio,
                m.nombre_mascota,
                m.especie,
                u.nombre AS dueno,
                u.telefono AS tel_dueno
            FROM Historial_Medico h
            JOIN Cita c ON h.id_cita = c.id_cita
            JOIN Mascotas m ON c.id_mascota = m.id_mascota
            JOIN Usuario u ON m.id_usuario = u.id_usuario
            JOIN Horario_Disponible hd ON c.id_horario = hd.id_horario
            JOIN Servicio s ON c.id_servicio = s.id_servicio
            WHERE m.id_mascota = %s
            ORDER BY hd.fecha DESC, hd.hora_inicio DESC
        """
        df = ejecutar_consulta(query, params=[id_mascota])
        if not df.empty and "fecha" in df.columns:
            df["fecha"] = df["fecha"].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/historial", status_code=status.HTTP_201_CREATED)
def create_historial(hist: HistorialCreate):
    """Registra una consulta en Historial_Medico, marca la Cita como 'Atendida' y actualiza el peso del paciente"""
    try:
        query_ins = """
            INSERT INTO Historial_Medico (id_cita, peso_actual, temperatura, sintomas, diagnostico, tratamiento)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        new_id = ejecutar_escritura(
            query_ins,
            (hist.id_cita, hist.peso_actual, hist.temperatura, hist.sintomas.strip(), hist.diagnostico.strip(), hist.tratamiento.strip()),
            return_last_id=True
        )
        # 1. Marcar cita como 'Atendida'
        ejecutar_escritura("UPDATE Cita SET estado_cita = 'Atendida' WHERE id_cita = %s", (hist.id_cita,))
        # 2. Actualizar el peso del paciente en Mascotas
        ejecutar_escritura(
            "UPDATE Mascotas SET peso = %s WHERE id_mascota = (SELECT id_mascota FROM Cita WHERE id_cita = %s)",
            (hist.peso_actual, hist.id_cita)
        )
        return {"status": "ok", "id_historial": new_id, "message": "Consulta médica registrada con éxito."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- REPORTE MAESTRO JOIN ---
@app.get("/api/reportes/master")
def get_reporte_master():
    """Reporte multitabla consolidado para exportación o visualización"""
    try:
        query = """
            SELECT 
                m.id_mascota AS id_paciente,
                m.nombre_mascota AS mascota,
                m.especie,
                m.raza,
                m.peso,
                u.nombre AS propietario,
                u.telefono,
                u.correo,
                COUNT(c.id_cita) AS total_citas
            FROM Mascotas m
            JOIN Usuario u ON m.id_usuario = u.id_usuario
            LEFT JOIN Cita c ON m.id_mascota = c.id_mascota
            GROUP BY m.id_mascota, m.nombre_mascota, m.especie, m.raza, m.peso, u.nombre, u.telefono, u.correo
            ORDER BY m.id_mascota ASC
        """
        df = ejecutar_consulta(query)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# SERVIR EL FRONTEND WEB
# ------------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def get_frontend():
    """Sirve la interfaz gráfica web principal"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend no encontrado en /static/index.html</h1>"

if __name__ == "__main__":
    print("Iniciando Servidor Web Clínica Veterinaria Amor Animal en http://localhost:8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
