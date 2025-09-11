from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from modelo_financiero import calcular_flujo_fotovoltaico
from procesador_factura import procesar_factura_pdf

app = FastAPI()

# CORS: permitir llamadas desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # puedes restringir a tu dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/procesar-factura")
async def procesar_factura(
    file: UploadFile = File(...),
    estructura: str = Form(...),
    cubierta: str = Form(...),
    ubicacion: str = Form(...),
    tipoInversor: str = Form(...),             # el frontend ya envía tipoInversor en camelCase
    porcentajeGeneracion: int = Form(100)      # NUEVO: cobertura de generación
):
    """
    Endpoint para procesar factura PDF y dimensionar el sistema FV.
    """
    return procesar_factura_pdf(
        file.file,
        estructura,
        cubierta,
        ubicacion,
        tipoInversor,
        porcentaje_generacion=porcentajeGeneracion
    )

@app.post("/calcular")
async def calcular(request: Request):
    """
    Endpoint para el modelo financiero de proyectos FV.
    """
    data = await request.json()
    resultado = calcular_flujo_fotovoltaico(data)
    return resultado

"""
@app.post("/cotizar")
async def cotizar(request: Request):
    data = await request.json()
    resultado = calcular_cotizacion_proyecto(data)
    return resultado
"""
