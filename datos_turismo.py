# datos_turismo.py

# Simulación de la base de datos anonimizada y cruzada (SIC + RNT + DIJIN)
AGENCIES_DB = {
    "900123456": {
        "nombre": "Caribe Tours & Viajes S.A.S.",
        "rnt_activo": True,
        "ciudad": "Cartagena",
        "historico_quejas_sic": 0,
        "reportes_dijin": 0,
        "canales_oficiales": ["web", "punto_fisico"]
    },
    "800987654": {
        "nombre": "Santa Marta Ecotours Informales",
        "rnt_activo": False,
        "ciudad": "Santa Marta",
        "historico_quejas_sic": 5,
        "reportes_dijin": 2,
        "canales_oficiales": ["instagram"]
    }
}