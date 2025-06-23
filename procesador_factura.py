import math
import pdfplumber
import re

def procesar_factura_pdf(file, estructura, cubierta, ubicacion, tipo_inversor):
    with pdfplumber.open(file) as pdf:
        texto = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # === OCR especializado para facturas EEP (Empresa de Energía de Pereira) ===
    patrones_consumo = re.findall(r"\b[A-Z]{3}\s+(\d{2,3})\s+\d{1,3}[,.]\d{3}\s+\d{2}\b", texto)
    consumo_prom = None

    if patrones_consumo:
        consumos_numeros = [int(valor) for valor in patrones_consumo]
        consumo_prom = sum(consumos_numeros) / len(consumos_numeros)

    if consumo_prom is None:
        return {"error": "No se pudo identificar el consumo mensual en la factura EEP."}

    # === Potencia requerida (kWp) ===
    hsp = 4.5
    eficiencia = 0.8
    consumo_diario = consumo_prom / 30
    potencia_kwp = consumo_diario / (hsp * eficiencia)

    # === Valor base por kWp según tipo de inversor ===
    precio_base_kwp = 3_800_000 if tipo_inversor == "ongrid" else 4_200_000
    valor_base = potencia_kwp * precio_base_kwp

    # === Factores de ajuste ===
    factores_estructura = {
        'trapezoidal': 0.0,
        'teja_colonial': 0.2,
        'fibrocemento': 0.1,
        'perfil_metalico': 0.05,
        'madera': 0.1,
        'cercha': 0.15,
        'plancha': 0.05,
        'granja': 0.2
    }

    factores_ubicacion = {
        'risaralda': 0.0,
        'valle': 0.1,
        'quindio': 0.2,
        'caldas': 0.1
    }

    factor_total = 1 + factores_estructura.get(estructura, 0) + factores_ubicacion.get(ubicacion, 0)
    precio_total = round(valor_base * factor_total)

    panel_watt = 580
    numero_paneles = math.ceil(potencia_kwp * 1000 / panel_watt)

    return {
        "consumo_kwh": round(consumo_prom, 2),
        "potencia_kwp": round(potencia_kwp, 2),
        "numero_paneles": numero_paneles,
        "precio_total": precio_total
    }
