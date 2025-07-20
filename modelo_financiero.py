import numpy as np
import pandas as pd
from numpy_financial import irr, npv
import matplotlib.pyplot as plt

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
    anios_deduccion_renta = min(data["anios_deduccion_renta"], 15)  # máximo 15 años

    # Beneficios tributarios
    depreciacion_total = 0.35 * capex
    depreciacion_anual = depreciacion_total / 3
    deduccion_total_renta = 0.175 * capex
    deduccion_anual_renta = deduccion_total_renta / anios_deduccion_renta

    # Energía autoconsumida y excedentes
    autoconsumo_kwh = generacion_anual_kwh * porcentaje_autoconsumo
    excedente_total = generacion_anual_kwh - autoconsumo_kwh
    cruce_posible = max(consumo_anual_usuario - autoconsumo_kwh, 0)
    excedente1_kwh = min(excedente_total, cruce_posible)
    excedente2_kwh = max(excedente_total - excedente1_kwh, 0)

    # Flujo de caja año a año
    flujos_sin_bt = [-capex]
    flujos_con_bt = [-capex]  # en año 0 no se aplica deducción

    for anio in range(1, horizonte_anios + 1):
        precio_compra_kwh_anio = precio_compra_kwh * (1 + crecimiento_energia) ** (anio - 1)
        precio_bolsa_anio = precio_bolsa * (1 + crecimiento_bolsa) ** (anio - 1)

        ingreso_autoconsumo = autoconsumo_kwh * precio_compra_kwh_anio
        ingreso_excedente1 = excedente1_kwh * (precio_compra_kwh_anio - componente_comercializacion)
        ingreso_excedente2 = excedente2_kwh * precio_bolsa_anio

        ingreso_total = ingreso_autoconsumo + ingreso_excedente1 + ingreso_excedente2
        flujo_base = ingreso_total - opex_anual
        flujos_sin_bt.append(flujo_base)

        # Beneficio por depreciación (solo 3 años) + deducción por renta (hasta anio X)
        beneficio_depreciacion = depreciacion_anual if anio <= 3 else 0
        beneficio_renta = deduccion_anual_renta if anio <= anios_deduccion_renta else 0
        flujo_con_bt = flujo_base + beneficio_depreciacion + beneficio_renta
        flujos_con_bt.append(flujo_con_bt)

        if anio == 1:
            ingreso_autoconsumo_anual = ingreso_autoconsumo
            ingreso_excedente1_anual = ingreso_excedente1
            ingreso_excedente2_anual = ingreso_excedente2

    # Indicadores
    vpn = npv(tasa_descuento, flujos_sin_bt)
    tir = irr(flujos_sin_bt)
    vpn_bt = npv(tasa_descuento, flujos_con_bt)
    tir_bt = irr(flujos_con_bt)

    # Payback sin beneficios
    flujo_acumulado = 0
    payback_year = None
    for i, f in enumerate(flujos_sin_bt):
        flujo_acumulado += f
        if flujo_acumulado >= 0:
            payback_year = i
            break

    # Payback con beneficios
    flujo_acumulado_bt = 0
    payback_year_bt = None
    for i, f in enumerate(flujos_con_bt):
        flujo_acumulado_bt += f
        if flujo_acumulado_bt >= 0:
            payback_year_bt = i
            break

    # Gráfica
    anios = list(range(horizonte_anios + 1))
    plt.figure(figsize=(10, 5))
    plt.plot(anios, np.cumsum(flujos_sin_bt), label="Flujo Acumulado sin Beneficios", color="blue")
    plt.plot(anios, np.cumsum(flujos_con_bt), label="Flujo Acumulado con Beneficios", color="green")
    plt.axvline(payback_year, color='red', linestyle='--', label=f"Payback sin BT: Año {payback_year}")
    plt.axvline(payback_year_bt, color='lime', linestyle='--', label=f"Payback con BT: Año {payback_year_bt}")
    plt.xlabel("Año")
    plt.ylabel("Flujo Acumulado ($)")
    plt.title("Flujo de Caja Acumulado con y sin Beneficios Tributarios")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return {
        "vpn_sin_bt": round(vpn, 2),
        "tir_sin_bt": round(tir * 100, 2),
        "vpn_con_bt": round(vpn_bt, 2),
        "tir_con_bt": round(tir_bt * 100, 2),
        "ingreso_total_anual": round(ingreso_autoconsumo_anual + ingreso_excedente1_anual + ingreso_excedente2_anual, 2),
        "autoconsumo_anual": round(ingreso_autoconsumo_anual, 0),
        "excedente1_anual": round(ingreso_excedente1_anual, 0),
        "excedente2_anual": round(ingreso_excedente2_anual, 0),
        "flujos_sin_bt": flujos_sin_bt,
        "flujos_con_bt": flujos_con_bt,
        "payback_year": payback_year,
        "payback_year_con_bt": payback_year_bt,
        "beneficio_depreciacion_anio1": round(depreciacion_anual, 0),
        "beneficio_renta_anio1": round(deduccion_anual_renta, 0),
        "beneficio_total_anio1": round(depreciacion_anual + deduccion_anual_renta, 0),
    }

    
