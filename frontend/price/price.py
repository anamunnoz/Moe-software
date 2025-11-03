def calculate_price(pages, color_pages, printing_format, costs):
    if pages <= 0 or color_pages < 0 or color_pages > pages:
        return (0, 0, 0)
    
    rates = exchange_app.get_rates()
    #print(f"Pages: {pages}")
    
    if printing_format == "NORMAL":
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

        # print(
        #     f"printing_cost: {printing_cost}\n"
        #     f"costo_portada_normal: {costo_portada_normal}\n"
        #     f"costo_fijo: {costo_fijo}\n"
        #     f"costo_tapa_normal_CUP: {costo_tapa_normal_CUP}"
        # )

        costo_tapa_normal_usd = costo_tapa_normal_CUP / rates["USD"]
        
        precio_venta_usd_tapa_normal = math.floor(costo_tapa_normal_usd * costs["multiplicador"])

        if precio_venta_usd_tapa_normal < 9:
            precio_venta_usd_tapa_normal = 9
        
        precio_venta_usd_tapa_normal_solapa = precio_venta_usd_tapa_normal + 5
        precio_venta_usd_tapa_dura = precio_venta_usd_tapa_normal + 7

        return (precio_venta_usd_tapa_normal, precio_venta_usd_tapa_normal_solapa, precio_venta_usd_tapa_dura)

    if printing_format == "GRANDE":
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

        # print(
        #     f"printing_cost: {printing_cost}\n"
        #     f"costo_portada_normal: {costo_portada_normal}\n"
        #     f"costo_fijo: {costo_fijo}\n"
        #     f"costo_tapa_normal_CUP: {costo_tapa_normal_CUP}"
        # )

        costo_tapa_normal_usd = costo_tapa_normal_CUP / rates["USD"]
        
        precio_venta_usd_tapa_normal = math.floor(costo_tapa_normal_usd * costs["multiplicador"]*0.8)

        if precio_venta_usd_tapa_normal < 9:
            precio_venta_usd_tapa_normal = 9
        
        #precio_venta_usd_tapa_normal_solapa = precio_venta_usd_tapa_normal + 8
        #precio_venta_usd_tapa_dura = precio_venta_usd_tapa_normal + 10

        #return (precio_venta_usd_tapa_normal, precio_venta_usd_tapa_normal_solapa, precio_venta_usd_tapa_dura)
        return precio_venta_usd_tapa_normal