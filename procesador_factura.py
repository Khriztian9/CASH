import math
import pdfplumber
import re

def procesar_factura_pdf(file, estructura, cubierta, ubicacion, tipo_inversor):
    with pdfplumber.open(file) as pdf:
        texto = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        page0_words = pdf.pages[0].extract_words()

    # === 1. Extracción de consumo mensual ===
    consumo_mensual = re.findall(r"\n(?:DIC|ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV)\s+(\d{1,3})", texto)
    consumos = [int(c) for c in consumo_mensual if int(c) > 0][-6:]

    if not consumos:
        return {"error": "No se pudo identificar el consumo mensual en la factura."}

    consumo_prom = sum(consumos) / len(consumos)
    hsp = 4.5
    eficiencia = 0.8
    consumo_diario = consumo_prom / 30
    potencia_kwp = consumo_diario / (hsp * eficiencia)

    # === 2. Extracción de datos del cliente ===
    def extraer_por_posicion(words, x0, x1, y0, y1):
        elementos = [w["text"] for w in words if x0 <= float(w["x0"]) <= x1 and y0 <= float(w["top"]) <= y1]
        return " ".join(elementos).strip() if elementos else "No disponible"

    nombre     = extraer_por_posicion(page0_words, 10, 200, 30, 40)
    direccion  = extraer_por_posicion(page0_words, 10, 220, 42, 53)
    municipio  = extraer_por_posicion(page0_words, 140, 180, 63, 70)
    estrato    = extraer_por_posicion(page0_words, 250, 270, 76, 85)

    tipo_servicio_texto = extraer_por_posicion(page0_words, 200, 240, 63, 70).lower()
    if "residencial" in tipo_servicio_texto:
        tipo_servicio = "Residencial"
    elif "comercial" in tipo_servicio_texto:
        tipo_servicio = "Comercial"
    elif "industrial" in tipo_servicio_texto:
        tipo_servicio = "Industrial"
    else:
        tipo_servicio = "No disponible"

    # === 3. Cálculo financiero del sistema ===
    precio_base_kwp = 3_800_000 if tipo_inversor == "ongrid" else 4_200_000
    valor_base = potencia_kwp * precio_base_kwp

    factores_cubierta = {
        'trapezoidal': 0.0,
        'teja_colonial': 0.2,
        'fibrocemento': 0.1,

    }
    factores_estructura = {
        'madera': 0.25,
        'cercha': 0.15,
        'plancha': 0.05,
        'granja': 0.2,
        'perfil_metalico': 0.05,
        
    }

    factores_ubicacion = {
        'risaralda': 0.0,
        'valle': 0.1,
        'quindio': 0.2,
        'caldas': 0.1
    }

    factor_total = 1 + \
                   factores_estructura.get(estructura, 0) + \
                   factores_cubierta.get(cubierta, 0) + \
                   factores_ubicacion.get(ubicacion, 0)

    precio_total = round(valor_base * factor_total)

    panel_watt = 580
    numero_paneles = math.ceil(potencia_kwp * 1000 / panel_watt)

    return {
        "nombre": nombre,
        "direccion": direccion,
        "tipo_servicio": tipo_servicio,
        "estrato": estrato,
        "municipio": municipio,
        "consumo_kwh": round(consumo_prom, 2),
        "potencia_kwp": round(potencia_kwp, 2),
        "numero_paneles": numero_paneles,
        "precio_total": precio_total
    }
