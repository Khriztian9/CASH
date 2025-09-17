# main.py
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from modelo_financiero import calcular_flujo_fotovoltaico
from Procesador_factura import procesar_factura_pdf

app = FastAPI()

# CORS: permitir llamadas desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # puedes restringir a tu dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📌 Endpoint 1: procesar factura PDF
@app.post("/procesar-factura")
async def procesar_factura(
    file: UploadFile = File(...),
    estructura: str = Form(...),
    cubierta: str = Form(...),
    ubicacion: str = Form(...),
    tipoInversor: str = Form(...),             # frontend envía en camelCase
    porcentajeGeneracion: int = Form(100)      # cobertura de generación
):
    return procesar_factura_pdf(
        file.file,
        estructura,
        cubierta,
        ubicacion,
        tipoInversor,
        porcentaje_generacion=porcentajeGeneracion
    )

# 📌 Endpoint 2: modelo financiero
@app.post("/calcular")
async def calcular(request: Request):
    data = await request.json()
    resultado = calcular_flujo_fotovoltaico(data)
    return resultado
