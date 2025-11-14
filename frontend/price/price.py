from frontend.price.get_rates import convert_to_currency
import math
import requests
from frontend.urls import API_URL_PRODUCTION_COSTS 

def get_costs_from_api():
    response = requests.get(API_URL_PRODUCTION_COSTS)
    response.raise_for_status()
    data = response.json()
    costs = {item['product']: item['product_price'] for item in data}
    return costs

def calculate_price(pages, color_pages, printing_format):
    costs = get_costs_from_api()
    if pages <= 0 or color_pages < 0 or color_pages > pages:
        return 0
    if printing_format == "normal":
        num_hojas_BN = pages / 4
        num_hojas_color = color_pages / 4

        if pages > 500 or color_pages > 500:
            costo_portada_normal = costs["pliego A3"]
        else:
            costo_portada_normal = costs["pliego A3"] / 2  

        printing_cost = float((costs["Imprimir una hoja en BN"] + costs["Precio de una hoja"]) * num_hojas_BN + (costs["Imprimir una hoja en color"] + costs["Precio de una hoja"]) * num_hojas_color)
        costo_fijo = (
            costs["flexibado"] +
            costs["repelado"] + 
            costs["acetato"] + 
            costs["ziplo"] +
            costs["otros costos"] +
            costs["Marcador"] +
            costs["Tarjeta de regalo"]
        )

        costo_tapa_normal_CUP = printing_cost + costo_portada_normal + costo_fijo
        costo_tapa_normal_usd = convert_to_currency(costo_tapa_normal_CUP, 'CUP', 'USD')
        precio_venta_usd_tapa_normal = math.floor(costo_tapa_normal_usd * costs["multiplicador"])


        if precio_venta_usd_tapa_normal < 9:
            precio_venta_usd_tapa_normal = 9

        return precio_venta_usd_tapa_normal

    if printing_format == "grande":
        num_hojas_BN = pages / 2
        num_hojas_color = color_pages / 2

        costo_portada_normal = costs["pliego A3"]  

        printing_cost = float((costs["Imprimir una hoja en BN"] + costs["Precio de una hoja"]) * num_hojas_BN + (costs["Imprimir una hoja en color"] + costs["Precio de una hoja"]) * num_hojas_color)

        costo_fijo = (
            costs["flexibado"] +
            costs["repelado"] + 
            costs["acetato"] + 
            
            costs["otros costos"] +
            costs["Marcador"] +
            costs["Tarjeta de regalo"]
        )
        
        costo_tapa_normal_CUP = printing_cost + costo_portada_normal + costo_fijo
        costo_tapa_normal_usd = convert_to_currency(costo_tapa_normal_CUP, 'CUP', 'USD')

        precio_venta_usd_tapa_normal = math.floor(costo_tapa_normal_usd * costs["multiplicador"]*0.8)

        if precio_venta_usd_tapa_normal < 9:
            precio_venta_usd_tapa_normal = 9
        return precio_venta_usd_tapa_normal
