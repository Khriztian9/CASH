import numpy as np
import pandas as pd
from numpy_financial import irr, npv

def calcular_flujo_fotovoltaico(data):
    # Inputs
    generacion_anual_kwh = data["generacion_anual_kwh"]
    porcentaje_autoconsumo = data["porcentaje_autoconsumo"]
    consumo_anual_usuario = data["consumo_anual_usuario"]
    precio_compra_kwh = data["precio_compra_kwh"]
    precio_bolsa = data["precio_bolsa"]
    componente_comercializacion = data["componente_comercializacion"]
    capex = data["capex"]
    opex_anual = data["opex_anual"]
    horizonte_anios = data["horizonte_anios"]
    tasa_descuento = data["tasa_descuento"]
    crecimiento_energia = data["crecimiento_energia"]
    crecimiento_bolsa = data["crecimiento_bolsa"]

    # Energía autoconsumida y excedentes
    autoconsumo_kwh = generacion_anual_kwh * porcentaje_autoconsumo
    excedente_total = generacion_anual_kwh - autoconsumo_kwh
    cruce_posible = max(consumo_anual_usuario - autoconsumo_kwh, 0)
    excedente1_kwh = min(excedente_total, cruce_posible)
    excedente2_kwh = max(excedente_total - excedente1_kwh, 0)

    # Flujo de caja año a año con crecimiento
    flujos = [-capex]
    for anio in range(1, horizonte_anios + 1):
        precio_compra_kwh_anio = precio_compra_kwh * (1 + crecimiento_energia) ** (anio - 1)
        precio_bolsa_anio = precio_bolsa * (1 + crecimiento_bolsa) ** (anio - 1)

        ingreso_autoconsumo = autoconsumo_kwh * precio_compra_kwh_anio
        ingreso_excedente1 = excedente1_kwh * (precio_compra_kwh_anio - componente_comercializacion)
        ingreso_excedente2 = excedente2_kwh * precio_bolsa_anio

        ingreso_total = ingreso_autoconsumo + ingreso_excedente1 + ingreso_excedente2
        flujos.append(ingreso_total - opex_anual)

    # Indicadores financieros
    vpn = npv(tasa_descuento, flujos)
    tir = irr(flujos)

        # Calcular año de recuperación (cuando el flujo acumulado pasa de negativo a positivo)
    flujo_acumulado = 0
    payback_year = None
    for i, f in enumerate(flujos):
        flujo_acumulado += f
        if flujo_acumulado >= 0:
            payback_year = i
            break

    return {
        "vpn": round(vpn, 2),
        "tir": round(tir * 100, 2),
        "ingreso_total": round(flujos[1] + opex_anual, 2),
        "autoconsumo_kwh": round(autoconsumo_kwh, 2),
        "excedente1_kwh": round(excedente1_kwh, 2),
        "excedente2_kwh": round(excedente2_kwh, 2),
        "flujos": flujos,
        "payback_year": payback_year,

    }
