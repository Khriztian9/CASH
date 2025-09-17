import math
import re
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
    {"serie": "GT3", "modelo": "GT3-30KL-Q", "potencia": 30.0}
]

def procesar_factura_pdf(file, estructura, cubierta, ubicacion, tipo_inversor, porcentaje_generacion: int = 100):
    """
    porcentaje_generacion: entero 50, 100, 150 o 200 que representa la cobertura deseada del consumo.
    """
    with pdfplumber.open(file) as pdf:
        page0_words = pdf.pages[0].extract_words()
        meses = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
        consumos = []

        # Extraer consumos mensuales
        for i in range(len(page0_words) - 1):
            mes = page0_words[i]["text"].strip().upper()
            siguiente = page0_words[i + 1]["text"].strip()
            if mes in meses:
                valor = siguiente.replace(".", "").replace(",", "")
                if valor.isdigit():
                    consumos.append(int(valor))

        if not consumos:
            return {"error": "No se encontraron consumos mensuales en la factura para calcular el promedio."}

        consumo_prom = sum(consumos) / len(consumos)

        def extraer_por_posicion(words, x0, x1, y0, y1):
            elementos = [w["text"] for w in words if x0 <= float(w["x0"]) <= x1 and y0 <= float(w["top"]) <= y1]
            return " ".join(elementos).strip() if elementos else "No disponible"

        nombre     = extraer_por_posicion(page0_words, 10, 200, 30, 40)
        direccion  = extraer_por_posicion(page0_words, 10, 220, 42, 53)
        municipio  = extraer_por_posicion(page0_words, 120, 180, 60, 70)
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

        # Parámetros Colombia
        hsp = 4.5
        eficiencia = 0.85

        consumo_diario = consumo_prom / 30.0
        potencia_kwp_base = consumo_diario / (hsp * eficiencia)

        # Cobertura (%)
        try:
            pct = int(porcentaje_generacion)
        except:
            pct = 100
        if pct not in (50, 100, 150, 200):
            pct = 100
        factor_cobertura = pct / 100.0
        potencia_kwp = round(potencia_kwp_base * factor_cobertura, 2)

        # Selección del inversor más cercano
        inversor = min(inversores, key=lambda inv: abs(inv["potencia"] - potencia_kwp))

        # Precio
        if tipo_inversor.lower() == "hibrido":
            precio_base_kwp = 7_600_000
        else:
            precios_servicio = {
                "residencial": 4_300_000,
                "comercial": 3_800_000,
                "industrial": 3_300_000
            }
            precio_base_kwp = precios_servicio.get(tipo_servicio.lower(), 4_300_000)

        valor_base = potencia_kwp * precio_base_kwp

        factores_cubierta = {'trapezoidal': 0.0, 'teja_colonial': 0.2, 'fibrocemento': 0.1}
        factores_estructura = {'madera': 0.2, 'cercha': 0.1, 'plancha': 0, 'granja': 0.2, 'perfil_metalico': 0.05}
        factores_ubicacion = {'risaralda': 0.0, 'valle': 0.2, 'quindio': 0.15, 'caldas': 0.1}

        factor_total = 1 + \
            factores_estructura.get(estructura.lower(), 0) + \
            factores_cubierta.get(cubierta.lower(), 0) + \
            factores_ubicacion.get(ubicacion.lower(), 0)

        precio_total = round(valor_base * factor_total)

        # Paneles
        panel_watt = 580
        numero_paneles = math.ceil(potencia_kwp * 1000 / panel_watt)

        # Valor kWh de la factura
        def extraer_valor_kwh(words):
            for i in range(len(words) - 1):
                actual = words[i]["text"].replace(",", "").strip()
                siguiente = words[i + 1]["text"].replace(",", "").strip()
                try:
                    if actual.isdigit() and float(siguiente) > 200 and len(siguiente.split(".")) == 2 and len(siguiente.split(".")[1]) == 4:
                        valor = float(siguiente)
                        if 300 <= valor <= 2000:
                            return valor
                except:
                    continue
            return None

        valor_kwh = extraer_valor_kwh(page0_words)

        try:
            estrato_int = int(estrato)
        except:
            estrato_int = 0

        aplica_contribucion = estrato_int in [5, 6] or tipo_servicio in ["Comercial", "Industrial"]
        valor_energia = consumo_prom * valor_kwh if valor_kwh else 0
        valor_contribucion = round(0.2 * valor_energia) if aplica_contribucion else 0

        # Generación mensual estimada (ajustada a cobertura)
        generacion_min = round(potencia_kwp * 1300) / 12
        generacion_max = round(potencia_kwp * 1600) / 12

        costo_energia = (valor_kwh or 0) * consumo_prom * 12 + valor_contribucion * 12

        return {
            "nombre": nombre,
            "direccion": direccion,
            "tipo_servicio": tipo_servicio,
            "estrato": estrato,
            "municipio": municipio,
            "consumo_kwh": round(consumo_prom, 2),
            "potencia_kwp": potencia_kwp,
            "numero_paneles": numero_paneles,
            "precio_total": precio_total,
            "valor_kwh": valor_kwh,
            "valor_contribucion": valor_contribucion,
            "generacion_mensual_min": generacion_min,
            "generacion_mensual_max": generacion_max,
            "inversor_utilizado": f"{inversor['modelo']} ({inversor['potencia']} kW)",
            "costo_energia": costo_energia,
            "porcentaje_generacion": pct
        }
