"""
==============================================================================
Clínica Veterinaria "Amor Animal"
Sistema de Gestión Integral (Streamlit + MySQL en XAMPP)
==============================================================================
"""

import streamlit as st
import pandas as pd
import mysql.connector
from datetime import date, datetime, time, timedelta
import altair as alt

from db import (
    CONFIG_DB_DEFAULT,
    obtener_conexion,
    probar_conexion,
    inicializar_base_datos,
    ejecutar_consulta,
    ejecutar_escritura,
    obtener_metricas_dashboard,
    traducir_error_mysql
)

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Amor Animal · Sistema Veterinario",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #0284c7 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.1rem;
        font-weight: 700;
    }
    .main-header p {
        color: #e0f2fe;
        margin: 0.3rem 0 0 0;
        font-size: 1.05rem;
    }
    .metric-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 10px 18px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. BARRA LATERAL (SIDEBAR) & CONTROL DE CONEXIÓN
# ------------------------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1548767797-d8c844163c4c?w=300&auto=format&fit=crop&q=80", use_container_width=True)
    st.title("🐾 Amor Animal")
    st.caption("Sistema de Gestión Clínica Veterinaria")
    st.markdown("---")
    
    st.subheader("⚙️ Conexión MySQL (XAMPP)")
    
    with st.expander("Parámetros de Servidor", expanded=False):
        db_host = st.text_input("Host", value=CONFIG_DB_DEFAULT["host"])
        db_user = st.text_input("Usuario", value=CONFIG_DB_DEFAULT["user"])
        db_pass = st.text_input("Contraseña", value=CONFIG_DB_DEFAULT["password"], type="password")
        db_name = st.text_input("Base de Datos", value=CONFIG_DB_DEFAULT["database"])
        db_port = st.number_input("Puerto", value=CONFIG_DB_DEFAULT["port"], step=1)
        
    cfg_activa = {
        "host": db_host,
        "user": db_user,
        "password": db_pass,
        "database": db_name,
        "port": int(db_port)
    }
    
    conectado, mensaje_conexion = probar_conexion(cfg_activa)
    
    if conectado:
        st.success("🟢 **MySQL Conectado**\n\nBase: `clinica_amor_animal`")
    else:
        st.error(f"🔴 **Sin Conexión**\n\n{mensaje_conexion}")
        st.info("💡 **Tip**: Abre el Panel de XAMPP y presiona **Start** en el servicio **MySQL**.")
        
    st.markdown("---")
    
    st.subheader("🛠️ Inicialización de BD")
    st.caption("Crea la estructura relacional con llaves foráneas y datos iniciales de prueba.")
    if st.button("⚡ Inicializar / Verificar Base de Datos", use_container_width=True):
        with st.spinner("Inicializando base de datos y verificando tablas..."):
            ok, msg = inicializar_base_datos(cfg_activa)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
                
    st.markdown("---")
    st.markdown("👨‍⚕️ **Clínica Veterinaria Amor Animal**\n\n*Gestión Relacional MySQL · 2026*")

# ------------------------------------------------------------------------------
# 3. ENCABEZADO PRINCIPAL
# ------------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🐾 Clínica Veterinaria "Amor Animal"</h1>
    <p>Control Integral de Propietarios, Pacientes, Citas, Servicios y Expedientes Médicos</p>
</div>
""", unsafe_allow_html=True)

if not conectado:
    st.warning("⚠️ **Atención:** No hay conexión activa con la base de datos MySQL en XAMPP.")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown("""
        ### Pasos para iniciar el sistema:
        1. Abre el **Panel de Control de XAMPP**.
        2. Presiona el botón **Start** en el servicio **MySQL** (puerto 3306).
        3. Haz clic en la barra lateral en **'⚡ Inicializar / Verificar Base de Datos'**.
        """)
    with col_b:
        if st.button("🔄 Reintentar Conexión Ahora", type="primary", use_container_width=True):
            st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 4. PESTAÑAS PRINCIPALES DEL SISTEMA
# ------------------------------------------------------------------------------
pestana_dash, pestana_prop, pestana_masc, pestana_citas, pestana_med, pestana_serv, pestana_diag = st.tabs([
    "📊 Panel General",
    "👥 Propietarios y Roles", 
    "🐶 Gestión de Pacientes", 
    "📅 Citas y Horarios", 
    "🩺 Médico & Historial Clínico",
    "📋 Catálogo y Listados (JOIN)",
    "⚙️ Diagnóstico DB"
])

# ==============================================================================
# PESTAÑA 0: DASHBOARD Y MÉTRICAS
# ==============================================================================
with pestana_dash:
    st.subheader("📈 Resumen Operativo de la Clínica")
    metricas = obtener_metricas_dashboard(cfg_activa)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("👥 Propietarios", metricas["total_propietarios"], help="Clientes registrados con rol Propietario")
    with col2:
        st.metric("🐶 Pacientes", metricas["total_mascotas"], help="Mascotas registradas en el sistema")
    with col3:
        st.metric("📅 Citas Activas", metricas["citas_pendientes"], help="Citas con estado Programada o Confirmada")
    with col4:
        st.metric("🩺 Consultas Médicas", metricas["total_consultas"], help="Historiales médicos y atenciones registradas")
    with col5:
        st.metric("⏰ Horarios Libres", metricas["horarios_disponibles"], help="Horarios disponibles para agendar citas")
        
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("##### 🐾 Pacientes Registrados por Especie")
        try:
            df_especies = ejecutar_consulta(
                "SELECT especie, COUNT(*) as cantidad FROM Mascotas GROUP BY especie ORDER BY cantidad DESC",
                config=cfg_activa
            )
            if not df_especies.empty:
                chart_especies = alt.Chart(df_especies).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X('especie:N', title='Especie', sort='-y'),
                    y=alt.Y('cantidad:Q', title='Número de Pacientes'),
                    color=alt.Color('especie:N', legend=None, scale=alt.Scale(scheme='tableau10')),
                    tooltip=['especie', 'cantidad']
                ).properties(height=260)
                st.altair_chart(chart_especies, use_container_width=True)
            else:
                st.info("No hay mascotas registradas para graficar.")
        except Exception as e:
            st.error(f"Error al generar gráfica: {e}")
            
    with col_chart2:
        st.markdown("##### 📌 Distribución de Citas por Estado")
        try:
            df_estados = ejecutar_consulta(
                "SELECT estado_cita, COUNT(*) as cantidad FROM Cita GROUP BY estado_cita",
                config=cfg_activa
            )
            if not df_estados.empty:
                chart_estados = alt.Chart(df_estados).mark_arc(innerRadius=45).encode(
                    theta=alt.Theta(field="cantidad", type="quantitative"),
                    color=alt.Color(field="estado_cita", type="nominal", title="Estado"),
                    tooltip=['estado_cita', 'cantidad']
                ).properties(height=260)
                st.altair_chart(chart_estados, use_container_width=True)
            else:
                st.info("No hay citas registradas para graficar.")
        except Exception as e:
            st.error(f"Error al generar gráfica: {e}")

    st.markdown("##### 🕒 Próximas Citas Agendadas")
    try:
        query_prox = """
            SELECT 
                c.id_cita AS 'ID Cita',
                h.fecha AS 'Fecha',
                TIME_FORMAT(h.hora_inicio, '%H:%i') AS 'Hora',
                m.nombre_mascota AS 'Paciente',
                m.especie AS 'Especie',
                u.nombre AS 'Propietario',
                s.nombre_servicio AS 'Servicio',
                c.estado_cita AS 'Estado'
            FROM Cita c
            JOIN Mascotas m ON c.id_mascota = m.id_mascota
            JOIN Usuario u ON m.id_usuario = u.id_usuario
            JOIN Horario_Disponible h ON c.id_horario = h.id_horario
            JOIN Servicio s ON c.id_servicio = s.id_servicio
            ORDER BY h.fecha ASC, h.hora_inicio ASC
            LIMIT 5
        """
        df_prox = ejecutar_consulta(query_prox, config=cfg_activa)
        if not df_prox.empty:
            st.dataframe(df_prox, use_container_width=True)
        else:
            st.info("No hay citas próximas programadas.")
    except Exception as e:
        st.error(f"Error al cargar citas próximas: {e}")

# ==============================================================================
# PESTAÑA 1: PROPIETARIOS Y ROLES
# ==============================================================================
with pestana_prop:
    sub1, sub2, sub3 = st.tabs(["📝 Registrar Nuevo Usuario / Propietario", "📋 Directorio de Usuarios", "🛡️ Catálogo de Roles"])
    
    with sub1:
        st.subheader("Registro de Nuevo Usuario / Propietario")
        st.caption("Crea una cuenta en el sistema vinculándola dinámicamente con la tabla `Rol` (Integridad Referencial).")
        
        # Cargar roles disponibles de la tabla Rol
        try:
            df_roles = ejecutar_consulta("SELECT id_rol, nombre_rol FROM Rol ORDER BY id_rol", config=cfg_activa)
            dict_roles = {f"{row['nombre_rol']} (ID: {row['id_rol']})": row['id_rol'] for _, row in df_roles.iterrows()}
            # Por defecto preseleccionar Propietario (id_rol = 3) si existe
            default_index = 2 if len(dict_roles) >= 3 else 0
        except Exception as e:
            st.error(f"Error al cargar roles: {e}")
            dict_roles = {}
            default_index = 0

        with st.form("form_nuevo_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre_u = st.text_input("Nombre Completo *", placeholder="Ej: Carlos Fuentes Hernández")
                telefono_u = st.text_input("Teléfono de Contacto *", placeholder="Ej: 555-0301")
            with col2:
                correo_u = st.text_input("Correo Electrónico (Único) *", placeholder="Ej: carlos.fuentes@correo.com")
                pass_u = st.text_input("Contraseña de Acceso *", type="password", value="cliente123")
                rol_seleccionado = st.selectbox(
                    "Rol asignado (Llave Foránea a Rol) *", 
                    options=list(dict_roles.keys()),
                    index=default_index,
                    help="Determina el rol del usuario (Propietario por defecto para dueños de mascotas)."
                )
                
            submitted_u = st.form_submit_button("💾 Guardar Usuario / Propietario", type="primary")
            
            if submitted_u:
                if nombre_u.strip() and telefono_u.strip() and correo_u.strip() and pass_u.strip():
                    id_rol_real = dict_roles[rol_seleccionado]
                    try:
                        query_insert_u = """
                            INSERT INTO Usuario (nombre, telefono, correo, contrasena, id_rol) 
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        ejecutar_escritura(
                            query_insert_u, 
                            (nombre_u.strip(), telefono_u.strip(), correo_u.strip(), pass_u, id_rol_real), 
                            config=cfg_activa
                        )
                        st.success(f"¡Usuario '{nombre_u}' registrado exitosamente con Rol ID {id_rol_real}!")
                    except Exception as err:
                        st.error(f"No se pudo guardar el usuario: {err}")
                else:
                    st.warning("⚠️ Por favor completa todos los campos obligatorios (*).")

    with sub2:
        st.subheader("Directorio de Usuarios Registrados")
        col_filtro1, col_filtro2 = st.columns([1, 2])
        with col_filtro1:
            filtro_rol = st.selectbox("Filtrar por Rol:", ["Todos"] + list(df_roles["nombre_rol"].unique()) if not df_roles.empty else ["Todos"])
        with col_filtro2:
            busqueda_u = st.text_input("Buscar por Nombre o Correo:", placeholder="Escribe para filtrar...")

        try:
            query_usuarios = """
                SELECT 
                    u.id_usuario AS 'ID',
                    u.nombre AS 'Nombre Completo',
                    u.telefono AS 'Teléfono',
                    u.correo AS 'Correo Electrónico',
                    r.nombre_rol AS 'Rol'
                FROM Usuario u
                JOIN Rol r ON u.id_rol = r.id_rol
                WHERE 1=1
            """
            params_u = []
            if filtro_rol != "Todos":
                query_usuarios += " AND r.nombre_rol = %s"
                params_u.append(filtro_rol)
            if busqueda_u.strip():
                query_usuarios += " AND (u.nombre LIKE %s OR u.correo LIKE %s)"
                params_u.extend([f"%{busqueda_u}%", f"%{busqueda_u}%"])
                
            query_usuarios += " ORDER BY u.id_usuario DESC"
            
            df_u_list = ejecutar_consulta(query_usuarios, params=params_u if params_u else None, config=cfg_activa)
            if not df_u_list.empty:
                st.dataframe(df_u_list, use_container_width=True)
                st.caption(f"Total: {len(df_u_list)} usuario(s) encontrado(s).")
            else:
                st.info("No se encontraron usuarios con los criterios indicados.")
        except Exception as e:
            st.error(f"Error al consultar usuarios: {e}")

    with sub3:
        st.subheader("Catálogo de Roles en el Sistema")
        try:
            df_r = ejecutar_consulta("SELECT id_rol AS 'ID Rol', nombre_rol AS 'Nombre del Rol' FROM Rol", config=cfg_activa)
            st.dataframe(df_r, use_container_width=True)
        except Exception as e:
            st.error(f"Error al consultar roles: {e}")

# ==============================================================================
# PESTAÑA 2: GESTIÓN DE PACIENTES (MASCOTAS)
# ==============================================================================
with pestana_masc:
    sub_m1, sub_m2, sub_m3 = st.tabs(["🐾 Registrar Paciente", "📋 Directorio de Pacientes", "🪪 Carnet Digital del Paciente"])
    
    with sub_m1:
        st.subheader("Registro de Paciente (Mascota)")
        st.caption("Asocia una mascota a su propietario correspondiente asegurando la integridad referencial.")
        
        # Cargar propietarios dinámicamente desde MySQL
        try:
            query_owners = """
                SELECT id_usuario, nombre, correo, telefono 
                FROM Usuario 
                ORDER BY nombre ASC
            """
            df_owners = ejecutar_consulta(query_owners, config=cfg_activa)
        except Exception:
            df_owners = pd.DataFrame()

        if not df_owners.empty:
            opciones_owners = {
                f"{row['nombre']} | 📧 {row['correo']} | 📞 {row['telefono']} (ID: {row['id_usuario']})": row['id_usuario'] 
                for _, row in df_owners.iterrows()
            }
            
            with st.form("form_nuevo_paciente", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nombre_m = st.text_input("Nombre de la Mascota *", placeholder="Ej: Max, Luna, Rocky")
                    especie_m = st.selectbox(
                        "Especie *", 
                        ["Perro", "Gato", "Ave", "Conejo", "Reptil", "Roedor", "Otro"]
                    )
                    raza_m = st.text_input("Raza (Ej. Labrador, Siamés)", placeholder="Ej: Golden Retriever, Criollo")
                with col2:
                    edad_m = st.number_input("Edad Aproximada (años)", min_value=0, max_value=35, value=2, step=1)
                    peso_m = st.number_input("Peso (kg)", min_value=0.01, max_value=250.0, value=5.0, format="%.2f")
                    dueno_sel = st.selectbox("Propietario Asociado (Llave Foránea a Usuario) *", options=list(opciones_owners.keys()))
                    
                submitted_m = st.form_submit_button("💾 Guardar Paciente en Base de Datos", type="primary")
                
                if submitted_m:
                    if nombre_m.strip():
                        id_dueno_real = opciones_owners[dueno_sel]
                        try:
                            query_insert_m = """
                                INSERT INTO Mascotas (nombre_mascota, especie, raza, edad_aprox, peso, id_usuario)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            nuevo_id = ejecutar_escritura(
                                query_insert_m, 
                                (nombre_m.strip(), especie_m, raza_m.strip(), edad_m, peso_m, id_dueno_real),
                                config=cfg_activa,
                                return_last_id=True
                            )
                            st.success(f"¡Paciente '{nombre_m}' registrado y vinculado con éxito! (ID Mascota: {nuevo_id})")
                        except Exception as err:
                            st.error(f"Error al registrar la mascota: {err}")
                    else:
                        st.warning("El nombre de la mascota no puede estar vacío.")
        else:
            st.warning("⚠️ Primero debes registrar al menos un Propietario en la pestaña 'Propietarios y Roles' para poder vincular pacientes.")

    with sub_m2:
        st.subheader("Directorio de Pacientes Registrados")
        col_fil1, col_fil2 = st.columns([1, 2])
        with col_fil1:
            especies_disponibles = ["Todas", "Perro", "Gato", "Ave", "Conejo", "Reptil", "Roedor", "Otro"]
            filtro_esp = st.selectbox("Filtrar por Especie:", especies_disponibles)
        with col_fil2:
            busqueda_m = st.text_input("Buscar por Nombre de Mascota o Propietario:", placeholder="Escribe el nombre...")

        try:
            query_pacientes = """
                SELECT 
                    m.id_mascota AS 'ID',
                    m.nombre_mascota AS 'Paciente',
                    m.especie AS 'Especie',
                    m.raza AS 'Raza',
                    m.edad_aprox AS 'Edad (años)',
                    m.peso AS 'Peso (kg)',
                    u.nombre AS 'Propietario',
                    u.telefono AS 'Tel. Propietario',
                    u.correo AS 'Correo Propietario'
                FROM Mascotas m
                JOIN Usuario u ON m.id_usuario = u.id_usuario
                WHERE 1=1
            """
            params_m = []
            if filtro_esp != "Todas":
                query_pacientes += " AND m.especie = %s"
                params_m.append(filtro_esp)
            if busqueda_m.strip():
                query_pacientes += " AND (m.nombre_mascota LIKE %s OR u.nombre LIKE %s)"
                params_m.extend([f"%{busqueda_m}%", f"%{busqueda_m}%"])
                
            query_pacientes += " ORDER BY m.id_mascota DESC"
            df_pacientes = ejecutar_consulta(query_pacientes, params=params_m if params_m else None, config=cfg_activa)
            if not df_pacientes.empty:
                st.dataframe(df_pacientes, use_container_width=True)
                st.caption(f"Total: {len(df_pacientes)} paciente(s) registrado(s).")
            else:
                st.info("No se encontraron pacientes que coincidan con la búsqueda.")
        except Exception as e:
            st.error(f"Error al listar pacientes: {e}")

    with sub_m3:
        st.subheader("🪪 Carnet Digital / Ficha del Paciente")
        try:
            df_pet_select = ejecutar_consulta(
                "SELECT m.id_mascota, m.nombre_mascota, m.especie, u.nombre AS owner FROM Mascotas m JOIN Usuario u ON m.id_usuario = u.id_usuario ORDER BY m.nombre_mascota", 
                config=cfg_activa
            )
            if not df_pet_select.empty:
                opciones_pet_carnet = {f"{row['nombre_mascota']} ({row['especie']}) - Dueño: {row['owner']} [ID: {row['id_mascota']}]": row['id_mascota'] for _, row in df_pet_select.iterrows()}
                pet_carnet_id = st.selectbox("Selecciona un Paciente para ver su expediente:", list(opciones_pet_carnet.keys()))
                id_seleccionado = opciones_pet_carnet[pet_carnet_id]
                
                query_ficha = """
                    SELECT 
                        m.id_mascota,
                        m.nombre_mascota,
                        m.especie,
                        m.raza,
                        m.edad_aprox,
                        m.peso,
                        u.nombre AS nombre_dueno, 
                        u.telefono AS tel_dueno, 
                        u.correo AS correo_dueno
                    FROM Mascotas m
                    JOIN Usuario u ON m.id_usuario = u.id_usuario
                    WHERE m.id_mascota = %s
                """
                df_ficha = ejecutar_consulta(query_ficha, params=[id_seleccionado], config=cfg_activa)
                
                if not df_ficha.empty:
                    ficha = df_ficha.iloc[0]
                    icono_especie = "🐶" if ficha["especie"] == "Perro" else "🐱" if ficha["especie"] == "Gato" else "🐰" if ficha["especie"] == "Conejo" else "🦜" if ficha["especie"] == "Ave" else "🐾"
                    
                    st.markdown(f"""
                    <div style="background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-top: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                            <h2 style="margin: 0; color: #1e3a8a;">{icono_especie} Expediente Digital: {ficha['nombre_mascota']}</h2>
                            <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold;">ID Paciente: #{ficha['id_mascota']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### 🐾 Datos Clínicos del Paciente")
                        st.write(f"**Especie:** {ficha['especie']}")
                        st.write(f"**Raza:** {ficha['raza'] or 'No especificada'}")
                        st.write(f"**Edad Estimada:** {ficha['edad_aprox']} años")
                        st.write(f"**Peso Registrado:** {ficha['peso']} kg")
                    with c2:
                        st.markdown("#### 👤 Datos del Propietario Responsable")
                        st.write(f"**Nombre:** {ficha['nombre_dueno']}")
                        st.write(f"**Teléfono:** 📞 {ficha['tel_dueno']}")
                        st.write(f"**Correo:** 📧 {ficha['correo_dueno']}")
            else:
                st.info("No hay pacientes registrados aún.")
        except Exception as e:
            st.error(f"Error al cargar carnet: {e}")

# ==============================================================================
# PESTAÑA 3: AGENDAMIENTO DE CITAS Y HORARIOS DISPONIBLES
# ==============================================================================
with pestana_citas:
    sub_c1, sub_c2, sub_c3 = st.tabs(["📅 Agendar Cita", "📋 Panel y Control de Citas", "⏰ Apertura de Horarios"])
    
    with sub_c1:
        st.subheader("Agendamiento de Nueva Cita")
        st.caption("Vincula un Paciente con un Horario Disponible y un Servicio, garantizando las restricciones foráneas.")
        
        try:
            # 1. Mascotas
            df_pets_c = ejecutar_consulta("""
                SELECT m.id_mascota, m.nombre_mascota, m.especie, u.nombre as owner 
                FROM Mascotas m 
                JOIN Usuario u ON m.id_usuario = u.id_usuario 
                ORDER BY m.nombre_mascota
            """, config=cfg_activa)
            
            # 2. Servicios
            df_serv_c = ejecutar_consulta("SELECT id_servicio, nombre_servicio, costo FROM Servicio ORDER BY nombre_servicio", config=cfg_activa)
            
            # 3. Horarios Disponibles (estado_horario = 'Disponible' y fecha >= hoy)
            df_horarios_c = ejecutar_consulta("""
                SELECT 
                    id_horario, 
                    fecha, 
                    hora_inicio, 
                    estado_horario
                FROM Horario_Disponible
                WHERE estado_horario = 'Disponible' AND fecha >= CURDATE()
                ORDER BY fecha ASC, hora_inicio ASC
            """, config=cfg_activa)
        except Exception as e:
            st.error(f"Error al cargar datos para citas: {e}")
            df_pets_c = pd.DataFrame()
            df_serv_c = pd.DataFrame()
            df_horarios_c = pd.DataFrame()

        if not df_pets_c.empty and not df_serv_c.empty and not df_horarios_c.empty:
            opc_pets = {f"{r['nombre_mascota']} ({r['especie']}) · Dueño: {r['owner']} (ID: {r['id_mascota']})": r['id_mascota'] for _, r in df_pets_c.iterrows()}
            opc_serv = {f"{r['nombre_servicio']} — ${r['costo']:.2f}": r['id_servicio'] for _, r in df_serv_c.iterrows()}
            opc_horarios = {
                f"📅 {r['fecha']} | ⏰ {r['hora_inicio']} [Turno #{r['id_horario']}]": r['id_horario'] 
                for _, r in df_horarios_c.iterrows()
            }
            
            with st.form("form_agendar_cita", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    pet_sel = st.selectbox("1. Seleccionar Paciente (Mascota) *", options=list(opc_pets.keys()))
                    serv_sel = st.selectbox("2. Seleccionar Servicio Clínico *", options=list(opc_serv.keys()))
                with col2:
                    horario_sel = st.selectbox("3. Seleccionar Turno / Horario Disponible *", options=list(opc_horarios.keys()))
                    estado_inicial = st.selectbox("4. Estado Inicial de la Cita", ["Programada", "Confirmada"])
                    
                submitted_cita = st.form_submit_button("✅ Confirmar y Agendar Cita", type="primary")
                
                if submitted_cita:
                    id_pet_real = opc_pets[pet_sel]
                    id_serv_real = opc_serv[serv_sel]
                    id_horario_real = opc_horarios[horario_sel]
                    
                    try:
                        # 1. Insertar Cita en la base de datos
                        query_ins_cita = """
                            INSERT INTO Cita (id_mascota, id_horario, id_servicio, estado_cita)
                            VALUES (%s, %s, %s, %s)
                        """
                        id_nueva_cita = ejecutar_escritura(
                            query_ins_cita, 
                            (id_pet_real, id_horario_real, id_serv_real, estado_inicial),
                            config=cfg_activa,
                            return_last_id=True
                        )
                        
                        # 2. Actualizar Horario a 'Ocupado' para garantizar consistencia y evitar colisiones
                        ejecutar_escritura(
                            "UPDATE Horario_Disponible SET estado_horario = 'Ocupado' WHERE id_horario = %s",
                            (id_horario_real,),
                            config=cfg_activa
                        )
                        st.success(f"🎉 ¡Cita #{id_nueva_cita} programada exitosamente! El horario asignado quedó registrado como 'Ocupado'.")
                    except Exception as err:
                        st.error(f"Error al programar la cita: {err}")
        else:
            if df_pets_c.empty:
                st.warning("⚠️ No hay mascotas registradas. Registra primero una mascota en la pestaña 'Gestión de Pacientes'.")
            if df_serv_c.empty:
                st.warning("⚠️ No hay servicios en el catálogo. Revisa la pestaña 'Catálogo y Listados'.")
            if df_horarios_c.empty:
                st.warning("⚠️ No hay horarios disponibles actualmente. Puedes generar o habilitar nuevos horarios en la subpestaña 'Apertura de Horarios'.")

    with sub_c2:
        st.subheader("Control y Gestión de Citas Agendadas")
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            filtro_est_cita = st.selectbox("Filtrar por Estado:", ["Todas", "Programada", "Confirmada", "Atendida", "Cancelada"])
        with col_f2:
            st.caption("Visualiza el historial de citas y actualiza su estado.")

        try:
            query_all_citas = """
                SELECT 
                    c.id_cita AS 'ID Cita',
                    h.fecha AS 'Fecha',
                    TIME_FORMAT(h.hora_inicio, '%H:%i') AS 'Hora',
                    m.nombre_mascota AS 'Paciente',
                    m.especie AS 'Especie',
                    u.nombre AS 'Propietario',
                    u.telefono AS 'Teléfono',
                    s.nombre_servicio AS 'Servicio',
                    CONCAT('$', FORMAT(s.costo, 2)) AS 'Costo',
                    c.estado_cita AS 'Estado'
                FROM Cita c
                JOIN Mascotas m ON c.id_mascota = m.id_mascota
                JOIN Usuario u ON m.id_usuario = u.id_usuario
                JOIN Horario_Disponible h ON c.id_horario = h.id_horario
                JOIN Servicio s ON c.id_servicio = s.id_servicio
                WHERE 1=1
            """
            params_ac = []
            if filtro_est_cita != "Todas":
                query_all_citas += " AND c.estado_cita = %s"
                params_ac.append(filtro_est_cita)
            query_all_citas += " ORDER BY h.fecha DESC, h.hora_inicio DESC"
            
            df_all_citas = ejecutar_consulta(query_all_citas, params=params_ac if params_ac else None, config=cfg_activa)
            if not df_all_citas.empty:
                st.dataframe(df_all_citas, use_container_width=True)
                
                st.markdown("---")
                st.markdown("##### ✏️ Actualizar Estado de una Cita")
                col_up1, col_up2, col_up3 = st.columns([2, 2, 1])
                with col_up1:
                    opciones_citas_up = {
                        f"Cita #{r['ID Cita']} - {r['Paciente']} ({r['Propietario']}) [{r['Fecha']} {r['Hora']}]": r['ID Cita']
                        for _, r in df_all_citas.iterrows()
                    }
                    cita_sel_up = st.selectbox("Seleccionar Cita a Modificar:", list(opciones_citas_up.keys()))
                with col_up2:
                    nuevo_estado = st.selectbox("Nuevo Estado:", ["Programada", "Confirmada", "Atendida", "Cancelada"])
                with col_up3:
                    st.write("")
                    st.write("")
                    if st.button("Actualizar Estado"):
                        id_c_sel = opciones_citas_up[cita_sel_up]
                        try:
                            ejecutar_escritura("UPDATE Cita SET estado_cita = %s WHERE id_cita = %s", (nuevo_estado, id_c_sel), config=cfg_activa)
                            # Si se cancela la cita, liberar el horario a 'Disponible'
                            if nuevo_estado == "Cancelada":
                                ejecutar_escritura(
                                    "UPDATE Horario_Disponible SET estado_horario = 'Disponible' WHERE id_horario = (SELECT id_horario FROM Cita WHERE id_cita = %s)",
                                    (id_c_sel,),
                                    config=cfg_activa
                                )
                            st.success(f"Cita #{id_c_sel} actualizada a '{nuevo_estado}' con éxito.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar estado: {e}")
            else:
                st.info("No se encontraron citas con el estado seleccionado.")
        except Exception as e:
            st.error(f"Error al consultar citas: {e}")

    with sub_c3:
        st.subheader("⏰ Apertura y Gestión de Horarios Disponibles")
        st.caption("Crea nuevos turnos para que los pacientes puedan agendar sus citas.")
        
        with st.form("form_nuevo_horario", clear_on_submit=True):
            col_h1, col_h2, col_h3 = st.columns(3)
            with col_h1:
                fecha_h = st.date_input("Fecha del Turno", min_value=date.today())
            with col_h2:
                hora_in = st.time_input("Hora de Inicio", value=time(9, 0))
            with col_h3:
                estado_h = st.selectbox("Estado del Horario", ["Disponible", "Ocupado"])
                
            submitted_h = st.form_submit_button("➕ Registrar Franja de Horario", type="primary")
            if submitted_h:
                try:
                    q_ins_h = "INSERT INTO Horario_Disponible (fecha, hora_inicio, estado_horario) VALUES (%s, %s, %s)"
                    nuevo_id_h = ejecutar_escritura(q_ins_h, (fecha_h, str(hora_in), estado_h), config=cfg_activa, return_last_id=True)
                    st.success(f"¡Franja de horario registrada con éxito! (ID Horario #{nuevo_id_h} para el {fecha_h} a las {hora_in})")
                except Exception as err:
                    st.error(f"Error al registrar horario: {err}")

        st.markdown("---")
        st.markdown("##### 📋 Horarios Registrados en el Sistema")
        try:
            df_h_list = ejecutar_consulta("""
                SELECT 
                    id_horario AS 'ID Horario',
                    fecha AS 'Fecha',
                    TIME_FORMAT(hora_inicio, '%H:%i') AS 'Hora',
                    estado_horario AS 'Estado'
                FROM Horario_Disponible
                ORDER BY fecha DESC, hora_inicio ASC
                LIMIT 25
            """, config=cfg_activa)
            st.dataframe(df_h_list, use_container_width=True)
        except Exception as e:
            st.error(f"Error al listar horarios: {e}")

# ==============================================================================
# PESTAÑA 4: MÓDULO DEL MÉDICO VETERINARIO & HISTORIAL CLÍNICO
# ==============================================================================
with pestana_med:
    sub_med1, sub_med2 = st.tabs(["📝 Registrar Consulta Médica", "📖 Expediente e Historial Clínico por Paciente"])
    
    with sub_med1:
        st.subheader("Atención Médica y Registro de Historial Clínico")
        st.caption("Módulo para el Médico Veterinario: captura de signos vitales, diagnóstico y tratamiento, vinculado a la tabla `Cita`.")
        
        try:
            # Consultar citas pendientes o atendidas que pueden registrar consulta médica
            query_citas_med = """
                SELECT 
                    c.id_cita,
                    m.nombre_mascota,
                    m.especie,
                    m.peso,
                    u.nombre AS dueno,
                    s.nombre_servicio,
                    h.fecha,
                    TIME_FORMAT(h.hora_inicio, '%H:%i') AS hora,
                    c.estado_cita
                FROM Cita c
                JOIN Mascotas m ON c.id_mascota = m.id_mascota
                JOIN Usuario u ON m.id_usuario = u.id_usuario
                JOIN Servicio s ON c.id_servicio = s.id_servicio
                JOIN Horario_Disponible h ON c.id_horario = h.id_horario
                ORDER BY h.fecha DESC, h.hora_inicio DESC
            """
            df_citas_med = ejecutar_consulta(query_citas_med, config=cfg_activa)
        except Exception as e:
            st.error(f"Error al cargar citas médicas: {e}")
            df_citas_med = pd.DataFrame()

        if not df_citas_med.empty:
            opciones_citas_med = {
                f"Cita #{r['id_cita']} - {r['nombre_mascota']} ({r['especie']}) | Dueño: {r['dueno']} | {r['nombre_servicio']} [{r['fecha']} {r['hora']}] - Estado: {r['estado_cita']}": (r['id_cita'], r['nombre_mascota'], r['peso'])
                for _, r in df_citas_med.iterrows()
            }
            
            cita_seleccionada_label = st.selectbox("Seleccionar Cita / Paciente para la Consulta *", list(opciones_citas_med.keys()))
            id_cita_sel, nombre_paciente_sel, peso_base = opciones_citas_med[cita_seleccionada_label]
            
            with st.form("form_consulta_medica", clear_on_submit=True):
                st.markdown(f"#### 🩺 Consulta Médica para: **{nombre_paciente_sel}** (Cita #{id_cita_sel})")
                
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    peso_act = st.number_input(
                        "Peso Actual del Paciente (kg) *", 
                        min_value=0.01, 
                        max_value=250.0, 
                        value=float(peso_base) if peso_base else 5.0, 
                        format="%.2f",
                        help="Se actualizará automáticamente en la ficha del paciente."
                    )
                with col_v2:
                    temp_act = st.number_input("Temperatura Corporal (°C) *", min_value=30.0, max_value=45.0, value=38.5, format="%.2f")

                sintomas_txt = st.text_area("Síntomas y Anamnesis Referida por el Dueño *", placeholder="Ej: Vómito recurrente desde hace 2 días, decaimiento e inapetencia...")
                diagnostico_txt = st.text_area("Diagnóstico Clínico *", placeholder="Ej: Gastroenteritis aguda bacteriana sin deshidratación severa...")
                tratamiento_txt = st.text_area("Tratamiento Clínico y Prescripción Médica *", placeholder="Ej: Terapia de fluidos 250ml. Amoxicilina con Ácido Clavulánico 250mg: 1 tableta cada 12 hrs por 7 días. Dieta blanda...")

                submitted_med = st.form_submit_button("💾 Guardar en Historial Médico", type="primary")

                if submitted_med:
                    if diagnostico_txt.strip() and tratamiento_txt.strip() and sintomas_txt.strip():
                        try:
                            # 1. Insertar en Historial_Medico
                            query_hist = """
                                INSERT INTO Historial_Medico (
                                    id_cita, peso_actual, temperatura, sintomas, diagnostico, tratamiento
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            id_hist_nuevo = ejecutar_escritura(
                                query_hist,
                                (id_cita_sel, peso_act, temp_act, sintomas_txt.strip(), diagnostico_txt.strip(), tratamiento_txt.strip()),
                                config=cfg_activa,
                                return_last_id=True
                            )
                            
                            # 2. Actualizar estado de la Cita a 'Atendida'
                            ejecutar_escritura("UPDATE Cita SET estado_cita = 'Atendida' WHERE id_cita = %s", (id_cita_sel,), config=cfg_activa)
                            
                            # 3. Actualizar el peso del paciente en la tabla Mascotas
                            ejecutar_escritura(
                                "UPDATE Mascotas SET peso = %s WHERE id_mascota = (SELECT id_mascota FROM Cita WHERE id_cita = %s)", 
                                (peso_act, id_cita_sel), 
                                config=cfg_activa
                            )
                            
                            st.success(f"🎉 ¡Consulta médica #{id_hist_nuevo} registrada con éxito! La Cita #{id_cita_sel} pasó a estado 'Atendida' y el peso del paciente fue actualizado.")
                        except Exception as err:
                            st.error(f"Error al registrar historial médico: {err}")
                    else:
                        st.warning("⚠️ Los síntomas, el diagnóstico y el tratamiento son obligatorios.")
        else:
            st.info("ℹ️ Para registrar una consulta médica, primero agenda una Cita en la pestaña 'Citas y Horarios'.")

    with sub_med2:
        st.subheader("Expediente e Historial Clínico Completo")
        st.caption("Visualiza toda la línea de tiempo de consultas y evolución médica por paciente.")
        
        try:
            df_pets_exp = ejecutar_consulta("SELECT id_mascota, nombre_mascota, especie FROM Mascotas ORDER BY nombre_mascota", config=cfg_activa)
            if not df_pets_exp.empty:
                dict_pets_exp = {f"{r['nombre_mascota']} ({r['especie']}) [ID Mascota: {r['id_mascota']}]": r['id_mascota'] for _, r in df_pets_exp.iterrows()}
                pet_exp_sel = st.selectbox("Seleccionar Paciente para consultar su Historial:", list(dict_pets_exp.keys()))
                id_mascota_exp = dict_pets_exp[pet_exp_sel]
                
                query_historial = """
                    SELECT 
                        h.id_historial,
                        c.id_cita,
                        hd.fecha,
                        TIME_FORMAT(hd.hora_inicio, '%H:%i') AS hora,
                        s.nombre_servicio,
                        h.peso_actual,
                        h.temperatura,
                        h.sintomas,
                        h.diagnostico,
                        h.tratamiento,
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
                df_historial = ejecutar_consulta(query_historial, params=[id_mascota_exp], config=cfg_activa)
                
                if not df_historial.empty:
                    st.success(f"📋 Se encontraron {len(df_historial)} registro(s) en el historial médico de este paciente.")
                    
                    for idx, row in df_historial.iterrows():
                        with st.expander(f"🩺 Consulta #{row['id_historial']} — Fecha: {row['fecha']} {row['hora']} | Servicio: {row['nombre_servicio']}", expanded=(idx == 0)):
                            c_sig1, c_sig2, c_sig3 = st.columns(3)
                            with c_sig1:
                                st.write(f"⚖️ **Peso Registrado:** {row['peso_actual']} kg")
                            with c_sig2:
                                st.write(f"🌡️ **Temperatura:** {row['temperatura']} °C")
                            with c_sig3:
                                st.write(f"👤 **Propietario:** {row['dueno']} (📞 {row['tel_dueno']})")
                                
                            st.markdown("---")
                            st.markdown(f"**🔍 Síntomas / Anamnesis:**\n{row['sintomas'] or 'Sin síntomas descritos'}")
                            st.markdown(f"**📌 Diagnóstico Clínico:**\n{row['diagnostico']}")
                            st.markdown(f"**💉 Tratamiento y Prescripción:**\n{row['tratamiento']}")
                else:
                    st.info("Este paciente aún no tiene consultas registradas en su historial médico.")
            else:
                st.info("No hay pacientes registrados.")
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

# ==============================================================================
# PESTAÑA 5: CATÁLOGO DE SERVICIOS Y LISTADO GENERAL (JOINs)
# ==============================================================================
with pestana_serv:
    sub_j1, sub_j2 = st.tabs(["📋 Consulta Multitabla Integral (JOIN)", "🏷️ Catálogo de Servicios"])
    
    with sub_j1:
        st.subheader("Listado General: Mascotas, Propietarios y Citas (JOIN)")
        st.caption("Demostración de la integridad referencial y consultas multitabla entre Mascotas, Usuario, Cita y Servicio.")
        try:
            query_master_join = """
                SELECT 
                    m.id_mascota AS 'ID Paciente',
                    m.nombre_mascota AS 'Mascota',
                    m.especie AS 'Especie',
                    m.raza AS 'Raza',
                    m.peso AS 'Peso (kg)',
                    u.nombre AS 'Propietario',
                    u.telefono AS 'Teléfono',
                    u.correo AS 'Correo Propietario',
                    COUNT(c.id_cita) AS 'Citas Registradas'
                FROM Mascotas m
                JOIN Usuario u ON m.id_usuario = u.id_usuario
                LEFT JOIN Cita c ON m.id_mascota = c.id_mascota
                GROUP BY m.id_mascota, m.nombre_mascota, m.especie, m.raza, m.peso, u.nombre, u.telefono, u.correo
                ORDER BY m.id_mascota ASC
            """
            df_master = ejecutar_consulta(query_master_join, config=cfg_activa)
            if not df_master.empty:
                st.dataframe(df_master, use_container_width=True)
                
                csv_data = df_master.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Reporte Completo en CSV",
                    data=csv_data,
                    file_name="reporte_clinica_amor_animal.csv",
                    mime="text/csv"
                )
            else:
                st.info("Aún no existen registros vinculados en la base de datos.")
        except Exception as e:
            st.error(f"Error al realizar la consulta multitabla: {e}")

    with sub_j2:
        st.subheader("Catálogo de Servicios Clínicos")
        try:
            df_servicios = ejecutar_consulta("SELECT id_servicio AS 'ID', nombre_servicio AS 'Servicio', descripcion AS 'Descripción', CONCAT('$', FORMAT(costo, 2)) AS 'Costo' FROM Servicio", config=cfg_activa)
            st.dataframe(df_servicios, use_container_width=True)
            
            st.markdown("---")
            st.markdown("##### ➕ Registrar Nuevo Servicio Clínico")
            with st.form("form_nuevo_servicio", clear_on_submit=True):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    nom_serv = st.text_input("Nombre del Servicio *", placeholder="Ej: Radiografía Digital")
                    costo_serv = st.number_input("Costo ($) *", min_value=10.0, max_value=50000.0, value=350.0, step=50.0)
                with col_s2:
                    desc_serv = st.text_input("Descripción breve", placeholder="Ej: Tomas radiológicas de tórax o miembros...")
                    
                submitted_serv = st.form_submit_button("Guardar Nuevo Servicio")
                if submitted_serv:
                    if nom_serv.strip():
                        try:
                            ejecutar_escritura(
                                "INSERT INTO Servicio (nombre_servicio, descripcion, costo) VALUES (%s, %s, %s)",
                                (nom_serv.strip(), desc_serv.strip(), costo_serv),
                                config=cfg_activa
                            )
                            st.success(f"Servicio '{nom_serv}' registrado exitosamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar servicio: {e}")
                    else:
                        st.warning("El nombre del servicio es obligatorio.")
        except Exception as e:
            st.error(f"Error al cargar servicios: {e}")

# ==============================================================================
# PESTAÑA 6: DIAGNÓSTICO DEL SISTEMA Y BASE DE DATOS
# ==============================================================================
with pestana_diag:
    st.subheader("⚙️ Diagnóstico de Integridad de la Base de Datos")
    st.caption("Inspección en tiempo real de las 7 tablas relacionales y su estado.")
    
    tablas = ["Rol", "Usuario", "Mascotas", "Servicio", "Horario_Disponible", "Cita", "Historial_Medico"]
    
    cols = st.columns(len(tablas))
    for i, tabla in enumerate(tablas):
        with cols[i]:
            try:
                cnt = ejecutar_consulta(f"SELECT COUNT(*) as c FROM {tabla}", config=cfg_activa).iloc[0]['c']
                st.metric(label=f"📁 {tabla}", value=cnt)
            except Exception:
                st.metric(label=f"📁 {tabla}", value="Error")

    st.markdown("---")
    st.markdown("##### 🔍 Ejecutor de Consultas SQL (SELECT)")
    st.caption("Herramienta interactiva para pruebas rápidas de laboratorio o evaluación.")
    
    consulta_usuario = st.text_area(
        "Sentencia SQL personalizada:",
        value="SELECT m.nombre_mascota, m.especie, u.nombre AS dueno, c.estado_cita FROM Mascotas m JOIN Usuario u ON m.id_usuario = u.id_usuario LEFT JOIN Cita c ON m.id_mascota = c.id_mascota LIMIT 10;"
    )
    if st.button("▶️ Ejecutar Consulta"):
        if consulta_usuario.strip().upper().startswith("SELECT"):
            try:
                df_custom = ejecutar_consulta(consulta_usuario, config=cfg_activa)
                st.dataframe(df_custom, use_container_width=True)
                st.success(f"Consulta ejecutada con éxito. Filas retornadas: {len(df_custom)}")
            except Exception as e:
                st.error(f"Error en la consulta: {e}")
        else:
            st.warning("Por seguridad, el ejecutor de pruebas solo permite sentencias SELECT.")
