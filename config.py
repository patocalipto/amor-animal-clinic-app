"""
Configuraciones globales y constantes del sistema para Clínica Veterinaria Amor Animal.
"""

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "clinica_amor_animal",
    "port": 3306
}

ROLES_PERMITIDOS = [
    "Administrador",
    "Veterinario",
    "Cliente",
    "Recepcionista"
]

ESPECIES_PERMITIDAS = [
    "Perro",
    "Gato",
    "Ave",
    "Conejo",
    "Reptil",
    "Roedor",
    "Equino",
    "Otro"
]

ESTADOS_CITA = [
    "Programada",
    "Confirmada",
    "Atendida",
    "Cancelada"
]
