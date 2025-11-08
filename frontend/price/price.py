from price.get_rates import convert_to_currency
import math

def calculate_price(pages, color_pages, printing_format, costs):
    if pages <= 0 or color_pages < 0 or color_pages > pages:
        return 0
    if printing_format == "Normal":
        num_hojas_BN = pages / 4
        num_hojas_color = color_pages / 4

        if pages > 500 or color_pages > 500:
            costo_portada_normal = costs["pliego_A3"]
        else:
            costo_portada_normal = costs["pliego_A3"] / 2  

        printing_cost = float((costs["precio_de_imprimir_1_hoja_BN"] + costs["precio_de_1_hoja"]) * num_hojas_BN + (costs["precio_de_imprimir_1_hoja_Color"] + costs["precio_de_1_hoja"]) * num_hojas_color)
        costo_fijo = (
            costs["flexibado"] +
            costs["repelado"] + 
            costs["acetado"] + 
            costs["ziplo"] +
            costs["otros_costos"] +
            costs["Marcador"] +
            costs["Tarjeta_regalo"]
        )

        costo_tapa_normal_CUP = printing_cost + costo_portada_normal + costo_fijo
        costo_tapa_normal_usd = convert_to_currency(costo_tapa_normal_CUP, 'CUP', 'USD')
        precio_venta_usd_tapa_normal = math.floor(costo_tapa_normal_usd * costs["multiplicador"])


        if precio_venta_usd_tapa_normal < 9:
            precio_venta_usd_tapa_normal = 9

        return precio_venta_usd_tapa_normal

    if printing_format == "Grande":
        num_hojas_BN = pages / 2
        num_hojas_color = color_pages / 2

        costo_portada_normal = costs["pliego_A3"]  

        printing_cost = float((costs["precio_de_imprimir_1_hoja_BN"] + costs["precio_de_1_hoja"]) * num_hojas_BN + (costs["precio_de_imprimir_1_hoja_Color"] + costs["precio_de_1_hoja"]) * num_hojas_color)

        costo_fijo = (
            costs["flexibado"] +
            costs["repelado"] + 
            costs["acetado"] + 
            
            costs["otros_costos"] +
            costs["Marcador"] +
            costs["Tarjeta_regalo"]
        )
        
        costo_tapa_normal_CUP = printing_cost + costo_portada_normal + costo_fijo
        costo_tapa_normal_usd = convert_to_currency(costo_tapa_normal_CUP, 'CUP', 'USD')

        precio_venta_usd_tapa_normal = math.floor(costo_tapa_normal_usd * costs["multiplicador"]*0.8)

        if precio_venta_usd_tapa_normal < 9:
            precio_venta_usd_tapa_normal = 9
        return precio_venta_usd_tapa_normal
