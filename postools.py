import os
import data.data_girls as data_girls
import time
import random
import pretools
import pandas as pd
import gradio_client
import servidor
import nycklar.nodes as nodes
import configuracion
from prompts import Prompt, Superhero, Hotgirl
import prompter
import tools


def creaDirectorioResults(sesion):
    """
    Crea el directorio donde se recibirán los resultados en caso de no existir. El directorio llevará el nombre de la sesión + "results".

    Parameters:
    dataframe (dataframe): El dataframe en el que estuvimos trabajando.

    Returns:
    bool: True si se guardó el archivo correctamente.

    """
    results_dir = os.path.join('imagenes', 'resultados', sesion + "-results" )   
    
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

def preparaDataframe(filename, samples):

    #Primero extraemos el dataframe:
    dataframe = pd.read_excel(filename)
    

    #Después vemos cuales son Success:
    #Filtra las filas donde 'Download Status' es igual a 'Success'
    df_images_ok = dataframe[dataframe['Download Status'] == 'Success']
    

    # Crea una nueva columna 'columna_imagenes' a partir de la columna 'Nombre'
    columna_imagenes = df_images_ok['Name']

    #Crea las rows para sus samples
    for imagen in columna_imagenes:
        #Separa la imagen antes de crearla 4 veces (para no separar cada vez de esas 4)
        nombre, extension = imagen.split(".")       

        #Cuando encuentra la imagen llena los datos de la primera incidencia.
        indice = obtenIndexRow(dataframe, 'Name', imagen)
        dataframe.loc[indice, 'Take'] = 1
        dataframe.loc[indice, 'File'] = nombre + "-" + "t" + str(1) + "." + extension
        
        #Y luego crea tantas rows adicionales como samples fuera a haber.
        for i in range(samples - 1): 
            #Empieza desde el 2 porque ya hizo la 1.
            filename = nombre + "-" + "t" + str(i+2) + "." + extension
            creaRow(dataframe, imagen, i + 2, filename)
    
    #Reordeno alfabéticamente.
    dataframe = dataframe.sort_values(['Name','Take'])

    #Es esto la línea universal para guardar el excel? = Si, si lo es :) 
    pretools.df2Excel(dataframe, configuracion.filename)
      
    return dataframe

def preProcess(sesion, dataframe, inicial=None):
    
    #Destino
    ruta_destino = sesion + "-results"
    target_dir = os.path.join('imagenes', 'resultados', ruta_destino)

    #En caso de no existir el directorio destino, lo creará.
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    #Va todo en un try para que podamos guardar el dataframe en un excel en caso de interrupción del ciclo:
    try: 

        # Filtra las filas donde 'Download Status' es igual a 'Success'
        df_images_ok = dataframe[dataframe['Download Status'] == 'Success']

        # Crea un dataset 'columna_imagenes' a partir de la columna 'Nombre'
        columna_samples = df_images_ok['File']
        
        #Si se le pasó el valor como parámetro entonces hace la búsqueda desde donde empezará.
        if inicial is not None: 
            #PROCESO PARA INICIAR DONDE NOS QUEDAMOS
            
            # Ésta es la foto donde iniciará, que se pasa como parámetro a full Process.
            texto_fila_objetivo = inicial  # Replace with your actual search text
            print("El archivo en el que iniciaremos es: ", inicial)
            
            
            # Create a boolean mask to identify the row matching the text
            mascara_fila_objetivo = df_images_ok['File'].str.contains(texto_fila_objetivo)
            # Get the index of the matching row
            indice_fila_objetivo = mascara_fila_objetivo.idxmax()  # Assumes only one match
            print("Su índice idmax es: ", indice_fila_objetivo)
            
            
            # If the text is found, get the names from that row onward
            if indice_fila_objetivo is not None:
                nombres_a_partir_fila_objetivo = columna_samples.iloc[indice_fila_objetivo:]
                print("Objetivo encontrado: ", nombres_a_partir_fila_objetivo)
               
                columna_samples = nombres_a_partir_fila_objetivo
            else:
                # Handle the case where the text is not found (no matching row)
                print(f"No se encontró la fila con el texto: {texto_fila_objetivo}")
                print("Esto es nombres_a_partor_fila_objetivo: ", nombres_a_partir_fila_objetivo)
                
                #Finalmente vacia las series.
                nombres_a_partir_fila_objetivo = pd.Series([])  # Empty Series

        contador = 0
        cuantos = len(columna_samples)
        print("La cantidad de resultados son: ", cuantos)
        print("Y ésta es la lista total...", columna_samples)
        
        # Recorre cada URL de foto en la columna
        for i, foto_path in enumerate(columna_samples):

            print("Estamos en la imagen: ", foto_path )
            #Future genera su ruta con la función que harás de hacer rutas, para desplegarla en consola de manera informativa.
                                
            #POSICIÓN
            print("Obteniendo la posición...")
            ruta_posicion, shot = getPosition()
            print(f"Ruta_posicion: {ruta_posicion} y shot: {shot}...")
            
            #Creación será el objeto que contiene todos los atributos de lo que vamos a crear.

            #PROMPT PARA CHICA
            creacion = Hotgirl(style="anime")
            prompt = f"A {creacion.style} of a {creacion.adjective} {creacion.type_girl} {creacion.subject} with {creacion.boobs} and {creacion.hair_style} wearing {creacion.wardrobe_top}, {creacion.wardrobe_accesories}, {creacion.wardrobe_bottom}, {creacion.wardrobe_shoes}, {creacion.situacion} at {creacion.place} {creacion.complemento}"           

            #PROMPT PARA HEROE
            # creacion = Superhero()
            # prompt = f"A {creacion.style} of a superhero like {creacion.subject} " #agregar otros atributos random aquí posteriormente.
            
            print("Éstos son los atributos que estamos a punto de guardar en el excel...")
            print(prompt)
           
            #Antes de iniciar el stablediffusion vamos a guardar nuestro registro: 
            print("Entrará a guardarRegistro cada que haya un objeto nuevo...")
            print(f"Estámos entrando con el objeto {creacion}, y la shot {shot}...")
            guardarRegistro(dataframe, foto_path, creacion, shot)

                        
    #La interrupción vía teclado también se deja para que guarde donde iba, 
    #podría parecer irrelevante pero en altas masivas quizá si sería bueno interrumpirla.
    #y tener una prueba antiinterrumpciones.
    except KeyboardInterrupt:
        print("Me quedé en la foto_path: ", foto_path)
        
        # Abrir el archivo configuracion.py en modo append
        with open("configuracion.py", "a") as archivo:
            # Escribir los valores en el archivo
            archivo.write(f"\nfoto_path = '{foto_path}'\n")
        
        print("Interrumpiste el proceso, guardaré el dataframe en el excel, hasta donde ibamos.")
        print("Aquí vamos a guardar el excel porque interrumpí el proceso...")
        #IMPORTANTE: Quizá no se necesita hacer ésta escritura pq si hace la escritura final. Prueba.
        #pretools.df2Excel(dataframe, configuracion.filename)

def fullProcess(sesion, dataframe, samples, inicial=None):
    """
    Ciclo completo de toma de imagen, llevado a HF, guardado en disco y actualización de archivo de Excel.

    Parameters:
    sesion
    dataframe (dataframe): El dataframe en el que estuvimos trabajando.

    Returns:
    bool: True si se guardó el archivo correctamente.
    """
    #Future, que los dataframes sean independientes.
    #Primero extraemos el dataframe:
    #dataframe = pd.read_excel(filename)

    #Origen
    ruta_origen = os.path.join('imagenes', 'fuentes', sesion)    

    #Destino
    ruta_destino = sesion + "-results"
    target_dir = os.path.join('imagenes', 'resultados', ruta_destino)

    #En caso de no existir el directorio destino, lo creará.
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

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
        #print("La cantidad de resultados son: ", cuantos)
               
        #Así solo entrará al cliente una vez y no cada que de vuelta el for.
        client = gradio_client.Client("Moibe/splashmix", hf_token=nodes.splashmix_token)

        # Recorre cada URL de foto en la columna
        for i, foto_path in enumerate(columna_imagenes):

            print(f"El valor de i es: {i} y su tipo es: {type(i)}...")  
            print(f"VIEW: La primer foto con la que estaremos trabajando será: {foto_path} y su tipo es: {type(foto_path)}...")
            time.sleep(1)       

            #Aquí debes darle la correcta original (2.jpg), y no la incorrecta (2-t1.jpg)
            #Como el archivo podría tener otros guiones, el que nos interesa a nosotros es
            source_photo = tools.obtenerArchivoOrigen(foto_path)
            print(f"La source_photo que obtuvimos es: {source_photo} y su tipo es: {type(source_photo)}...")
                                              
            #FOTO
            foto = os.path.join(ruta_origen, source_photo)
            print("La ruta de Foto quedó despues de obtener su original como: ", foto)
            
            #Prepara la imagen para gradio.
            
            imagenSource = gradio_client.handle_file(foto)
            #Poner una excepción aquí para cuando no pudo procesar la imagen como por ejemplo por que no es una imagen.
 
            #Ya no necesito crear el nombre de archivos como t, porque ya es el que tengo, no necesitamos 
            # éste for de hecho.     
            # nombre, extension = foto_path.split(".")
            # filename = nombre + "-t" + str(take) + "." + extension
            # #Obtén el índice de la row que contiene al objeto con el que trabajaremos.
            # print("Éste es el filename que usaremos para obtener el índice...:", filename)
            # print("Ahora si estamos usando el filename...")                        
            
            indice = obtenIndexRow(dataframe, 'File', foto_path) 
            print("El índice de la row u objeto de donde sacaremos los atributos es: ", indice)
                                            
            #Éste contenedor contendrá los atributos que sacó de la respectiva ROW.
            contenedor = prompter.creaContenedor(dataframe, indice)

            print("Esto es el contenedor que me regreso...>")
            print(contenedor)                         

            #AHORA CREA EL PROMPT
            print("Creando prompt después de meterle el contenedor...")
            prompt=prompter.creaPrompt(contenedor)
            
            #Mini proceso para sacar la ruta de la posición. 
            #Future: Ver si lo haces función o lo combinas con getPosition. 
            #O si haces una función creadora de rutas.
            ruta_carpeta = os.path.join("imagenes", "positions\\posiciones")
            #ruta_carpeta = "imagenes\\posiciones"

            lista_archivos = os.listdir(ruta_carpeta)
            
            if not lista_archivos:
                print("La carpeta está vacía o no existe.")
                exit()
            
            imagen_posicion = contenedor['shot']
            ruta_posicion = os.path.join(ruta_carpeta, imagen_posicion)

            print("Ésta es la ruta_posicion que se meterá al cliente de gradio, verifica si es correcta:", ruta_posicion)
                                                    
            imagenPosition = gradio_client.handle_file(ruta_posicion)
            #Poner una excepeción aquí para cuando no pudo procesar la imagen como por ejemplo por que no es una imagen.

            print("Ésto es el prompt obtenido de creaPrompt: ", prompt)
                            
            print("LISTO PARA STABLE DIFFUSION!!!!!")                               

            #STABLE DIFFUSION
            print("Iniciando Stable Difussion...")
            #Los valores ya estarán guardados en el excel, resultado solo reportará si hay imagen o no.
            resultado = stableDiffuse(client, imagenSource, imagenPosition, prompt)
            print("El resultado de predict fue: ", resultado)

            #-->Aquí es donde llegan los breaks cuando la API estaba apagada.
            
            #Aquí cambiaremos a que también pueda regresar PAUSED, que significa que nada adicional se puede hacer.  
            if resultado == "api apagada":
                print("Me quedé en la foto_path: ", foto_path)
                
                with open("configuracion.py", "a") as archivo:
                    # Escribir los valores en el archivo
                    archivo.write(f"\n foto_path = {foto_path}\n")
                                        
                print("La api está apagada, esperando a que reinicie.")
                print("Aquí vamos a guardar el excel, porque se apago la API...")
                
                pretools.df2Excel(dataframe, configuracion.filename)
                configuracion.api_apagada = True
                #Se definirá si esperar a que reinicie o no.
                if configuracion.wait_awake == True: 
                    print("Esperando 500 segundos a que reinicie...")
                    time.sleep(configuracion.wait_time)
                    configuracion.waited = True
                    break #Se va a donde acaba el for de 4.
                else: 
                    
                    configuracion.waited = False
                    break                
            else: 
                print("Se fue al else porque type(resultado) es: ", type(resultado))

            #PROCESO DESPÚES DE QUE YA TERMINÓ EL STABLE DIFUSSE:

            #SI PROCESO CORRECTAMENTE SERÁ UNA TUPLA.        
            if isinstance(resultado, tuple):
                print("Es una tupla: ", resultado)
                print(f"IMPORTANTE: Vamos a guardar el resultado, y la ruta_final o destino es {target_dir} y es del tipo: {type(target_dir)}...")
                
                #Future: guardar Resultado ahora debe pasar el diccionario de atributos y después usarlo adentro en actualiza Row.
                print("Vamos a guardar un resultado existoso:")
                guardarResultado(dataframe, resultado, foto_path, target_dir, 'Completed')

            #NO PROCESO CORRECTAMENTE NO GENERA UNA TUPLA.
            #CORRIGE IMPORTANTE: QUE NO SE SALGA DEL CICLO DE ESA IMAGEN AL ENCONTRAR ERROR.
            else:
                print("No es una tupla: ", resultado)
                print("El tipo del resultado cuando no fue una tupla es: ", type(resultado))
                
                texto = str(resultado)
                segmentado = texto.split('exception:')
                print("Segmentado es una posible causa de error, analiza segmentado es: ", segmentado)
                ###FUTURE: Agregar que si tuvo problemas con la imagen de referencia, agregue en un 
                #Log de errores porque ya no lo hará en el excel, porque le dará la oportunidad con otra 
                #imagen de posición.
                try:
                    #Lo pongo en try porque si no hay segmentado[1], suspende toda la operación. 
                    print("Segmentado[1] es: ", segmentado[1])
                    mensaje = segmentado[1]
                except Exception as e:
                    print("Error en el segmentado: ", e)
                    mensaje = "concurrent.futures._base.CancelledError"
                finally: 
                    pass
                
                print("Si no la pudo procesar, no la guarda, solo actualiza el excel.")
                #Cuando no dio un resultado, la var resultado no sirve y mejor pasamos imagenSource, si no sirviera, ve como asignar la imagen.
                print("Vamos a guardar un resultado no exitoso:")
                
                guardarResultado(dataframe, imagenSource, foto_path, target_dir, mensaje)
                
            print("Salí del if instance...")

                #AQUÍ TERMINA EL PROCESO QUE BIEN PODRÍAMOS REPETIR 4 VECES.

            #Revisa si éste for debería tener un try-except.
            print("Salí del for de 4....")
            #Aquí llega el break si la API estaba apagada, habiendo esperado o no."        
            
            if configuracion.api_apagada == True:
                if configuracion.waited == True: 
                #Si estaba apagada, pero esperó, ya no hagas el segundo break.
                    configuracion.waited = False #Solo regresa a waited al estado normal. (quizá no es necesario pq no llega aquí.)
                else: 
                    #Si estaba apagada y no esperaste, salte totalmente con el segundo break...
                    print("Como el problema fue que la API estaba apagada, volveré a saltar hacia un break.")
                    break
            else:
                #Si la API no estaba apagada, éste es el camino normal.
                contador =+ 1
    except KeyboardInterrupt:
        print("Me quedé en la foto_path: ", foto_path)
        
        # Abrir el archivo configuracion.py en modo append
        with open("configuracion.py", "a") as archivo:
            # Escribir los valores en el archivo
            archivo.write(f"\nfoto_path = '{foto_path}'\n")           
        
        print("Interrumpiste el proceso, guardaré el dataframe en el excel, hasta donde ibamos.")
        print("Aquí vamos a guardar el excel porque interrumpí el proceso...")
        #IMPORTANTE: Quizá no se necesita hacer ésta escritura pq si hace la escritura final. Prueba.
        #pretools.df2Excel(dataframe, configuracion.filename)

def getPosition():
    """
    Regresa una posición del cuerpo humano para ser utilizada por el proceso de Stable Diffusion.

    Parameters:
    dataframe (dataframe): El dataframe en el que estuvimos trabajando.

    Returns:
    bool: True si se guardó el archivo correctamente.

    """
    #FUTURE: Aquí se podrá poner dinámicamente el set de posiciones en el subfolder de la carpeta posiciones.
    ruta_carpeta = os.path.join("imagenes", "positions\\posiciones")
    #ruta_carpeta = "imagenes\\posiciones"

    lista_archivos = os.listdir(ruta_carpeta)
    
    if not lista_archivos:
        print("La carpeta está vacía o no existe.")
        exit()

    #Selecciona una imagen aleatoriamente.
    imagen_aleatoria = random.choice(lista_archivos)
    posicion_actual = os.path.join(ruta_carpeta, imagen_aleatoria)

    print("Ruta Posicion o posicion_actual: ", posicion_actual)
    
    nombre_archivo = os.path.basename(posicion_actual)
    
    #shot, extension = nombre_archivo.split(".")
    #Ahora si necesitamos la extensión: 
    shot = nombre_archivo
    
    print("Posición elegida: ", shot)
        
    return posicion_actual, shot

def stableDiffuse(client, imagenSource, imagenPosition, prompt):
    
    #Los dos iguales.
    #Revisar si se puede subir el hf_token.

    #Hacer primer contacto con API, ésto ayudará a saber si está apagada y prenderla automáticamente.

    try:
        #Usando Moibe Splashmix
        print("Estoy adentro, donde se usaba el cliente...")
        #client = gradio_client.Client("Moibe/splashmix", hf_token=nodes.splashmix_token)


    except Exception as e:
        print("API apagada o pausada...", e)
        print("Revisar si el datafame está vivo a éstas alturas...:", )
    
        #Analiza e para definir si está apagada o pausada, cuando está pausada, no debes esperar pq nada cambiará.
        #Si e tiene la palabra PAUSED.
        print("Reiniciandola, vuelve a correr el proceso en 10 minutos.")
        print("ZZZZZZZ")
        print("ZZZZZZZ")
        print("ZZZZZZZ")
        #No podemos hacer break porque no es un loop.
        #Por eso hago un return para que se salga de stablediffuse.
        return "api apagada" # o regresa api pausada.
    
    #Ahora correr el proceso central de Stable Diffusion.
    try:

        print("Ahora estoy ya en el predict...")
        
        result = client.predict(
                imagenSource,
                imagenPosition,
                prompt=prompt,
                negative_prompt="(lowres, low quality, worst quality:1.2), (text:1.2), watermark, (frame:1.2), deformed, ugly, deformed eyes, blur, out of focus, blurry, deformed cat, deformed, photo, anthropomorphic cat, monochrome, pet collar, gun, weapon, blue, 3d, drones, drone, buildings in background, green",
                style_name="(No style)", #ver lista en styles.txt
                num_steps=30,
                identitynet_strength_ratio=0.8,
                adapter_strength_ratio=0.8,
                pose_strength=0.4,
                canny_strength=0.4,
                depth_strength=0.4,
                controlnet_selection=["pose"], #pueden ser ['pose', 'canny', 'depth']
                guidance_scale=5,
                #seed=43,
                seed=42, #Wow deje una seed fija desde siempre, por eso con las mismas características creará lo mismo. Está bien!
                scheduler="EulerDiscreteScheduler",
                enable_LCM=False,
                enhance_face_region=True,
                api_name="/generate_image"
        )
        return result

    except Exception as e:
        print("Hubo un error, recuerda éste prompt...", e)
        print("Aquí llega cuando la imagen no existe, no cuando no se pudo procesar, revisar si eso llega al excel, la e sería: ", e)
        #No está llegando al excel, pero no es necesario porque cuando se sale llega a la línea: 364
        print("XXXXX")
        print("XXXXX")
        print("XXXXX")
        return e

def guardarRegistro(dataframe, foto_dir, creacion, shot):
    """
    Guarda el registro de lo que se va a hacer en excel.

    Parameters:
    dataframe (dataframe): El dataframe en el que estuvimos trabajando.
    result
    foto_dir
    take
    shot
    estilo
    ruta_final
    message: el mensaje textual que irá en la columna stable diffusion: si fue error el error, si no: Image Processed.

    Returns:
    bool: True si se guardó el archivo correctamente.
    """

    # nombre, extension = foto_dir.split(".")
    # filename = nombre + "-" + "t" + str(take) + "." + extension

    print("Ya dentro de guardar registro repasaremos cada atributo de la creación:")
    
    #Después cada atributo
    for nombre_atributo in dir(creacion):
        # Verificar si el nombre es un atributo real
        if not nombre_atributo.startswith("__"):
            valor_atributo = getattr(creacion, nombre_atributo)
            print(f"Atributo: {nombre_atributo}, Valor: {valor_atributo}")
            
            
            #File es la columna donde busca, filename lo que está buscando, nombre_atributo la col donde guardará y valor lo que guardará.
            actualizaRow(dataframe, 'File', foto_dir, nombre_atributo, valor_atributo)

    #Y al final el shot: 
    actualizaRow(dataframe, 'File', foto_dir, 'Shot', shot)

    #Es esto la línea universal para guardar el excel? = Si, si lo es :) 
    pretools.df2Excel(dataframe, configuracion.filename)

      
def guardarResultado(dataframe, result, filename, ruta_final, message):
    """
    Guarda el resultado con una nomenclatura específica. Y lo guarda en disco.

    Parameters:
    dataframe (dataframe): El dataframe en el que estuvimos trabajando.
    result
    foto_dir
    take
    shot
    estilo
    ruta_final
    message: el mensaje textual que irá en la columna stable diffusion: si fue error el error, si no: Image Processed.

    Returns:
    bool: True si se guardó el archivo correctamente.
    """
    
    #Aquí guardará la imagen.
    #Ésta parte solo debe hacerla si no viene de error. 

    print("HOY: Estamos en guardar Resultado, y el mensaje que recibimos como parámetro es: ", message)
    ruta_total = ""
    ruta_absoluta = ""

    if message == "Completed":
        #ENTONCES SI HAY UNA IMAGEN QUE GUARDAR EN DISCO DURO.
        
        ruta_total = os.path.join(ruta_final, filename)
        print("El resultado del SD fue exitoso, y su ruta total es/será: ", ruta_total)
        raiz_pc = os.getcwd()
        ruta_absoluta = os.path.join(raiz_pc, ruta_total)
        print("La ruta absoluta es desde donde le podré dar click desde el excel...", ruta_absoluta)
                
        ruta_imagen_local = result[0] 
        print("La ruta de gradio en result[0] es: ", ruta_imagen_local)
        
        #IMPORTANTE, GUARDANDO EN DISCO DURO.
        with open(ruta_imagen_local, "rb") as archivo_lectura:
            contenido_imagen = archivo_lectura.read()	

        with open(ruta_total, "wb") as archivo_escritura:
            archivo_escritura.write(contenido_imagen)
            print(f"Imagen guardada correctamente en: {ruta_total}")
            print("Estamos por actualizar excel...")
            
    #FUTURE: Ésto se tiene que hacer dinámicamente.

    #Después, haya o no guardado en disco duro, registrará que terminó en el excel.

    #actualiza Row actualiza una sola row.
    print("Estoy por actualizarRow y el mensaje es:", message)
    print("y su filename (índice) es: ", filename)
    
    #Sin problema ya puede actualizar el respectivo DiffusionStatus porque siempre está presente.
    actualizaRow(dataframe, 'File', filename, 'Diffusion Status', message)      
    actualizaRow(dataframe, 'File', filename, 'Direccion', ruta_absoluta)

    #Es esto la línea universal para guardar el excel? = Si, si lo es :) 
    pretools.df2Excel(dataframe, configuracion.filename)


def creaRow(dataframe, imagen, take, filename):    

    #Aquí en lugar de len(dataframef) abía un -1 y por eso hacia también las dos líneas comentadas de abajo.
    dataframe.loc[len(dataframe)] = [imagen, 'Success', take, filename, ""]  #adding a row
    # dataframe.index = dataframe.index + 1  #shifting index
    # dataframe = dataframe.sort_index()  # sorting by index

def obtenIndexRow(dataframe, deColumna, indicador):
       
    print(f"El nombre de la imagen buscada es: ")
    index = dataframe[dataframe[deColumna] == indicador].index
    print("Esto es index: ", index)
    print("y ésto es el tipo de index: ", type(index))

    return index



def actualizaRow(dataframe, index_col, indicador, receiving_col, contenido): 
    """
    Función general que recibe una columna indice y una columna receptora para actualizar la información.

    Parameters:
    archivo (str): Contenido que será agregado a esa celda.

    Returns:
    dataframe:Regresa dataframe.
    """

    print("Estoy en actualiza row...")
    print(f"El indicador es: {indicador}")
    
        
    #Recibe el dataframe, el nombre y en que columna buscará, regresa el index.
    index = obtenIndexRow(dataframe, 'File', indicador)
    print(f"El indice obtenido es: {index}")
        
    print("Y la receiving_col es: ", receiving_col)
    
        
    # If the value exists, get the corresponding cell value
    if not index.empty:
        print("El index se encontró...")
                
        cell_value = dataframe.loc[index[0], index_col]  # Get the value at the first matching index
        print(f"Valor de la celda que coincide: {cell_value}")        

        print("Para la revisión de Warning, valor de contenido es: ", contenido)
        print("y tipo de contenido es: ", type(contenido))
                       
        print(f"Voy a guardar en el index de éste indicador: {indicador} en ésta colúmna: {receiving_col}")
        dataframe.loc[index, receiving_col] = contenido
       
    else:
        print("No se encontró la celda coincidente.")   
           

def subirTodo(dataframe, sesion, foto_complete_url_dir):

    print("Entramos a subir todo, la sesión es: ", sesion)

    #Conexión al servidor.
    ssh, sftp = servidor.conecta()
        
    #Define ruta de la carpeta remota
    carpeta_remota = nodes.avaimentekijä
    print(f"La carpeta remota es: {carpeta_remota} y su tipo es: {type(carpeta_remota)}.")
    directorio_receptor = carpeta_remota + sesion
    print(f"El directorio receptor será entonces: {directorio_receptor} y su tipo es: {type(directorio_receptor)}")
    
    #Define ruta de la carpeta local donde se encuentran los resultados.
    carpeta_local = 'imagenes\\resultados\\' + sesion + '-results'

    #Subir el resultado al servidor y esperar respuesta que se guardará en la var resultado.
    resultado = servidor.sube(sftp, dataframe, carpeta_local, directorio_receptor, foto_complete_url_dir)
    #Checar si aquí tendría que regresar el dataframe para tener sus modificaciones.
    print(resultado)

    servidor.cierraConexion(ssh, sftp)

    return dataframe