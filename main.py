from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from modelo_financiero import calcular_flujo_fotovoltaico
from cotizador import calcular_cotizacion_proyecto

app = FastAPI()

# Permitir llamadas desde el frontend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/calcular")
async def calcular(request: Request):
    data = await request.json()
    resultado = calcular_flujo_fotovoltaico(data)
    return resultado

@app.post("/cotizar")
async def cotizar(request: Request):
    data = await request.json()
    resultado = calcular_cotizacion_proyecto(data)
    return resultado