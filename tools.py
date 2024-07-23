import pandas as pd

def obtenerArchivoOrigen(foto_path):
    """
    Obtiene el archivo original (fuente), basado en el archivo destino listado en el excel.

    Parameters:
    foto_path
    
    Returns:
    str: La ruta del archivo origen.
    """
    #foto_path = "203112-t3.webp"

    segmentos_guion = foto_path.split("-")
    cuantos_segmentos = len(segmentos_guion)
    # print(f"Hay {cuantos_segmentos} en segmentos_guion de la foto {foto_path}")

    # print(f"Presentando el último segmento: {segmentos_guion[cuantos_segmentos-1]}.")

    #Ahora divide por el punto a ese último segmento: 

    division_puntos = segmentos_guion[cuantos_segmentos-1].split(".")

    # print(f"Al que estoy buscando es a éste, el primer segmento: {division_puntos[0]} ")

    quitable = "-" + division_puntos[0]

    resultado_final = foto_path.split(quitable)

    union_final = resultado_final[0] + resultado_final[1]

    print(f"El resultado final es: {union_final} ")

    return union_final

def preparaColumnaImagenes(dataframe, inicial):
    
        #Va todo en un try para que podamos guardar el dataframe en un excel en caso de interrupción del ciclo:
        try: 

            # Filtra las filas donde 'Download Status' es igual a 'Success'
            df_images_ok = dataframe[dataframe['Download Status'] == 'Success']

            # Crea un dataset 'columna_imagenes' a partir de la columna 'Nombre'
            #IMPORTANTE: Aquí si debe ser 'Name' ya que solo tenemos una foto origen (aunq tengamos 4 samples).
            #columna_imagenes = df_images_ok['Name'].unique()
            columna_imagenes = df_images_ok['File']
        
            
            
            #print("Ésta es la columna de imagenes sin repetidos...", columna_imagenes)
                    
            #Si se le pasó el valor como parámetro entonces hace la búsqueda desde donde empezará.
            if inicial is not None: 
                #PROCESO PARA INICIAR DONDE NOS QUEDAMOS
                
                # Ésta es la foto donde iniciará, que se pasa como parámetro a full Process.
                texto_fila_objetivo = inicial  # Replace with your actual search text
                print("El archivo en el que iniciaremos es: ", inicial)
                
                # Create a boolean mask to identify the row matching the text
                mascara_fila_objetivo = df_images_ok['File'].str.contains(texto_fila_objetivo)
                print("Ésto es máscara fila objetivo: ", mascara_fila_objetivo)
                
                # Get the index of the matching row
                indice_fila_objetivo = mascara_fila_objetivo.idxmax()  # Assumes only one match
                print("VIEW: Su índice idmax es: ", indice_fila_objetivo)                
                
                # If the text is found, get the names from that row onward
                #Para cuando llega aquí tenemos que re arreglarle el nombre.
                if indice_fila_objetivo is not None:
                    nombres_a_partir_fila_objetivo = columna_imagenes.iloc[indice_fila_objetivo:]
                    print("Objetivo encontrado: ", nombres_a_partir_fila_objetivo)
                    columna_imagenes = nombres_a_partir_fila_objetivo
                else:
                    # Handle the case where the text is not found (no matching row)
                    print(f"No se encontró la fila con el texto: {texto_fila_objetivo}")
                    print("Esto es nombres_a_partor_fila_objetivo: ", nombres_a_partir_fila_objetivo)
                    #Finalmente vacia las series.
                    nombres_a_partir_fila_objetivo = pd.Series([])  # Empty Series

            contador = 0
            cuantos = len(columna_imagenes)
            
            return columna_imagenes

        except KeyboardInterrupt:
            print("Se interrumpió la creación de la columna")
            