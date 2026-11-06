"""
==============================================================================
PRUEBAS UNITARIAS DE CAJA BLANCA CON PYTEST
Clínica Veterinaria "Amor Animal"
Archivo: test_app.py
==============================================================================
Este archivo implementa pruebas unitarias siguiendo los estándares de
pruebas de caja blanca (White-Box Testing), cobertura de caminos lógicos
y aislamiento de dependencias externas mediante técnicas de Mocking.
==============================================================================
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import mysql.connector
from mysql.connector import errorcode
import pandas as pd

# Importar funciones de la lógica del sistema y base de datos
from db import (
    obtener_conexion,
    probar_conexion,
    traducir_error_mysql,
    ejecutar_consulta,
    ejecutar_escritura,
    inicializar_base_datos,
    obtener_metricas_dashboard,
    CONFIG_DB_DEFAULT
)

# ==============================================================================
# 1. PRUEBAS DE CAJA BLANCA: CONEXIÓN A BASE DE DATOS (probar_conexion)
# ==============================================================================
class TestConexionBaseDatos:
    """
    Verifica la cobertura de caminos lógicos (Branch Coverage)
    en la función de conexión hacia MySQL en XAMPP.
    """

    @patch("db.obtener_conexion")
    def test_probar_conexion_exitosa(self, mock_obtener_conexion):
        """
        Camino 1: Conexión exitosa al servidor y base de datos.
        Debe retornar (True, mensaje_exito) y cerrar la conexión.
        """
        mock_conn = MagicMock()
        mock_obtener_conexion.return_value = mock_conn

        exito, mensaje = probar_conexion()

        assert exito is True
        assert "Conexión exitosa" in mensaje
        mock_obtener_conexion.assert_called_once_with(config=None, include_database=True)
        mock_conn.close.assert_called_once()

    @patch("db.obtener_conexion")
    def test_probar_conexion_error_base_no_creada(self, mock_obtener_conexion):
        """
        Camino 2: El servidor MySQL responde pero la base de datos 'clinica_amor_animal'
        aún no ha sido creada (Error ER_BAD_DB_ERROR).
        """
        error_mysql = mysql.connector.Error(errno=errorcode.ER_BAD_DB_ERROR, msg="Unknown database")
        mock_obtener_conexion.side_effect = error_mysql

        exito, mensaje = probar_conexion()

        assert exito is False
        assert "aún no ha sido creada" in mensaje

    @patch("db.obtener_conexion")
    def test_probar_conexion_error_servidor_apagado(self, mock_obtener_conexion):
        """
        Camino 3: El servicio MySQL en XAMPP está apagado (Error 2003 Connection Refused).
        """
        error_mysql = mysql.connector.Error(errno=2003, msg="Can't connect to MySQL server")
        mock_obtener_conexion.side_effect = error_mysql

        exito, mensaje = probar_conexion()

        assert exito is False
        assert "Verifica que el módulo 'MySQL' esté en 'Running'" in mensaje

    @patch("db.obtener_conexion")
    def test_probar_conexion_error_credenciales(self, mock_obtener_conexion):
        """
        Camino 4: Credenciales erróneas (Error ER_ACCESS_DENIED_ERROR).
        """
        error_mysql = mysql.connector.Error(errno=errorcode.ER_ACCESS_DENIED_ERROR, msg="Access denied")
        mock_obtener_conexion.side_effect = error_mysql

        exito, mensaje = probar_conexion()

        assert exito is False
        assert "Usuario o contraseña de MySQL incorrectos" in mensaje


# ==============================================================================
# 2. PRUEBAS DE CAJA BLANCA: TRADUCTOR DE ERRORES MYSQL (traducir_error_mysql)
# ==============================================================================
class TestTraductorErroresMySQL:
    """
    Evalúa la cobertura exhaustiva de todas las ramas de control condicional
    para el manejo de excepciones de integridad referencial.
    """

    def test_error_1062_duplicidad(self):
        """Rama 1: Código 1062 - Violación de restricción UNIQUE (ej. correo duplicado)"""
        err = mysql.connector.Error(errno=1062, msg="Duplicate entry")
        msg = traducir_error_mysql(err)
        assert "El registro ya existe" in msg
        assert "correo electrónico duplicado" in msg

    def test_error_1451_restriccion_eliminar_foranea(self):
        """Rama 2: Código 1451 - Intento de eliminar registro padre con hijos vinculados"""
        err = mysql.connector.Error(errno=1451, msg="Cannot delete or update a parent row")
        msg = traducir_error_mysql(err)
        assert "No se puede eliminar o modificar este registro" in msg
        assert "Integridad Referencial" in msg

    def test_error_1452_llave_foranea_inexistente(self):
        """Rama 3: Código 1452 - Llave foránea inexistente al insertar (ej. dueño no registrado)"""
        err = mysql.connector.Error(errno=1452, msg="Cannot add or update a child row")
        msg = traducir_error_mysql(err)
        assert "Error de Llave Foránea" in msg
        assert "no existe en la base de datos" in msg

    def test_error_2003_sin_conexion(self):
        """Rama 4: Código 2003 - Conexión rechazada con MySQL"""
        err = mysql.connector.Error(errno=2003, msg="Can't connect")
        msg = traducir_error_mysql(err)
        assert "No se puede establecer conexión con el servidor MySQL" in msg

    def test_error_mysql_generico(self):
        """Rama 5: Error de MySQL no mapeado específicamente"""
        err = mysql.connector.Error(errno=1045, msg="Custom error")
        msg = traducir_error_mysql(err)
        assert "Error de MySQL [1045]" in msg

    def test_excepcion_estandar_python(self):
        """Rama 6: Excepción que no hereda de mysql.connector.Error"""
        err = ValueError("Error de prueba en argumento")
        msg = traducir_error_mysql(err)
        assert msg == "Error de prueba en argumento"


# ==============================================================================
# 3. PRUEBAS DE CAJA BLANCA: FUNCIÓN PRINCIPAL TRANSACCIONAL (ejecutar_escritura)
# ==============================================================================
class TestEjecutarEscritura:
    """
    Pruebas unitarias de caja blanca para operaciones de inserción,
    actualización y borrado con manejo transaccional (commit/rollback).
    """

    @patch("db.obtener_conexion")
    def test_escritura_exitosa_retorna_last_id(self, mock_obtener_conexion):
        """
        Camino 1: Inserción exitosa de datos con retorno de ID autoincremental
        (como registrar un nuevo Paciente o Propietario).
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 15
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_obtener_conexion.return_value = mock_conn

        query = "INSERT INTO Mascotas (nombre_mascota, especie, id_usuario) VALUES (%s, %s, %s)"
        params = ("Rocky", "Perro", 3)

        resultado_id = ejecutar_escritura(query, params, return_last_id=True)

        assert resultado_id == 15
        mock_cursor.execute.assert_called_once_with(query, params)
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("db.obtener_conexion")
    def test_escritura_exitosa_retorna_rowcount(self, mock_obtener_conexion):
        """
        Camino 2: Actualización exitosa con retorno de filas afectadas
        (como actualizar estado de Cita a 'Atendida' o 'Cancelada').
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_conn.cursor.return_value = mock_cursor
        mock_obtener_conexion.return_value = mock_conn

        query = "UPDATE Cita SET estado_cita = %s WHERE id_cita = %s"
        params = ("Atendida", 1)

        filas_afectadas = ejecutar_escritura(query, params, return_last_id=False)

        assert filas_afectadas == 2
        mock_conn.commit.assert_called_once()

    @patch("db.obtener_conexion")
    def test_escritura_falla_ejecuta_rollback(self, mock_obtener_conexion):
        """
        Camino 3: Ante cualquier fallo en la sentencia SQL, el sistema DEBE
        garantizar la atomicidad ejecutando rollback() para proteger la base de datos.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        error_db = mysql.connector.Error(errno=1452, msg="Foreign key constraint fails")
        mock_cursor.execute.side_effect = error_db
        mock_conn.cursor.return_value = mock_cursor
        mock_obtener_conexion.return_value = mock_conn

        query = "INSERT INTO Cita (id_mascota, id_horario, id_servicio) VALUES (%s, %s, %s)"
        params = (999, 1, 1)  # ID Mascota inexistente

        with pytest.raises(RuntimeError) as exc_info:
            ejecutar_escritura(query, params)

        # Verificar que se aplicó Rollback
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()
        assert "Error de Llave Foránea" in str(exc_info.value)


# ==============================================================================
# 4. PRUEBAS DE CAJA BLANCA: FUNCIÓN PRINCIPAL DE CONSULTA (ejecutar_consulta)
# ==============================================================================
class TestEjecutarConsulta:
    """
    Pruebas para consultas SELECT multitabla y lectura relacional de datos.
    """

    @patch("db.pd.read_sql")
    @patch("db.obtener_conexion")
    def test_consulta_exitosa_retorna_dataframe(self, mock_obtener_conexion, mock_read_sql):
        """
        Verifica que se ejecute la consulta SELECT y retorne un DataFrame válido,
        cerrando la conexión tras la lectura.
        """
        mock_conn = MagicMock()
        mock_obtener_conexion.return_value = mock_conn

        df_simulado = pd.DataFrame({
            "id_mascota": [1, 2],
            "nombre_mascota": ["Max", "Luna"],
            "especie": ["Perro", "Gato"]
        })
        mock_read_sql.return_value = df_simulado

        query = "SELECT id_mascota, nombre_mascota, especie FROM Mascotas"
        resultado_df = ejecutar_consulta(query)

        assert isinstance(resultado_df, pd.DataFrame)
        assert len(resultado_df) == 2
        assert "Max" in resultado_df["nombre_mascota"].values
        mock_conn.close.assert_called_once()

    @patch("db.pd.read_sql")
    @patch("db.obtener_conexion")
    def test_consulta_falla_lanza_runtime_error(self, mock_obtener_conexion, mock_read_sql):
        """
        Verifica que errores durante el SELECT sean interceptados y traducidos correctamente.
        """
        mock_conn = MagicMock()
        mock_obtener_conexion.return_value = mock_conn
        mock_read_sql.side_effect = mysql.connector.Error(errno=1054, msg="Unknown column")

        with pytest.raises(RuntimeError) as exc_info:
            ejecutar_consulta("SELECT columna_inexistente FROM Mascotas")

        assert "Error de MySQL [1054]" in str(exc_info.value)


# ==============================================================================
# 5. PRUEBAS DE MÉTRICAS DEL DASHBOARD (obtener_metricas_dashboard)
# ==============================================================================
class TestMetricasDashboard:
    """
    Verifica que la función recolectora de métricas procese adecuadamente
    las consultas de resumen del sistema.
    """

    @patch("db.obtener_conexion")
    def test_obtener_metricas_calculo_correcto(self, mock_obtener_conexion):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Simular respuestas secuenciales de los SELECT COUNT(*)
        # 1. Propietarios, 2. Mascotas, 3. Citas totales, 4. Citas pendientes, 5. Consultas, 6. Horarios
        mock_cursor.fetchone.side_effect = [(5,), (8,), (12,), (3,), (10,), (7,)]
        mock_conn.cursor.return_value = mock_cursor
        mock_obtener_conexion.return_value = mock_conn

        metricas = obtener_metricas_dashboard()

        assert metricas["total_propietarios"] == 5
        assert metricas["total_mascotas"] == 8
        assert metricas["total_citas"] == 12
        assert metricas["citas_pendientes"] == 3
        assert metricas["total_consultas"] == 10
        assert metricas["horarios_disponibles"] == 7
        mock_conn.close.assert_called_once()


# ==============================================================================
# 6. PRUEBA DE INTEGRACIÓN: VERIFICACIÓN CON BASE DE DATOS REAL (OPCIONAL)
# ==============================================================================
def test_integracion_conexion_real_si_mysql_activo():
    """
    Prueba de verificación real: Si MySQL en XAMPP está encendido localmente,
    comprueba que la base de datos 'clinica_amor_animal' responda correctamente.
    Si está apagado, la prueba se omite limpiamente (skip) sin fallar el test suite.
    """
    conectado, _ = probar_conexion()
    if not conectado:
        pytest.skip("MySQL (XAMPP) no está activo en este momento. Omitiendo prueba de integración real.")

    # Si está activo, verificar que las 7 tablas existan
    df_tablas = ejecutar_consulta("SHOW TABLES")
    assert not df_tablas.empty
    tablas_existentes = [t.lower() for t in df_tablas.iloc[:, 0].tolist()]
    
    assert "rol" in tablas_existentes
    assert "usuario" in tablas_existentes
    assert "mascotas" in tablas_existentes
    assert "servicio" in tablas_existentes
    assert "horario_disponible" in tablas_existentes
    assert "cita" in tablas_existentes
    assert "historial_medico" in tablas_existentes
