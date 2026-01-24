import math
import re
from typing import Optional
import pdfplumber

inversores = [
    {"serie": "GT1", "modelo": "GT1-1K6-S1", "potencia": 1.6},
    {"serie": "GT1", "modelo": "GT1-2K2-S1", "potencia": 2.2},
    {"serie": "GT1", "modelo": "GT1-3K-S1", "potencia": 3.0},
    {"serie": "GT1", "modelo": "GT1-3K3-S1", "potencia": 3.3},
    {"serie": "GT1", "modelo": "GT1-3K6-D1", "potencia": 3.6},
    {"serie": "GT1", "modelo": "GT1-4K-D1", "potencia": 4.0},
    {"serie": "GT1", "modelo": "GT1-4K6-D1", "potencia": 4.6},
    {"serie": "GT1", "modelo": "GT1-5K-D1", "potencia": 5.0},
    {"serie": "GT1", "modelo": "GT1-6K-D1", "potencia": 6.0},
    {"serie": "GT1", "modelo": "GT1-7K-T2", "potencia": 7.0},
    {"serie": "GT1", "modelo": "GT1-7K5-T2", "potencia": 7.5},
    {"serie": "GT1", "modelo": "GT1-8K-T2", "potencia": 8.0},
    {"serie": "GT1", "modelo": "GT1-9K-T2", "potencia": 9.0},
    {"serie": "GT1", "modelo": "GT1-10K-T2", "potencia": 10.0},
    {"serie": "Hyper", "modelo": "Hyper-3K", "potencia": 3.0},
    {"serie": "Hyper", "modelo": "Hyper-3K6", "potencia": 3.6},
    {"serie": "Hyper", "modelo": "Hyper-4K6", "potencia": 4.6},
    {"serie": "Hyper", "modelo": "Hyper-5K", "potencia": 5.0},
    {"serie": "GT3", "modelo": "GT3-10K-DL1", "potencia": 10.0},
    {"serie": "GT3", "modelo": "GT3-12K-DL1", "potencia": 12.0},
    {"serie": "GT3", "modelo": "GT3-17KL-D", "potencia": 17.0},
    {"serie": "GT3", "modelo": "GT3-20KL-T", "potencia": 20.0},
    {"serie": "GT3", "modelo": "GT3-25KL-T", "potencia": 25.0},
    {"serie": "GT3", "modelo": "GT3-30KL-Q", "potencia": 30.0},
    {"serie": "GT3", "modelo": "GT3-50K-Q", "potencia": 50.0},
    {"serie": "GT3", "modelo": "GT3-60K-Q", "potencia": 60.0},
    {"serie": "GT3", "modelo": "GT3-100K", "potencia": 100.0},
    {"serie": "GT3", "modelo": "GT3-125K", "potencia": 125.0}
]

# ------------------- Utilidades de extracción -------------------
MESES_ABR = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

def _texto_en_bbox(words, x0, x1, y0, y1) -> str:
    sel = [w["text"] for w in words if x0 <= float(w["x0"]) <= x1 and y0 <= float(w["top"]) <= y1]
    return " ".join(sel).strip() if sel else ""

def _extraer_consumos_mensuales(words) -> list:
    consumos = []
    for i in range(len(words)-1):
        mes = words[i]["text"].strip().upper()
        sig = words[i+1]["text"].replace(".", "").replace(",", "").strip()
        if mes in MESES_ABR and sig.isdigit():
            consumos.append(int(sig))
    return consumos

def extraer_valor_kwh(words) -> Optional[float]:
    """
    Heurística: buscar un número con 3-4 decimales en el rango 300..2000 (COP/kWh).
    """
    tokens = [w["text"].replace(",", "").strip() for w in words]
    for tok in tokens:
        m = re.match(r"^(\d+\.\d{3,4})$", tok)
        if m:
            try:
                val = float(m.group(1))
                if 300 <= val <= 2000:
                    return val
            except:
                pass
    # fallback: buscar patrón $ XXX.XXXX o COP XXX.XXXX
    joined = " ".join(tokens)
    m2 = re.search(r"(?:\$|COP)\s*(\d+\.\d{3,4})", joined, flags=re.I)
    if m2:
        try:
            val = float(m2.group(1))
            if 300 <= val <= 2000:
                return val
        except:
            pass
    return None

# ------------------- Núcleo común Colombia -------------------
FACTORES_CUBIERTA = {'trapezoidal': 0.0, 'teja_colonial': 0.2, 'fibrocemento': 0.1,'grafada': 0.0,}
FACTORES_ESTRUCTURA = {'madera': 0.2, 'cercha': 0.1, 'plancha': 0.0, 'granja': 0.2, 'perfil_metalico': 0.05}
FACTORES_UBICACION = {'risaralda': 0.0, 'valle': 0.2, 'quindio': 0.15, 'caldas': 0.1, 'antioquia': 0.2}

def _calculos_colombia(consumo_prom, tipo_servicio, tipo_inversor, estructura, cubierta, ubicacion, porcentaje_generacion):
    # Parámetros base
    hsp = 4.5
    eficiencia = 0.85
    # Cobertura
    try:
        pct = int(porcentaje_generacion)
    except:
        pct = 100
    if pct not in (50, 100, 150, 200):
        pct = 100
    factor_cobertura = pct / 100.0

    consumo_diario = max(consumo_prom, 0) / 30.0
    potencia_kwp_base = consumo_diario / (hsp * eficiencia)
    potencia_kwp = round(potencia_kwp_base * factor_cobertura, 2)

    # Selección inversor más cercano
    inv = min(inversores, key=lambda x: abs(x["potencia"] - potencia_kwp))

    # Precio base por tipo
    if (tipo_inversor or "").lower() == "hibrido":
        precio_base_kwp = 7_600_000
    else:
        precios_servicio = {"residencial": 4_300_000, "comercial": 4_100_000, "industrial": 3_300_000}
        precio_base_kwp = precios_servicio.get((tipo_servicio or "").lower(), 4_300_000)

    valor_base = potencia_kwp * precio_base_kwp

    # Factores locales
    f_total = 1 \
        + FACTORES_ESTRUCTURA.get((estructura or "").lower(), 0) \
        + FACTORES_CUBIERTA.get((cubierta or "").lower(), 0) \
        + FACTORES_UBICACION.get((ubicacion or "").lower(), 0)

    precio_total = round(valor_base * f_total)

    # Paneles 580 W
    numero_paneles = max(1, math.ceil(potencia_kwp * 1000 / 580))

    # Generación mensual estimada
    generacion_min = round(potencia_kwp * 1300) / 12
    generacion_max = round(potencia_kwp * 1600) / 12

    return potencia_kwp, inv, precio_total, numero_paneles, generacion_min, generacion_max, pct

# ------------------- Procesar PDF -------------------
def procesar_factura_pdf(file, estructura, cubierta, ubicacion, tipo_inversor, porcentaje_generacion: int = 100):
    """
    Lee la factura (PDF) y estima la potencia, inversor y precio.
    """
    with pdfplumber.open(file) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()

        consumos = _extraer_consumos_mensuales(words)
        if not consumos:
            return {"error": "No se encontraron consumos mensuales para calcular el promedio."}
        consumo_prom = sum(consumos) / len(consumos)

        # Datos del cliente (heurísticos por posición; si fallan, quedan vacíos)
        def _bbox(x0,x1,y0,y1): 
            return _texto_en_bbox(words, x0,x1,y0,y1) or "No disponible"

        nombre    = _bbox(10, 200, 30, 40)
        direccion = _bbox(10, 220, 42, 53)
        municipio = _bbox(120, 180, 60, 70)
        estrato   = _bbox(250, 270, 76, 85)

        tipo_servicio_texto = (_bbox(200, 240, 63, 70) or "").lower()
        if "residencial" in tipo_servicio_texto:
            tipo_servicio = "Residencial"
        elif "comercial" in tipo_servicio_texto:
            tipo_servicio = "Comercial"
        elif "industrial" in tipo_servicio_texto:
            tipo_servicio = "Industrial"
        else:
            tipo_servicio = "Residencial"  # por defecto

        potencia_kwp, inv, precio_total, numero_paneles, generacion_min, generacion_max, pct = _calculos_colombia(
            consumo_prom, tipo_servicio, tipo_inversor, estructura, cubierta, ubicacion, porcentaje_generacion
        )

        valor_kwh = extraer_valor_kwh(words)

        # Contribución 20% cuando aplica
        try:
            estrato_int = int(estrato)
        except:
            estrato_int = 0
        servicio_l = (tipo_servicio or "").lower()
        aplica_contribucion = (servicio_l in ("comercial", "industrial")) or (servicio_l == "residencial" and estrato_int in (5,6))

        valor_energia_mensual = (valor_kwh or 0) * consumo_prom
        valor_contribucion = round(0.2 * valor_energia_mensual) if aplica_contribucion else 0
        costo_energia = valor_energia_mensual * 12 + valor_contribucion * 12

        return {
            "nombre": nombre or "No disponible",
            "direccion": direccion or "No disponible",
            "tipo_servicio": tipo_servicio,
            "estrato": estrato or "0",
            "municipio": municipio or "No disponible",
            "consumo_kwh": round(consumo_prom, 2),
            "potencia_kwp": potencia_kwp,
            "numero_paneles": numero_paneles,
            "precio_total": precio_total,
            "valor_kwh": valor_kwh,
            "valor_contribucion": valor_contribucion,
            "generacion_mensual_min": generacion_min,
            "generacion_mensual_max": generacion_max,
            "inversor_utilizado": f"{inv['modelo']} ({inv['potencia']} kW)",
            "costo_energia": costo_energia,
            "porcentaje_generacion": pct
        }

# ------------------- Procesar datos manuales -------------------
def procesar_datos_manuales(
    nombre: str,
    direccion: str,
    municipio: str,
    estrato: str,
    tipo_servicio: str,
    consumo_kwh: float,
    estructura: str,
    cubierta: str,
    ubicacion: str,
    tipo_inversor: str,
    porcentaje_generacion: int = 100,
    valor_kwh: Optional[float] = None
):
    consumo_prom = max(float(consumo_kwh or 0), 0.0)

    potencia_kwp, inv, precio_total, numero_paneles, generacion_min, generacion_max, pct = _calculos_colombia(
        consumo_prom, tipo_servicio, tipo_inversor, estructura, cubierta, ubicacion, porcentaje_generacion
    )

    # Contribución 20% cuando aplica
    try:
        estrato_int = int(estrato)
    except:
        estrato_int = 0
    servicio_l = (tipo_servicio or "").strip().lower()
    aplica_contribucion = (servicio_l in ("comercial", "industrial")) or (servicio_l == "residencial" and estrato_int in (5,6))

    valor_energia_mensual = (valor_kwh or 0) * consumo_prom
    valor_contribucion = round(0.2 * valor_energia_mensual) if aplica_contribucion else 0
    costo_energia = valor_energia_mensual * 12 + valor_contribucion * 12

    return {
        "nombre": nombre or "No disponible",
        "direccion": direccion or "No disponible",
        "tipo_servicio": tipo_servicio or "Residencial",
        "estrato": str(estrato or "0"),
        "municipio": municipio or "No disponible",
        "consumo_kwh": round(consumo_prom, 2),
        "potencia_kwp": potencia_kwp,
        "numero_paneles": numero_paneles,
        "precio_total": precio_total,
        "valor_kwh": valor_kwh,
        "valor_contribucion": valor_contribucion,
        "generacion_mensual_min": generacion_min,
        "generacion_mensual_max": generacion_max,
        "inversor_utilizado": f"{inv['modelo']} ({inv['potencia']} kW)",
        "costo_energia": costo_energia,
        "porcentaje_generacion": pct
    }
