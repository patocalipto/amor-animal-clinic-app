-- ==============================================================================
-- BASE DE DATOS: clinica_amor_animal
-- Sistema de Gestión para Clínica Veterinaria "Amor Animal"
-- Esquema relacional con llaves foráneas e integridad referencial
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS clinica_amor_animal 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_general_ci;

USE clinica_amor_animal;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- 1. TABLA: Rol
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Rol (
  id_rol INT(11) NOT NULL AUTO_INCREMENT,
  nombre_rol VARCHAR(50) NOT NULL,
  PRIMARY KEY (id_rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------------------------
-- 2. TABLA: Usuario
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Usuario (
  id_usuario INT(11) NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  telefono VARCHAR(15) NOT NULL,
  correo VARCHAR(100) NOT NULL UNIQUE,
  contrasena VARCHAR(255) NOT NULL,
  id_rol INT(11) DEFAULT NULL,
  PRIMARY KEY (id_usuario),
  KEY id_rol (id_rol),
  CONSTRAINT usuario_ibfk_1 
    FOREIGN KEY (id_rol) REFERENCES Rol (id_rol) 
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------------------------
-- 3. TABLA: Mascotas
-- ------------------------------------------------------------------------------
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
  CONSTRAINT mascotas_ibfk_1 
    FOREIGN KEY (id_usuario) REFERENCES Usuario (id_usuario) 
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------------------------
-- 4. TABLA: Servicio
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Servicio (
  id_servicio INT(11) NOT NULL AUTO_INCREMENT,
  nombre_servicio VARCHAR(100) NOT NULL,
  descripcion TEXT DEFAULT NULL,
  costo DECIMAL(10,2) DEFAULT NULL,
  PRIMARY KEY (id_servicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------------------------
-- 5. TABLA: Horario_Disponible
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Horario_Disponible (
  id_horario INT(11) NOT NULL AUTO_INCREMENT,
  fecha DATE NOT NULL,
  hora_inicio TIME NOT NULL,
  estado_horario VARCHAR(20) DEFAULT 'Disponible',
  PRIMARY KEY (id_horario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------------------------
-- 6. TABLA: Cita
-- ------------------------------------------------------------------------------
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
  CONSTRAINT cita_ibfk_1 
    FOREIGN KEY (id_mascota) REFERENCES Mascotas (id_mascota) 
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT cita_ibfk_2 
    FOREIGN KEY (id_horario) REFERENCES Horario_Disponible (id_horario) 
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT cita_ibfk_3 
    FOREIGN KEY (id_servicio) REFERENCES Servicio (id_servicio) 
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------------------------
-- 7. TABLA: Historial_Medico
-- ------------------------------------------------------------------------------
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
  CONSTRAINT historial_medico_ibfk_1 
    FOREIGN KEY (id_cita) REFERENCES Cita (id_cita) 
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- INSERCIÓN DE DATOS INICIALES (SEED DATA)
-- ==============================================================================

-- 1. Roles iniciales
INSERT INTO Rol (id_rol, nombre_rol) VALUES
(1, 'Administrador'),
(2, 'Veterinario'),
(3, 'Propietario')
ON DUPLICATE KEY UPDATE nombre_rol=VALUES(nombre_rol);

-- 2. Usuarios de prueba (Veterinarios, Propietarios y Admin)
INSERT INTO Usuario (id_usuario, nombre, telefono, correo, contrasena, id_rol) VALUES
(1, 'Administrador General', '555-0100', 'admin@amoranimal.com', 'admin123', 1),
(2, 'Dr. Roberto Mendoza', '555-0201', 'roberto.mendoza@amoranimal.com', 'vet123', 2),
(3, 'Carlos Fuentes Hernández', '555-0301', 'carlos.fuentes@correo.com', 'cliente123', 3),
(4, 'Mariana Gómez Lozano', '555-0302', 'mariana.gomez@correo.com', 'cliente123', 3),
(5, 'Sofía Ramírez Díaz', '555-0303', 'sofia.ramirez@correo.com', 'cliente123', 3)
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- 3. Catálogo de Servicios
INSERT INTO Servicio (id_servicio, nombre_servicio, descripcion, costo) VALUES
(1, 'Consulta General Veterinaria', 'Revisión médica completa, toma de constantes vitales y valoración física.', 250.00),
(2, 'Vacunación y Desparasitación', 'Aplicación de esquemas preventivos de vacunas y desparasitante interno/externo.', 350.00),
(3, 'Esterilización / Cirugía Menor', 'Procedimiento quirúrgico con anestesia segura y monitoreo constante.', 1200.00),
(4, 'Limpieza Dental (Profilaxis)', 'Remoción de sarro por ultrasonido y pulido dental para salud bucal.', 600.00),
(5, 'Estética Canina y Felina', 'Baño terapéutico, corte de pelo especializado, limpieza de oídos y uñas.', 300.00),
(6, 'Urgencias Médicas', 'Atención inmediata por cuadros críticos, traumatismos o intoxicaciones.', 500.00)
ON DUPLICATE KEY UPDATE nombre_servicio=VALUES(nombre_servicio);

-- 4. Mascotas iniciales
INSERT INTO Mascotas (id_mascota, nombre_mascota, especie, raza, edad_aprox, peso, id_usuario) VALUES
(1, 'Max', 'Perro', 'Golden Retriever', 4, 30.50, 3),
(2, 'Luna', 'Gato', 'Siamés', 2, 4.20, 3),
(3, 'Rocky', 'Perro', 'Bulldog Francés', 3, 12.80, 4),
(4, 'Pelusa', 'Conejo', 'Cabeza de León', 1, 1.85, 5)
ON DUPLICATE KEY UPDATE nombre_mascota=VALUES(nombre_mascota);

-- 5. Horarios Disponibles de Ejemplo (CURDATE y días posteriores)
INSERT INTO Horario_Disponible (id_horario, fecha, hora_inicio, estado_horario) VALUES
(1, CURDATE(), '09:00:00', 'Ocupado'),
(2, CURDATE(), '10:00:00', 'Disponible'),
(3, CURDATE(), '11:00:00', 'Disponible'),
(4, CURDATE(), '12:00:00', 'Disponible'),
(5, CURDATE(), '16:00:00', 'Disponible'),
(6, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:30:00', 'Disponible'),
(7, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '10:30:00', 'Disponible'),
(8, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '11:30:00', 'Disponible'),
(9, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '10:00:00', 'Disponible'),
(10, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '11:00:00', 'Disponible')
ON DUPLICATE KEY UPDATE estado_horario=VALUES(estado_horario);

-- 6. Citas iniciales
INSERT INTO Cita (id_cita, id_mascota, id_horario, id_servicio, estado_cita) VALUES
(1, 1, 1, 1, 'Atendida')
ON DUPLICATE KEY UPDATE estado_cita=VALUES(estado_cita);

-- 7. Historial Médico inicial
INSERT INTO Historial_Medico (id_historial, id_cita, peso_actual, temperatura, sintomas, diagnostico, tratamiento) VALUES
(1, 1, 30.50, 38.4, 'Decaimiento leve tras caminatas largas y ligera claudicación en miembro posterior derecho.', 'Leve esguince articular en corvejón derecho. Sin compromiso óseo.', 'Reposo relativo durante 5 días. Crioterapia local (10 min c/8 hrs) y Meloxicam 0.1 mg/kg vía oral cada 24 horas con comida.')
ON DUPLICATE KEY UPDATE diagnostico=VALUES(diagnostico);
