# main.py
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from modelo_financiero import calcular_flujo_fotovoltaico
from procesador_factura import procesar_factura_pdf, procesar_datos_manuales  # <- importar la nueva función

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    tipoInversor: str = Form(...),
    porcentajeGeneracion: int = Form(100)
):
    return procesar_factura_pdf(
        file.file, estructura, cubierta, ubicacion, tipoInversor,
        porcentaje_generacion=porcentajeGeneracion
    )

# === NUEVO: procesar datos manuales ===
@app.post("/procesar-datos")
async def procesar_datos(request: Request):
    data = await request.json()
    return procesar_datos_manuales(
        nombre=data.get("nombre"),
        direccion=data.get("direccion"),
        municipio=data.get("municipio"),
        estrato=str(data.get("estrato", "0")),
        tipo_servicio=data.get("tipo_servicio"),
        consumo_kwh=float(data.get("consumo_kwh") or 0),
        valor_kwh=(float(data["valor_kwh"]) if data.get("valor_kwh") is not None else None),
        estructura=data.get("estructura"),
        cubierta=data.get("cubierta"),
        ubicacion=data.get("ubicacion"),
        tipo_inversor=data.get("tipoInversor"),
        porcentaje_generacion=int(data.get("porcentajeGeneracion", 100)),
    )

@app.post("/calcular")
async def calcular(request: Request):
    data = await request.json()
    resultado = calcular_flujo_fotovoltaico(data)
    return resultado
