# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from datos_turismo import AGENCIES_DB

app = FastAPI(
    title="Portal de Verificación y Prevención de Fraude Turístico",
    description="Módulo de Evaluación de Riesgo en Turismo (Cartagena y Santa Marta)",
    version="1.0.0"
)

# 1. Modelos de Entrada y Salida
class EvaluacionRiesgoRequest(BaseModel):
    nit_agencia: Optional[str] = Field(default=None)
    ciudad_destino: str = Field(default="Santa Marta")
    canal_venta: str = Field(default="instagram")
    temporada_alta: bool = Field(default=True)

class EvaluacionRiesgoResponse(BaseModel):
    nombre_agencia: str
    nivel_riesgo: str
    score_numerico: int
    rnt_registrado: bool
    se_consulto_nit: bool
    banderas_rojas: List[str]
    recomendaciones: List[str]

# 2. Servir la interfaz gráfica HTML principal
@app.get("/", response_class=HTMLResponse, summary="Ver Interfaz Web")
def cargar_interfaz():
    # Intenta leer el archivo HTML en el mismo directorio
    ruta_html = os.path.join(os.path.dirname(__file__), "index.html")
    if not os.path.exists(ruta_html):
        # Si el archivo tiene otro nombre (ej. codigo.html)
        ruta_html = os.path.join(os.path.dirname(__file__), "codigo.html")
    
    if os.path.exists(ruta_html):
        with open(ruta_html, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: No se encontró el archivo HTML de la interfaz gráfica en la carpeta.</h1>"

# 3. Endpoint de API procesador de reglas
@app.post("/evaluar-riesgo", response_model=EvaluacionRiesgoResponse, summary="Evaluar Riesgo")
def evaluar_riesgo(solicitud: EvaluacionRiesgoRequest):
    score = 0
    banderas_rojas = []
    recomendaciones = []
    rnt_valido = False
    se_consulto_nit = False
    nombre_agencia = "Consulta General de Servicio"

    ciudad = solicitud.ciudad_destino.strip().title()
    if ciudad not in ["Cartagena", "Santa Marta"]:
        raise HTTPException(status_code=400, detail="La herramienta está delimitada para servicios en Cartagena y Santa Marta.")

    nit = solicitud.nit_agencia.strip() if solicitud.nit_agencia else ""
    agencia_info = AGENCIES_DB.get(nit) if nit else None

    if agencia_info:
        se_consulto_nit = True
        nombre_agencia = agencia_info.get("nombre", "Agencia Registrada")
        rnt_valido = agencia_info.get("rnt_activo", False)

        if not rnt_valido:
            score += 40
            banderas_rojas.append("El NIT/RNT consultado NO cuenta con un registro activo en las bases oficiales del RNT.")
        
        quejas_sic = agencia_info.get("historico_quejas_sic", 0)
        if quejas_sic > 0:
            score += 20
            banderas_rojas.append(f"El prestador registra un histórico de {quejas_sic} quejas formales ante la Superintendencia de Industria y Comercio (SIC).")
            
        reportes_dijin = agencia_info.get("reportes_dijin", 0)
        if reportes_dijin > 0:
            score += 30
            banderas_rojas.append(f"Se identificaron {reportes_dijin} investigaciones o denuncias por estafa vinculadas en los registros de la Policía Nacional (DIJIN).")
    else:
        if nit != "":
            se_consulto_nit = True
            score += 35
            banderas_rojas.append("El número de NIT/RNT ingresado no fue localizado dentro de la lista de agencias formales verificadas.")
        else:
            score += 15
            banderas_rojas.append("No se ingresó un número de NIT/RNT para validación directa en registros públicos.")

    canal = solicitud.canal_venta.lower()
    if canal in ["instagram", "whatsapp", "facebook"]:
        score += 25
        banderas_rojas.append("Venta realizada exclusivamente vía redes sociales/mensajería instantánea sin verificación de portal web oficial.")
        recomendaciones.append("Exija que la cuenta bancaria receptora coincida con la Razón Social (S.A.S. o S.A.) de la empresa y su NIT.")
    elif canal in ["web", "página web oficial / plataforma reconocida"]:
        score += 5
        recomendaciones.append("Verifique que el sitio web cuente con certificado de seguridad SSL (candado en la URL) y políticas de retracto visibles.")
    elif canal in ["punto_fisico", "punto de venta físico / establecimiento"]:
        recomendaciones.append("Solicite la factura de venta formal con la resolución de autorización visible.")

    if solicitud.temporada_alta:
        score += 10
        banderas_rojas.append(f"Período de alta afluencia en {ciudad}: Coincide con el pico histórico delictivo de suplantación de agencias.")

    if score >= 40:
        recomendaciones.append("Evite realizar adelantos de dinero superiores al 20% antes de contar con vouchers de reserva confirmados.")
        recomendaciones.append("Consulte el Registro Único Empresarial y Social (RUES) antes de enviar cualquier transferencia bancaria.")

    if score >= 60:
        nivel = "ALTO"
        recomendaciones.append("ABSTÉNGASE DE REALIZAR PAGOS. El proveedor presenta múltiples factores de riesgo.")
    elif score >= 30:
        nivel = "MEDIO"
        recomendaciones.append("Solicite el certificado de RNT actualizado antes de realizar transferencias.")
    else:
        nivel = "BAJO"
        recomendaciones.append("El proveedor cumple con las validaciones básicas de registro legal.")

    return EvaluacionRiesgoResponse(
        nombre_agencia=nombre_agencia,
        nivel_riesgo=nivel,
        score_numerico=min(score, 100),
        rnt_registrado=rnt_valido,
        se_consulto_nit=se_consulto_nit,
        banderas_rojas=banderas_rojas,
        recomendaciones=recomendaciones
    )