def calcular_cotizacion_proyecto(data):
    valor_factura = data["valor_factura"]
    tipo_instalacion = data["tipo_instalacion"]
    area_disponible = data["area_disponible"]
    tipo_area = data["tipo_area"]

    tarifas = {
        "residencial": 1000,
        "comercial": 900,
        "industrial": 800
    }

    capex_unitario = {
        "residencial": 5000000,
        "comercial": 4000000,
        "industrial": 3000000
    }

    if tipo_instalacion not in tarifas:
        return {"error": "Tipo de instalación no válido"}

    tarifa = tarifas[tipo_instalacion]
    capex_por_kwp = capex_unitario[tipo_instalacion]

    consumo_estimado_kwh = (valor_factura * 12) / tarifa
    potencia_estim_kwp = consumo_estimado_kwh / 1200
    capex_estimado = potencia_estim_kwp * capex_por_kwp
    area_requerida = potencia_estim_kwp * 8

    advertencia = ""
    if area_disponible < area_requerida:
        advertencia = "El área disponible no es suficiente para cubrir el 100% del consumo estimado."

    return {
        "consumo_estimado_kwh": round(consumo_estimado_kwh, 2),
        "potencia_estim_kwp": round(potencia_estim_kwp, 2),
        "capex_estimado": round(capex_estimado),
        "area_requerida": round(area_requerida, 2),
        "advertencia": advertencia,
        "tipo_area": tipo_area
    }