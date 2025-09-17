import numpy as np
import pandas as pd
from numpy_financial import irr, npv


def safe_value(x, multiplier=1):
    try:
        if x is None:
            return None
        if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
            return None
        return round(x * multiplier, 2)
    except Exception:
        return None


def calcular_payback(flujos):
    acumulado = 0
    for i, f in enumerate(flujos):
        acumulado += f
        if acumulado >= 0:
            return i
    return None


def calcular_flujo_fotovoltaico(data):
    # Inputs
    generacion_inicial = data["generacion_anual_kwh"]
    porcentaje_autoconsumo = data["porcentaje_autoconsumo"]
    consumo_anual_usuario = data["consumo_anual_usuario"]
    precio_compra_kwh = data["precio_compra_kwh"]
    precio_bolsa = data["precio_bolsa"]
    componente_comercializacion = data["componente_comercializacion"]
    capex = data["capex"]
    opex_inicial = data["opex_anual"]
    horizonte_anios = data["horizonte_anios"]
    tasa_descuento = data["tasa_descuento"]
    crecimiento_energia = data["crecimiento_energia"]
    crecimiento_bolsa = data["crecimiento_bolsa"]
    anios_deduccion_renta = min(data["anios_deduccion_renta"], 15)

    # Leasing inputs
    anios_leasing = data.get("anios_leasing", 10)
    tasa_leasing = data.get("tasa_leasing", 0.08)

    # Beneficios tributarios
    depreciacion_total = 0.35 * capex
    depreciacion_anual = depreciacion_total / 3
    deduccion_total_renta = 0.175 * capex
    deduccion_anual_renta = deduccion_total_renta / anios_deduccion_renta

    # Inicialización
    flujos_sin_bt = [-capex]
    flujos_con_bt = [-capex]
    flujos_leasing_sin_bt = [0]
    flujos_leasing_con_bt = [0]

    # Cálculo de cuota leasing
    if tasa_leasing > 0:
        cuota_leasing = capex * (tasa_leasing / (1 - (1 + tasa_leasing) ** (-anios_leasing)))
    else:
        cuota_leasing = capex / anios_leasing

    # Tabla resultados (sin Flujo Neto ni Flujo Acumulado)
    registros = []

    for anio in range(1, horizonte_anios + 1):
        # 📉 Degradación de módulos FV
        generacion_anual_kwh = generacion_inicial * ((1 - 0.005) ** (anio - 1))

        # Precios de energía
        precio_compra_kwh_anio = precio_compra_kwh * (1 + crecimiento_energia) ** (anio - 1)
        precio_bolsa_anio = precio_bolsa * (1 + crecimiento_bolsa) ** (anio - 1)

        # OPEX crece 3% anual
        opex_anual = opex_inicial * ((1.03) ** (anio - 1))

        # Energía autoconsumida y excedentes
        autoconsumo_kwh = generacion_anual_kwh * porcentaje_autoconsumo
        excedente_total = generacion_anual_kwh - autoconsumo_kwh
        cruce_posible = max(consumo_anual_usuario - autoconsumo_kwh, 0)
        excedente1_kwh = min(excedente_total, cruce_posible)
        excedente2_kwh = max(excedente_total - excedente1_kwh, 0)

        # Ingresos
        ingreso_autoconsumo = autoconsumo_kwh * precio_compra_kwh_anio
        ingreso_excedente1 = excedente1_kwh * (precio_compra_kwh_anio - componente_comercializacion)
        ingreso_excedente2 = excedente2_kwh * precio_bolsa_anio
        ingreso_total = ingreso_autoconsumo + ingreso_excedente1 + ingreso_excedente2

        flujo_base = ingreso_total - opex_anual

        # Beneficios
        beneficio_depreciacion = depreciacion_anual if anio <= 3 else 0
        beneficio_renta = deduccion_anual_renta if anio <= anios_deduccion_renta else 0

        # Leasing
        costo_leasing = cuota_leasing if anio <= anios_leasing else 0

        # Flujos
        flujo_sin_bt = flujo_base
        flujo_con_bt = flujo_base + beneficio_depreciacion + beneficio_renta
        flujo_leasing_sin_bt = flujo_base - costo_leasing
        flujo_leasing_con_bt = flujo_base - costo_leasing + beneficio_depreciacion + beneficio_renta

        flujos_sin_bt.append(flujo_sin_bt)
        flujos_con_bt.append(flujo_con_bt)
        flujos_leasing_sin_bt.append(flujo_leasing_sin_bt)
        flujos_leasing_con_bt.append(flujo_leasing_con_bt)

        # Tabla base (sin Flujo Neto ni Flujo Acumulado)
        registros.append({
            "Año": anio,
            "Generación (kWh)": round(generacion_anual_kwh, 0),
            "Tarifa Energía (COP/kWh)": round(precio_compra_kwh_anio, 2),
            "Ingreso Autoconsumo": round(ingreso_autoconsumo, 0),
            "Ingreso Excedente1": round(ingreso_excedente1, 0),
            "Ingreso Excedente2": round(ingreso_excedente2, 0),
            "OPEX": round(opex_anual, 0),
            "Costo Leasing": round(costo_leasing, 0),
            "Beneficio Depreciación": round(beneficio_depreciacion, 0),
            "Beneficio Renta": round(beneficio_renta, 0),
            "Flujo Base": round(flujo_base, 0)
        })

    def indicadores(flujos):
        return {
            "vpn": safe_value(npv(tasa_descuento, flujos)),
            "tir": safe_value(irr(flujos), 100),
            "payback": calcular_payback(flujos)
        }

    return {
        "sin_bt": indicadores(flujos_sin_bt),
        "con_bt": indicadores(flujos_con_bt),
        "leasing_sin_bt": indicadores(flujos_leasing_sin_bt),
        "leasing_con_bt": indicadores(flujos_leasing_con_bt),
        "flujos_sin_bt": flujos_sin_bt,
        "flujos_con_bt": flujos_con_bt,
        "flujos_leasing_sin_bt": flujos_leasing_sin_bt,
        "flujos_leasing_con_bt": flujos_leasing_con_bt,
        "tabla_resultados": registros if registros else []   # ✅ nunca None
    }