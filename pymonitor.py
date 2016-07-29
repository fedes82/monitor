#!/usr/local/bin/python
#kivy imports
from kivy.app import App
from kivy.lang import Builder
from kivy.cache import Cache
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition
from kivy.uix.image import Image
from kivy.properties import ListProperty
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.properties import BooleanProperty
from kivy.properties import BoundedNumericProperty
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.core.image import Image as MemImage
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior

#PIL imports
from PIL import Image as PILImage
from PIL import ImageFont as PILImageFont
from PIL import ImageDraw as PILImageDraw

#watchdog -- monitores - imports
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler  

#para el gps
import gps

#general - imports
import socket
import io
from time import sleep
import atexit
from os import remove 
from os import system
from os import makedirs
from os import listdir
import shutil
import time
import os.path
import datetime
import StringIO
import threading
import Queue
import multiprocessing as mp
import struct
import json
import copy
import textwrap
import subprocess
from functools import partial
from tendo import singleton

me = singleton.SingleInstance()




### ESTO NO SE SI HACE FALTA, ES POR LAS DUDAS, PARA USAR TODOS LOS 
### NUCLEOS, VEREMOS CUANDO TERMINE
system("taskset -p 0xff %d" % os.getpid())
####
####

###----------------------------------------CONSTANTES
Window.maximize()

metros = StringProperty('inicial-metros')
datoGps= StringProperty('inicial-gps') 
velocidad = StringProperty('inicial_velocidad')

def actualizar_datos(q,mostrar_metros,mostrar_progreso,mostrar_velocidad):
    """Actualiza los datos mostrados en el GUI cuando opera"""
    while True:
        metros = q.get()
        if metros == 'salir':
            return
        mostrar_metros.text = metros+'m'
        progreso = q.get()
        mostrar_progreso.text = str(int(metros)+int(progreso))+'m'
        velocidad = q.get()
        mostrar_velocidad.text =velocidad[:5]+'Km/h'
        
###------------------


#CONSTANTES
PUERTO_IMAGEN= 20000
PUERTO_TRIGGER = 21000
PUERTO_METROS = 11112
PUERTO_ENCODER = 22000

IP_CAM1 = '10.42.0.3'
IP_CAM2 = '10.42.0.4'
IP_CAM3 = '10.42.0.5'

#constantes operar
CARPETA_SESIONES = '/home/monitoreo/Escritorio/SESIONES/'
CARPETA_FOTOS_TEMPORAL = 'Cam1_almacen/'

#constante configuracion
SIN_CONEXION = 'img_default/error-conexion.jpg'

#  constantes diagnostico
CONEXION_OK = 'img_default/ok.png'
CONEXION_FAIL = 'img_default/fail.png'
ENCODER_DIAGNOSTICO = 'temporales/metros_diagnostico.txt'
### constantres revisador
CARPETA_SESION_FOTOS = 'fotelis/'
CARPETA_TEMPORAL = 'temporales/'
CARPETA_BANDERAS = 'banderas/'
IMG_DEFAULT = 'img_default/imgDefault.jpg'
COMENTARIO = 'comentario.txt'

#globales revisador
DEBUG = True
print('Comenzo el revisador')
archivos_cam1 = []
archivos_cam2 = []
archivos_cam3 = []
indices_marcas = []
comentario = ''




###--------------------------------------------------FOTOGRAFO
def fotografo(operador, ruta, sentido, progreso, q_mostrar_datos):
    #global metros
    global datoGps
    con_cam1 = imgcam()
    con_cam2 = imgcam()
    con_cam3 = imgcam()
    con_cam1,con_cam2,con_cam3 = checkear_conexiones(con_cam1,con_cam2,con_cam3)
    try:
    #CREO CONEXION CON METROS, O SEA , EL ENCODER
        conexion_metros = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print 'Failed to create socket metros. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
        sys.exit();
    while True:
        if not conexion_metros.connect_ex((IP_CAM1,PUERTO_METROS)):
            print 'conexion_metros OK'
            break
        else:
            print 'no conecte conexion metros'
            sleep(0.5)
    #CREO CONEXION trigger CON Camaras
    try:#---CAMARA1
        conexion_TRIGGER_cam1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print 'Failed to create socket camara. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
        sys.exit();
    while True:
        if not conexion_TRIGGER_cam1.connect_ex((IP_CAM1, PUERTO_TRIGGER)):
            print 'conexion_TRIGGER cam1 OK'
            break
        else:
            print 'no conecte conexion_TRIGGER cam1'
            sleep(0.5)
    if con_cam2:
        try:#---CAMARA2
            conexion_TRIGGER_cam2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            print 'Failed to create socket camara. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
            sys.exit();
        while True:
            if not conexion_TRIGGER_cam2.connect_ex((IP_CAM2, PUERTO_TRIGGER)):
                print 'conexion_TRIGGER cam 2 -OK '
                break
            else:
                print 'no conecte conexion_TRIGGER cam2'
                sleep(0.5)
    else:
        shutil.copy(SIN_CONEXION,'temporales/c2.jpg')
    if con_cam3:
        try:#---CAMARA3
            conexion_TRIGGER_cam3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            print 'Failed to create socket camara. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
            sys.exit();
        while True:
            if not conexion_TRIGGER_cam3.connect_ex((IP_CAM3, PUERTO_TRIGGER)):
                print 'conexion_TRIGGER cam 3 -OK '
                break
            else:
                print 'no conecte conexion_TRIGGER cam3'
                sleep(0.5)
    else:
        shutil.copy(SIN_CONEXION,'temporales/c3.jpg')
    q_cam1 = mp.Queue()
    if con_cam2:
        q_cam2 = mp.Queue()
    if con_cam3:
        q_cam3 = mp.Queue()
    #Creo el proceso procesador, en la version final son 3 procesos
    procesador_cam1 = mp.Process(target=ProcesadorFotos, args=(q_cam1, operador, ruta, sentido , progreso,IP_CAM1,'c1'))
    procesador_cam1.start()
    if con_cam2:
        procesador_cam2 = mp.Process(target=ProcesadorFotos, args=(q_cam2, operador, ruta, sentido , progreso,IP_CAM2,'c2'))
        procesador_cam2.start()
    if con_cam3:
        procesador_cam3 = mp.Process(target=ProcesadorFotos, args=(q_cam3, operador, ruta, sentido , progreso,IP_CAM3,'c3'))
        procesador_cam3.start()
    
###-------------Primer foto
    conexion_TRIGGER_cam1.sendall('foto'.ljust(15,'#'))
    if con_cam2:
        conexion_TRIGGER_cam2.sendall('foto'.ljust(15,'#'))
    if con_cam3:
        conexion_TRIGGER_cam3.sendall('foto'.ljust(15,'#'))
    #parseo datos del encoder
    metros = '0'
    velocidad = '0'
    #mando datos a los procesadores de fotos de cada cam
    q_cam1.put(metros)
    q_cam1.put(datoGps)
    q_cam1.put(velocidad)
    if con_cam2:
        q_cam2.put(metros)
        q_cam2.put(datoGps)
        q_cam2.put(velocidad)
    if con_cam3:
        q_cam3.put(metros)
        q_cam3.put(datoGps)
        q_cam3.put(velocidad)
    #muestro los datos en la gui
    q_mostrar_datos.put(metros)
    q_mostrar_datos.put(progreso)
    q_mostrar_datos.put(velocidad)
###----------------------------------Loop principal
    while True:
        dato = conexion_metros.recv(512)
        print 'recibi dato: ',dato
        if dato == 'salir' or dato == '':
            conexion_metros.shutdown(2)
            conexion_metros.close()
            print 'se cerro la conexion metros'
            break
        #envio orden de fotografiar
        conexion_TRIGGER_cam1.sendall('foto'.ljust(15,'#'))
        if con_cam2:
            conexion_TRIGGER_cam2.sendall('foto'.ljust(15,'#'))
        if con_cam3:
            conexion_TRIGGER_cam3.sendall('foto'.ljust(15,'#'))
        #parseo datos del encoder
        metros = dato.partition('m')[2].partition('v')[0]
        velocidad = dato.partition('v')[2].partition('s')[0]
        #mando datos a los procesadores de fotos de cada cam
        q_cam1.put(metros)
        q_cam1.put(datoGps)
        q_cam1.put(velocidad)
        if con_cam2:
            q_cam2.put(metros)
            q_cam2.put(datoGps)
            q_cam2.put(velocidad)
        if con_cam3:
            q_cam3.put(metros)
            q_cam3.put(datoGps)
            q_cam3.put(velocidad)
        #muestro los datos en la gui
        q_mostrar_datos.put(metros)
        q_mostrar_datos.put(progreso)
        q_mostrar_datos.put(velocidad)
    q_mostrar_datos.put('salir')
    #cierro conexion trigger con camaras
    conexion_TRIGGER_cam1.sendall('salir'.ljust(15,'#'))
    conexion_TRIGGER_cam1.shutdown(2)
    conexion_TRIGGER_cam1.close()
    if con_cam2:
        conexion_TRIGGER_cam2.sendall('salir'.ljust(15,'#'))
        conexion_TRIGGER_cam2.shutdown(2)
        conexion_TRIGGER_cam2.close()
    if con_cam3:
        conexion_TRIGGER_cam3.sendall('salir'.ljust(15,'#'))
        conexion_TRIGGER_cam3.shutdown(2)
        conexion_TRIGGER_cam3.close()
    print 'se cerro la conexion camara'
    procesador_cam1.join()
    if con_cam2:
        procesador_cam2.join()
    if con_cam3:
        procesador_cam3.join()

def ProcesadorFotos( q, operador, ruta, sentido, progreso,ip, camara):

    socket_imagen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_imagen.connect((ip, PUERTO_IMAGEN))
    conexion_imagen = socket_imagen.makefile('wrb')
    while True:
        ###---------recivo imagen por socket
        image_len = struct.unpack('<L', conexion_imagen.read(struct.calcsize('<L')))[0]
        #condicion de salida, la genera la camara enviando un mensaje vacio
        if not image_len:
            break
        # Construct a stream to hold the image data and read the image
        # data from the connection
        image_stream = io.BytesIO()
        image_stream.write(conexion_imagen.read(image_len))
        # Rewind the stream, open it as an image with PIL and do some
        # processing on it
        image_stream.seek(0)
        ###----------tomo datos de la queue
        metros = q.get()
        datoGps = q.get()
        velocidad = q.get()
        ts = time.time()
        ###----------proceso imagen
        img = PILImage.open(image_stream)
        draw = PILImageDraw.Draw(img)
        # font = ImageFont.truetype(<font-file>, <font-size>)
        font = PILImageFont.truetype('UbuntuMono-B.ttf',45)
        # draw.text((x, y),"Sample Text",(r,g,b))
        #draw.text((2, 1),"Operador: "+operador,(255,0,0),font=font)
        #draw.text((2, 1),"Fecha-Hora: "+datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y_%Hh%Mm%S.%fs').rstrip('0'),(255,0,0),font=font) tiene segundos con decimales
        draw.text((2, 1),"Fecha-Hora: "+datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y_%Hh%Mm%Ss').rstrip('0'),(255,0,0),font=font)
        draw.text((2, 50),"Ruta: "+ruta,(255,0,0),font=font)
        draw.text((960, 50),"Sentido: "+ sentido,(255,0,0),font=font)
        draw.text((2, 100),"Distancia Parcial: %07dm"%int(metros),(255,0,0),font=font)
        draw.text((960, 100),"Distancia Total: %07dm"%(int(metros) + int(progreso)),(255,0,0),font=font)
        draw.text((2, 150),"GPS: "+datoGps,(255,0,0),font=font)
        draw.text((960, 150),"Velocidad: " + velocidad[:5],(255,0,0),font=font)
        # NOMBRE VIEJO
        #img.save("Cam1_almacen/"+camara+"_"+'_%06dm'%int(metros)+'__'+ruta+"__"+sentido+"_"+datetime.datetime.fromtimestamp(ts).strftime('%Y_%m_%d_%Hh%Mm%S.%fs').rstrip('0')+"_GPS_"+datoGps+".jpg",quality=95)   
        img.save("Cam1_almacen/"+'%06dm'%int(metros)+'__'+camara+'__'+ruta+"__"+sentido+"_"+datetime.datetime.fromtimestamp(ts).strftime('%Y_%m_%d_%Hh%Mm%S.%fs').rstrip('0')+"_GPS_"+datoGps+".jpg",quality=95)   
        img.save('temporales/'+camara+'.jpg',quality=95)
    conexion_imagen.close()
    print 'cierro proceso procesador fotos'

####-------------------------------------------FIN FOTOGRAFO


######--------GPS

def LectorGPS(queue, evento):
    """ Crea la conexion con el GPS y le pide los datos
        toma el dato de posicion y lo escribe en la 
        queue que despues lee el programa que lo llamo
    """
    try:
        sesion = gps.gps("localhost", "2947")
        sesion.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
        while True:
            if evento.is_set():
                return
            try:
                reporte = sesion.next()
                    #espera un reporte TPV que no se que es y
                    #muestra la hora actual. Para ver el reporte
                    #completo, descomentar la sig linea
                #print reporte
                if reporte['class'] == 'TPV':
                    if hasattr(reporte, 'time') :
                       # print reporte.time
                        pass
                    #if hasattr(reporte,'lat'):
                    #    print 'Latitud: ',reporte.lat
                    #if hasattr(reporte,'lon'):
                    #    print 'Longitud: ',reporte.lon
                    if hasattr(reporte,'lon') and hasattr(reporte,'lat'):
                    #    datoGPS = (str(reporte.lat)+','+str(reporte.lon))
                        queue.put((str(reporte.lat)+','+str(reporte.lon)))
                        #print datoGPS
                    else:
                     #   datoGPS = ('NO-GPS-DATA')
                        queue.put('NO-GPS-DATA')
                        #print datoGps
            except KeyError:
                pass
            except KeyboardInterrupt:
                quit()
            except StopIteration:
                sesion = None
                print 'Termino la ejecucion de GPSD'
    except:
        queue.put('GPS-NO-CONECTADO')

###----------FIN GPS


#####--------------CHECKEO DE CONEXION - HACE PINGS A LAS RASPIS

class imgcam():
    """Clase boluda vacia que solo sirve para ver que devuelve el 
    checkeador de cnexiones xcon pings"""
    source =''

def checkear_conexiones(imgcam1,imgcam2,imgcam3, *largs):
    """ Envia un ping a cada camara y espera el resultado, es 0 si el ping fue
    exitoso y  != 0 si no fue exitoso. Muestra dibujitos acorde a eso
    """
    muerto1  = subprocess.Popen( ['ping', '-c 1', '-W 1' ,IP_CAM1] ,stdout=open('/dev/null', 'w'))
    muerto2  = subprocess.Popen( ['ping', '-c 1', '-W 1' ,IP_CAM2] ,stdout=open('/dev/null', 'w'))
    muerto3  = subprocess.Popen( ['ping', '-c 1', '-W 1' ,IP_CAM3] ,stdout=open('/dev/null', 'w'))
    muerto1.communicate()
    muerto2.communicate()
    muerto3.communicate()
    if not muerto1.returncode:
        imgcam1.source = CONEXION_OK
    else:
        imgcam1.source = CONEXION_FAIL
    if not muerto2.returncode:
        imgcam2.source = CONEXION_OK
    else:
        imgcam2.source = CONEXION_FAIL
    if not muerto3.returncode:
        imgcam3.source = CONEXION_OK
    else:
        imgcam3.source = CONEXION_FAIL
    return imgcam1.source == CONEXION_OK,imgcam2.source == CONEXION_OK,imgcam3.source == CONEXION_OK

####---- FIN CHECKEO CONEXION



################################################################
### INTERFAZ GRAFICA
class IntInput(TextInput):
    """Como textInput, pero solo permite ingresar numeros del 0 al 9"""
    def insert_text(self, substring,from_undo=False):
        """esto hace el filtro de enteros"""
        #print type(substring), substring
        if substring in ['1','2','3','4','5','6','7','8','9','0']:
            return super(IntInput,self).insert_text(substring, from_undo=from_undo)

class TxtInput(TextInput):
    """Como textInput pero solo permite letras 
    numeros y espacios, los que reemplaza por '_' ."""
    def insert_text(self, substring,from_undo=False):
        """esto hace el filtro de enteros"""
        #print type(substring), substring
        if substring == ' ':
            return super(TxtInput,self).insert_text('_', from_undo=from_undo)
        if substring.lower() in 'abcdefghijklmnopqrstuvwxyz0123456789':
            return super(TxtInput,self).insert_text(substring, from_undo=from_undo)

class Apagar_reiniciar_popup(BoxLayout):
    reiniciar= ObjectProperty(None)
    apagar = ObjectProperty(None)
    cancelar = ObjectProperty(None)

class MemoryImage(Image):
    """Display an image already loaded in memory."""
    memory_data = ObjectProperty(None)

    #def __init__(self, memory_data, **kwargs):
        #super(MemoryImage, self).__init__(**kwargs)

        #self.memory_data = memory_data

    def on_memory_data(self, *args):
        """Load image from memory."""
        data = StringIO.StringIO(self.memory_data)
        #data = io.BytesIO(self.memory_data)
        with self.canvas:
            self.texture = ImageLoaderPygame(data).texture

class Pantalla_Inicio(Screen):
    checkcam1 = ObjectProperty(None)
    checkcam2 = ObjectProperty(None)
    checkcam3 = ObjectProperty(None)
    
    def comprobar_conexiones(self):
        checkear_conexiones(self.checkcam1,self.checkcam2,self.checkcam3)
        

class Pantalla_Conf_Operar(Screen):
    operador = ObjectProperty()
    ruta = ObjectProperty()
    sentido = ObjectProperty()
    progreso = ObjectProperty()
    adv = ObjectProperty()
    #observaciones = ObjectProperty()
    
  #  def actualizar_datos(self,op,):
  #      self.

class Pantalla_Apagar_Camaras(Screen):
    l_apagar = ObjectProperty()
    

class Elegir_sesion(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class ImageButton(ButtonBehavior, Image):
    pass


class Pantalla_Revisar(Screen):
    #pass
    btn_playpausa = ObjectProperty()
    velocidad = ObjectProperty()
    comentario = ObjectProperty()
    img1 = ObjectProperty()
    img2 = ObjectProperty()
    img3 = ObjectProperty()
    
    DEBUG = True
    print('Comenzo el revisador')
    archivos_cam1 = []
    archivos_cam2 = []
    archivos_cam3 = []
    indices_marcas = []
    indice = 0
    estado = 'MANUAL'
    
    def crear_fullscreens(self,*largs):
        self.img1_fullscreen = ImageButton(source = self.img1.source, on_release = self.ocultar_pantalla_completa_img1)
        self.img2_fullscreen = ImageButton(source = self.img2.source, on_release = self.ocultar_pantalla_completa_img2)
        self.img3_fullscreen = ImageButton(source = self.img3.source, on_release = self.ocultar_pantalla_completa_img3)
        print 'entre en build'
        
    def mostrar_pantalla_completa_img1(self,*largs):
        self.add_widget(self.img1_fullscreen)
    
    def mostrar_pantalla_completa_img2(self,*largs):
        self.add_widget(self.img2_fullscreen)
    
    def mostrar_pantalla_completa_img3(self,*largs):
        self.add_widget(self.img3_fullscreen)
    
    def ocultar_pantalla_completa_img1(self, *largs):
        self.remove_widget(self.img1_fullscreen)
        
    def ocultar_pantalla_completa_img2(self, *largs):
        self.remove_widget(self.img2_fullscreen)
    
    def ocultar_pantalla_completa_img3(self, *largs):
        self.remove_widget(self.img3_fullscreen)
    def on_exit(self):
        Clock.unschedule(self.siguiente)
        self.estado = 'MANUAL'
        self.btn_playpausa.text = 'PLAY'
    
    def borrar_temporales(self,*largs):
        """borra los temporales con la imagen default
            que se pueden haber usado para rellenar las listas 
            de archivos
        """
        if os.path.exists(CARPETA_SESION_FOTOS+IMG_DEFAULT):
            os.remove(CARPETA_SESION_FOTOS+IMG_DEFAULT)
        if os.path.exists(CARPETA_SESION_FOTOS+IMG_DEFAULT):
            os.remove(CARPETA_SESION_FOTOS+IMG_DEFAULT)
        if os.path.exists(CARPETA_SESION_FOTOS+IMG_DEFAULT):
            os.remove(CARPETA_SESION_FOTOS+IMG_DEFAULT)
    
    def play(self):
        if self.estado == 'MANUAL':
            if self.velocidad.text == '':
                vel = 500
            else:
                vel=int(self.velocidad.text)
            Clock.schedule_interval(self.siguiente, vel/1000.0)
            self.estado = 'AUTOMATICO'
            self.btn_playpausa.text = 'STOP'
        else:
            Clock.unschedule(self.siguiente)
            self.estado = 'MANUAL'
            self.btn_playpausa.text = 'PLAY'
        pass
    

    def rellenar_lista(self):
        """Rellena la lista de archivos cuando alguna lista tiene menos que otras
            tambien copia los repetidos
            Los nuevos que pone, les pone nombre cortos, con los metros para que 
            queden acomodados y terminando en FALTA para identificarlos
        """
        cam1 = []
        cam2 = []
        cam3 = []
        print 'entre a relllenar_lista'
        #print cam1
        #print self.archivos_cam1
        for archivo in self.archivos_cam1:
            print archivo[0:6]
            print int(archivo[0:6])
            cam1.append(int(archivo[0:6]))
        
        for archivo in self.archivos_cam2:
            cam2.append(int(archivo[0:6]))
        
        for archivo in self.archivos_cam3:
            cam3.append(int(archivo[0:6]))
        
        cam1.sort()
        cam2.sort()
        cam3.sort()
        ## Lista cam1
        for i in range(len(cam1)):
            if len(cam2) == 0:
                cam2.append(cam1[i])
                self.archivos_cam2.append(self.archivos_cam1[i][0:6]+'m__c2__'+'FALTA')
                cam2.sort()
            elif i > len(cam2)-1:
                cam2.append(cam1[i])
                self.archivos_cam2.append(self.archivos_cam1[i][0:6]+'m__c2__'+'FALTA')
                cam2.sort()
                self.archivos_cam2.sort()
            elif cam1[i] < cam2[i]:
                cam2.append(cam1[i])
                self.archivos_cam2.append(self.archivos_cam1[i][0:6]+'m__c2__'+'FALTA')
                cam2.sort()
                self.archivos_cam2.sort()
            if len(cam3) == 0 :
                cam3.append(cam1[i])
                self.archivos_cam3.append(self.archivos_cam1[i][0:6]+'m__c3__'+'FALTA')
            elif i > len(cam3)-1:
                cam3.append(cam1[i])
                self.archivos_cam3.append(self.archivos_cam1[i][0:6]+'m__c3__'+'FALTA')
                cam3.sort()
                self.archivos_cam3.sort()
            elif cam1[i] < cam3[i]:
                cam3.append(cam1[i])
                self.archivos_cam3.append(self.archivos_cam1[i][0:6]+'m__c3__'+'FALTA')
                cam3.sort()
                self.archivos_cam3.sort()
        #lista cam2
        for i in range(len(cam2)):
            if len(cam1)== 0:
                cam1.append(cam2[i])
                self.archivos_cam1.append(self.archivos_cam2[i][0:6]+'m__c1__'+'FALTA')
                cam1.sort()
                self.archivos_cam1.sort()
            elif i > len(cam1)-1:
                cam1.append(cam2[i])
                self.archivos_cam1.append(self.archivos_cam2[i][0:6]+'m__c1__'+'FALTA')
                cam1.sort()
                self.archivos_cam1.sort()
            elif cam2[i] < cam1[i]:
                cam1.append(cam2[i])
                self.archivos_cam1.append(self.archivos_cam2[i][0:6]+'m__c1__'+'FALTA')
                cam1.sort()
                self.archivos_cam1.sort()
            if len(cam1)== 0:
                cam3.append(cam2[i])
                self.archivos_cam3.append(self.archivos_cam2[i][0:6]+'m__c3__'+'FALTA')
            elif i > len(cam3)-1:
                cam3.append(cam2[i])
                self.archivos_cam3.append(self.archivos_cam2[i][0:6]+'m__c3__'+'FALTA')
                cam3.sort()
                self.archivos_cam3.sort()
            elif cam2[i] < cam3[i]:
                cam3.append(cam2[i])
                self.archivos_cam3.append(self.archivos_cam2[i][0:6]+'m__c3__'+'FALTA')
                cam3.sort()
                self.archivos_cam3.sort()
        #lista cam3
        for i in range(len(cam3)):
            if len(cam2) == 0:
                cam2.append(cam3[i])
                self.archivos_cam2.append(self.archivos_cam3[i][0:6]+'m__c2__'+'FALTA')
            elif i > len(cam2)-1:
                cam2.append(cam3[i])
                self.archivos_cam2.append(self.archivos_cam3[i][0:6]+'m__c2__'+'FALTA')
                cam2.sort()
                self.archivos_cam2.sort()
            elif cam3[i] < cam2[i]:
                cam2.append(cam3[i])
                self.archivos_cam2.append(self.archivos_cam3[i][0:6]+'m__c2__'+'FALTA')
                cam2.sort()
                self.archivos_cam2.sort()
            if len(cam1) == 0:
                cam1.append(cam3[i])
                self.archivos_cam1.append(self.archivos_cam3[i][0:6]+'m__c1__'+'FALTA')
            elif i > len(cam1)-1:
                cam1.append(cam3[i])
                self.archivos_cam1.append(self.archivos_cam3[i][0:6]+'m__c1__'+'FALTA')
                cam1.sort()
                self.archivos_cam1.sort()
            elif cam3[i] < cam1[i]:
                cam1.append(cam3[i])
                self.archivos_cam1.append(self.archivos_cam3[i][0:6]+'m__c1__'+'FALTA')
                cam1.sort()
                self.archivos_cam1.sort()
        print 'las listas tienen ',len(self.archivos_cam1),len(self.archivos_cam2),len(self.archivos_cam3),' archivos'

    def actualizar_indices(self):
        """Actualiza la lista de los indices de las imagenes que tienen marca
        """

        ##global indices_marcas
        
        self.indices_marcas=[]
        for archivo in self.archivos_cam3:
            if archivo.endswith('MARCA.jpg') and (self.archivos_cam3.index(archivo) not in self.indices_marcas):
                self.indices_marcas.append(self.archivos_cam3.index(archivo))
        for archivo in self.archivos_cam2:
            if archivo.endswith('MARCA.jpg')and (self.archivos_cam2.index(archivo) not in self.indices_marcas):
                self.indices_marcas.append(self.archivos_cam2.index(archivo))
        for archivo in self.archivos_cam1:
            if archivo.endswith('MARCA.jpg') and (self.archivos_cam1.index(archivo) not in self.indices_marcas):
                self.indices_marcas.append(self.archivos_cam1.index(archivo))
        self.indices_marcas.sort()
        print 'hay ',len(self.indices_marcas),' archivos marcados: ',self.indices_marcas

        

    def leer_archivos(self):
        """Crea listas ordenadas de los archivos de cada camara, 
        archivos_camx       con los nombres de los archivos
        self.indices_marcas     con los indices que tienen las imagenes marcadas en la primer lista
        """
        global DEBUG

        self.archivos_cam1 = os.listdir(CARPETA_SESION_FOTOS)
        self.archivos_cam2 = os.listdir(CARPETA_SESION_FOTOS)
        self.archivos_cam3 = os.listdir(CARPETA_SESION_FOTOS)
        
        if self.DEBUG:
            copia = copy.deepcopy(self.archivos_cam1)
            for archivo in copia:
                if (not '__c1__' in archivo) or (not archivo.lower().endswith('jpg')):
                    self.archivos_cam1.remove(archivo)
            self.archivos_cam1.sort()
            
            copia = copy.deepcopy(self.archivos_cam2)
            for archivo in copia:
                if (not '__c2__' in archivo) or (not archivo.lower().endswith('jpg')):
                    self.archivos_cam2.remove(archivo)
            self.archivos_cam2.sort()
            
            copia = copy.deepcopy(self.archivos_cam3)
            for archivo in copia:
                if (not '__c3__'  in archivo) or (not archivo.lower().endswith('jpg')):
                    self.archivos_cam3.remove(archivo)
            self.archivos_cam3.sort()
            
            del(copia)
        self.rellenar_lista()
        self.actualizar_indices()
        self.copiar_fotos_para_gui(0)
        #print archivos_cam1
        print 'las listas tienen ',len(archivos_cam1),len(self.archivos_cam2),len(self.archivos_cam3),' archivos'
        print 'con ',len(self.indices_marcas),' archivos marcados: ',self.indices_marcas

#######---------vengo hasta aca por ahora
    def copiar_fotos_para_gui(self,indice):
        if len(self.archivos_cam1) == 0:
            self.img1.source = IMG_DEFAULT
            self.img2.source = IMG_DEFAULT
            self.img3.source = IMG_DEFAULT
        else:
            if indice > len(self.archivos_cam1):
                indice = 0
            if not self.archivos_cam1[indice].endswith('FALTA'):
                #shutil.copy(CARPETA_SESION_FOTOS+self.archivos_cam1[indice],'imagenCamara1.jpg')
                self.img1.source = CARPETA_SESION_FOTOS+self.archivos_cam1[indice]
            else:
                #shutil.copy(IMG_DEFAULT,'imagenCamara1.jpg')
                self.img1.source = IMG_DEFAULT
            if not self.archivos_cam2[indice].endswith('FALTA'):
                #shutil.copy(CARPETA_SESION_FOTOS+self.archivos_cam2[indice],'imagenCamara2.jpg')
                self.img2.source = CARPETA_SESION_FOTOS+self.archivos_cam2[indice]
            else:
               # shutil.copy(IMG_DEFAULT,'imagenCamara2.jpg')
                self.img2.source = IMG_DEFAULT
            if not self.archivos_cam3[indice].endswith('FALTA'):
                self.img3.source = CARPETA_SESION_FOTOS+self.archivos_cam3[indice]
              #  shutil.copy(CARPETA_SESION_FOTOS+self.archivos_cam1[indice],'imagenCamara3.jpg')
            else:
                shutil.copy(IMG_DEFAULT,'imagenCamara3.jpg')
                self.img3.source = IMG_DEFAULT
        try:
            self.img1_fullscreen.source = self.img1.source
        except:
            pass
        try:
            self.img2_fullscreen.source = self.img2.source
        except:
            pass
        try:
            self.img3_fullscreen.source = self.img3.source
        except:
            pass

    def siguiente(self,*largs):
        
        print 'avanzo con indice ',self.indice
        if self.indice >= (len(self.archivos_cam1) -1):
            self.indice = 0
        else:
            self.indice = self.indice + 1
        self.copiar_fotos_para_gui(self.indice)
        print 'nuevo indice', self.indice

    def anterior(self):
        print 'retrocedo con indice ',self.indice
        if self.indice == 0 :
            self.indice = (len(self.archivos_cam1) -1)
        else:
            self.indice = self.indice - 1
        self.copiar_fotos_para_gui(self.indice)
        print 'nuevo indice', self.indice

    def marca_siguiente(self):
        print 'indice actual:',self.indice
        print 'indice marcas:',self.indices_marcas
        if len(self.indices_marcas) == 0 :
            print 'no hay marcas, no hago nada'
            return
        for indice_marca in self.indices_marcas:
            if indice_marca > self.indice:
                self.indice = indice_marca
                print 'nuevo indice', self.indice
                self.copiar_fotos_para_gui(self.indice)
                return
        self.indice = self.indices_marcas[0]
        self.copiar_fotos_para_gui(self.indice)
        print 'nuevo indice', self.indice
        
    def marca_anterior(self):
        print 'indice actual:',self.indice
        print 'indice marcas:',self.indices_marcas
        if len(self.indices_marcas) == 0 :
            return
        for indice_marca in sorted(self.indices_marcas,reverse=True):
            if indice_marca < self.indice:
                self.indice = indice_marca
                print 'nuevo indice', self.indice
                self.copiar_fotos_para_gui(self.indice)
                return
        self.indice = self.indices_marcas[-1]
        self.copiar_fotos_para_gui(self.indice)
        print 'nuevo indice', self.indice

    def marcar_imagen(self,ruta, archivo_original,ruta_destino):
        """
        Crea una copia de la imagen, agregando MARCA al final del nombre del
        archivo y devuelve el nombre del archivo marcado
        """
        print archivo_original
        nombre_nuevo = os.path.split(archivo_original)[-1].rstrip('.jpg')+'MARCA.jpg'
        ###creo la copia de las imagenes marcadas
        ##agrego marca en la imagen y agrego en las listas de imagenes 
        img = PILImage.open(ruta+archivo_original,'r')
        draw = PILImageDraw.Draw(img)
        font = PILImageFont.truetype('UbuntuMono-B.ttf',200)
      # draw.text((x, y),"Sample Text",(r,g,b))
        draw.text((800, 80),"*",(255,0,0),font=font)
        img.save(ruta_destino+nombre_nuevo,quality=100)
        self.copiar_fotos_para_gui(self.indice)
        return nombre_nuevo
    
    def pre_marcar(self):
        print 'entro a premarcar con indice:',self.indice
        print 'en una lista con ',len(self.archivos_cam1),' elementos'
        if not self.archivos_cam1[self.indice].endswith('FALTA'):
            self.archivos_cam1.insert(self.indice,self.marcar_imagen(CARPETA_SESION_FOTOS,self.archivos_cam1[self.indice],CARPETA_SESION_FOTOS))
            print 'inserte, en premarcar :',self.indice,self.marcar_imagen(CARPETA_SESION_FOTOS,self.archivos_cam1[self.indice],CARPETA_SESION_FOTOS)
        if not self.archivos_cam2[self.indice].endswith('FALTA'):
            self.archivos_cam2.insert(self.indice,self.marcar_imagen(CARPETA_SESION_FOTOS,self.archivos_cam2[self.indice],CARPETA_SESION_FOTOS))
        if not self.archivos_cam3[self.indice].endswith('FALTA'):
            self.archivos_cam3.insert(self.indice,self.marcar_imagen(CARPETA_SESION_FOTOS,self.archivos_cam3[self.indice],CARPETA_SESION_FOTOS))
        self.rellenar_lista()
        self.actualizar_indices()
        #self.siguiente()



        
    def adherir_comentario(self):
        print 'voy a adherir comentario'
        ####aca esta la papota del comentaroi
        #with open(COMENTARIO,'r') as texto:
            #texto_crudo = texto.read()
        #print texto_crudo
        lineas = textwrap.wrap(self.comentario.text, width=50)
        if not self.archivos_cam1[self.indice].endswith('FALTA'):
            img = PILImage.open(CARPETA_SESION_FOTOS+self.archivos_cam1[self.indice],'r')
            draw = PILImageDraw.Draw(img)
            font = PILImageFont.truetype('UbuntuMono-B.ttf',45)
          # draw.text((x, y),"Sample Text",(r,g,b))
            i=0
            for linea in lineas:
                draw.text((2, 400+i*100),linea,(255,0,0),font=font)
                i+= 1
                if not self.archivos_cam1[self.indice].endswith('MARCA.jpg'):
                    img.save(CARPETA_TEMPORAL+self.archivos_cam1[self.indice],quality=100)
                    self.archivos_cam1.insert(self.indice,self.marcar_imagen(CARPETA_TEMPORAL,self.archivos_cam1[self.indice],CARPETA_SESION_FOTOS))
                else:
                    img.save(CARPETA_SESION_FOTOS+self.archivos_cam1[self.indice],quality=100)
        
        if not self.archivos_cam2[self.indice].endswith('FALTA'):
            img = PILImage.open(CARPETA_SESION_FOTOS+self.archivos_cam2[self.indice],'r')
            draw = PILImageDraw.Draw(img)
            font = PILImageFont.truetype('UbuntuMono-B.ttf',45)
          # draw.text((x, y),"Sample Text",(r,g,b))
            i=0
            for linea in lineas:
                draw.text((2, 400+i*100),linea,(255,0,0),font=font)
                i+= 1
                if not self.archivos_cam2[self.indice].endswith('MARCA.jpg'):
                    img.save(CARPETA_TEMPORAL+self.archivos_cam2[self.indice],quality=100)
                    self.archivos_cam2.insert(self.indice,self.marcar_imagen(CARPETA_TEMPORAL,self.archivos_cam2[self.indice],CARPETA_SESION_FOTOS))
                else:
                    img.save(CARPETA_SESION_FOTOS+self.archivos_cam2[self.indice],quality=100)   
        
        if not self.archivos_cam3[self.indice].endswith('FALTA'):
            img = PILImage.open(CARPETA_SESION_FOTOS+self.archivos_cam3[self.indice],'r')
            draw = PILImageDraw.Draw(img)
            font = PILImageFont.truetype('UbuntuMono-B.ttf',45)
          # draw.text((x, y),"Sample Text",(r,g,b))
            i=0
            for linea in lineas:
                draw.text((2, 400+i*100),linea,(255,0,0),font=font)
                i+= 1
                if not self.archivos_cam3[self.indice].endswith('MARCA.jpg'):
                    img.save(CARPETA_TEMPORAL+self.archivos_cam3[self.indice],quality=100)
                    self.archivos_cam3.insert(self.indice,self.marcar_imagen(CARPETA_TEMPORAL,self.archivos_cam3[self.indice],CARPETA_SESION_FOTOS))
                else:
                    img.save(CARPETA_SESION_FOTOS+self.archivos_cam3[self.indice],quality=100)
        self.comentario.text = ''
        self.rellenar_lista()
        self.actualizar_indices()
        self.copiar_fotos_para_gui(self.indice)
        #self.siguiente()
        #print 'nuevo indice', indice
        
class Pantalla_Operar(Screen):
    cam1 = ObjectProperty()
    cam2 = ObjectProperty()
    cam3 = ObjectProperty()
    l_operador = ObjectProperty()
    l_ruta = ObjectProperty()
    l_sentido= ObjectProperty()
    l_metros= ObjectProperty()
    l_prog = ObjectProperty()
    l_velocidad = ObjectProperty()
    
    def recargar(self, *largs):
        self.cam1.reload()
        self.cam2.reload()
        self.cam3.reload()
    
    def actualizar_datos(self,op,):
        pass
        #self.l_operador=
        #self.l_ruta = 
        #self.l_sentido = 

class Pantalla_Diagnostico(Screen):
    checkcam1 = ObjectProperty(None)
    checkcam2 = ObjectProperty(None)
    checkcam3 = ObjectProperty(None)
    gpstxt = ObjectProperty(None)
    encodertxt = ObjectProperty(None)
    
    def reiniciar_cam1(self):
        if self.checkcam1.source == CONEXION_OK:
            system("ssh pi@%s './reset_camara.sh' & " % IP_CAM1)
    
    def reiniciar_cam2(self):
        if self.checkcam2.source == CONEXION_OK:
            system("ssh pi@%s './reset_camara.sh' & " % IP_CAM2)

    def reiniciar_cam3(self):
        if self.checkcam3.source == CONEXION_OK:
            system("ssh pi@%s './reset_camara.sh' & " % IP_CAM3)
    
    def reiniciar_encoder(self):
        if self.checkcam1.source == CONEXION_OK:
            system("ssh pi@%s './reset_encoder.sh' & " % IP_CAM1)
            self.termino_diagnostico()
            Clock.schedule_once(self.crear_conexion_encoder,3)
    
    def crear_conexion_encoder(self,*largs):
        try:
            self.conexion_ENCODER = socket.socket()
            self.conexion_ENCODER.connect((IP_CAM1,PUERTO_ENCODER))
            self.conexion_ENCODER.sendall('diagnostico')
        except:
            print 'no pude conectar CONEXION ENCODER en diagnostico'
            self.encodertxt.text = 'No hay conexion con encoder'

    def actualizar_encoder_diag(self,*largs):

        if os.path.exists(ENCODER_DIAGNOSTICO):
            with open(ENCODER_DIAGNOSTICO,'r') as enc:
                metros = enc.readline()
                self.encodertxt.text = metros
        else:
            self.encodertxt.text = 'No hay Lectura de Encoder'

    def termino_diagnostico(self):
        try:
            self.conexion_ENCODER.sendall('nodiagnostico')
            self.conexion_ENCODER.close()
        except:
            print'no pude cerrar conexion encoder'

class Pantalla_Guardar(Screen):
    prog_bar = ObjectProperty()
    prog_txt = ObjectProperty()
    btn_guardar = ObjectProperty()
    btn_descartar = ObjectProperty()
    nombre = ObjectProperty()
    adv = ObjectProperty()
    btn_volver = ObjectProperty()
    
    def guardar_sesion(self):
        if self.nombre.text == '':
            adv.text = 'DEBE INGRESAR UN NOMBRE PARA GUARDAR LA SESION'
            return
        if not os.path.exists(CARPETA_SESIONES+self.nombre.text):
            carpeta_destino = CARPETA_SESIONES+self.nombre.text
            makedirs(carpeta_destino)
        else:
            self.adv.text = 'YA EXISTE UNA CARPETA CON ESE NOMBRE'
            return
        self.adv.text = ''
        self.btn_guardar.disabled = True
        self.btn_descartar.disabled = True
        self.nombre.disabled = True
        lista_archivos = listdir(CARPETA_FOTOS_TEMPORAL)
        i=0
        self.prog_bar.max = len(lista_archivos)
        for archivo in lista_archivos:
            shutil.move(CARPETA_FOTOS_TEMPORAL+archivo,carpeta_destino)
            i+=1
            self.prog_bar.value = i
            self.prog_txt.text = 'Moviendo archivo '+str(i)+' de '+str(len(lista_archivos))
        self.adv.text = 'COPIA FINALIZADA - puede volver al menu principal'
        self.btn_volver.disabled = False

        
    def descartar_sesion(self):
        self.adv.text = ''
        self.btn_guardar.disabled = True
        self.btn_descartar.disabled = True
        self.nombre.disabled = True
        lista_archivos = listdir('Cam1_almacen/')
        i=0
        self.prog_bar.max = len(lista_archivos)
        for archivo in lista_archivos:
            remove('Cam1_almacen/'+archivo)
            i+=1
            self.prog_bar.value = i
            self.prog_txt.text = 'Borrando archivo '+str(i)+' de '+str(len(lista_archivos))
        self.adv.text = 'BORRADO FINALIZADO - puede volver al menu principal'
        self.btn_volver.disabled = False
            
            
            
class Pantalla_Configurar(Screen):
    ####FALTA HACER QUE CAMBIE DE CAMARA CUANDO ELIJO OTRA
    #### O SEA, CERRAR CONEXIONES, LEER CONF DE CAMARA NUEVA
    #### Y CREAR CONEXIONES NUEVAS
    preview= ObjectProperty()
    brillo= ObjectProperty()
    contraste= ObjectProperty()
    comp_exp= ObjectProperty()
    vel_disparo= ObjectProperty()
    iso= ObjectProperty()
    expo= ObjectProperty()
    contraste_viejo=0
    brillo_viejo=0
    iso_viejo=''
    vel_disparo_viejo=0
    comp_exp_viejo=0
    expo_viejo=''
    rotacion_viejo = 0
    cam1 = ObjectProperty()
    cam2 = ObjectProperty()
    cam3 = ObjectProperty()
    rot0= ObjectProperty()
    rot90= ObjectProperty()
    rot180= ObjectProperty()
    rot270= ObjectProperty()
    
    #~ def build(self):
        #~ self.cam1.bind(active=self.cambio_de_camara)
        #~ self.cam3.bind(active=self.cambio_de_camara)
        #~ self.cam2.bind(active=self.cambio_de_camara)
    #~ 
    def cambio_de_camara(self,button_cam):
        #if checkbox_cam.active:
        #    try:
        self.cerrar_conexiones()
        #    except:
        #        print 'no estaba abierta todavia la conexion'
        self.leer_configuracion()
        self.crear_conexiones()
        
    
    def leer_configuracion(self):
        if self.cam1.state == 'down':
            with open('configCamara1.txt','r') as configuracion:
                json_leido = json.loads(configuracion.read())   
                print json_leido
        elif self.cam2.state == 'down':
            with open('configCamara2.txt','r') as configuracion:
                json_leido = json.loads(configuracion.read())   
                print json_leido
        else:
            with open('configCamara3.txt','r') as configuracion:
                json_leido = json.loads(configuracion.read())   
                print json_leido
        self.contraste.value= int(json_leido['contraste'])
        self.contraste_viejo=self.contraste.value
        self.brillo.value= int(json_leido['brillo'])
        self.brillo_viejo = self.brillo.value
        self.rotacion = int(json_leido['rotaci'])
        self.rotacion_viejo = self.rotacion
        self.rot0.active = False
        self.rot90.active = False
        self.rot180.active = False
        self.rot270.active = False
        print self.rotacion
        if self.rotacion == 0:
            self.rot0.active = True
        elif self.rotacion == 90:
            self.rot90.active = True
        elif self.rotacion == 180:
            self.rot180.active = True
        else:
            self.rot270.active = True
        if str (json_leido['iso']) == '0':
            self.iso.text = 'AUTO'
        else:
            self.iso.text = str (json_leido['iso'])
        self.iso_viejo = self.iso.text
        self.vel_disparo.value= int(json_leido['veldisparo'])
        self.vel_disparo_viejo = self.vel_disparo.value
        self.comp_exp.value = int(json_leido['ev'])
        self.comp_exp_viejo = self.comp_exp.value
        self.expo.text = (str(json_leido['modo_exposicion'])).lower()
        self.expo_viejo = self.expo.text
    
    def crear_conexiones(self):
        self.socket_imagen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_imagen.settimeout(2)
        if self.cam1.state == 'down':
            try:
                self.socket_imagen.connect((IP_CAM1, PUERTO_IMAGEN))
            except:
                shutil.copy(SIN_CONEXION,'temporales/camaraconfig.jpg')
                self.preview.reload()
                return
        elif self.cam2.state == 'down':
            try:
                self.socket_imagen.connect((IP_CAM2, PUERTO_IMAGEN))
            except:
                shutil.copy(SIN_CONEXION,'temporales/camaraconfig.jpg')
                self.preview.reload()
                return
        else:
            try:
                self.socket_imagen.connect((IP_CAM3, PUERTO_IMAGEN))
            except:
                shutil.copy(SIN_CONEXION,'temporales/camaraconfig.jpg')
                self.preview.reload()
                return
        self.conexion_imagen = self.socket_imagen.makefile('wrb')
        print 'cree conexion IMAGEN OK'    
        self.conexion_TRIGGER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conexion_TRIGGER.settimeout(2)
        if self.cam1.state == 'down':
            try:
                self.conexion_TRIGGER.connect_ex((IP_CAM1, PUERTO_TRIGGER))
            except:
                shutil.copy(SIN_CONEXION,'temporales/camaraconfig.jpg')
                self.preview.reload()
                self.conexion_imagen.close()
                return
        elif self.cam2.state == 'down':
            try:
                self.conexion_TRIGGER.connect_ex((IP_CAM2, PUERTO_TRIGGER))
            except:
                
                shutil.copy(SIN_CONEXION,'temporales/camaraconfig.jpg')
                self.preview.reload()
                self.conexion_imagen.close()
        else:
            try:
                self.conexion_TRIGGER.connect_ex((IP_CAM3, PUERTO_TRIGGER))
            except:
                shutil.copy(SIN_CONEXION,'temporales/camaraconfig.jpg')
                self.preview.reload()
                self.conexion_imagen.close()
        print 'cree conexion TRIGGER OK'
        self.socket_imagen.settimeout(None)
        self.conexion_TRIGGER.settimeout(None)
        Clock.schedule_once(self.fotografo,0.5)
        Clock.schedule_once(self.enviar_configuracion,0.5)
        
    def cerrar_conexiones(self):
        try:
            self.conexion_TRIGGER.sendall('salir'.ljust(15,'#'))
            self.conexion_TRIGGER.close()
        except:
            print 'error al intentar cerrar conexiones'
            
        Clock.unschedule(self.enviar_configuracion)
        Clock.unschedule(self.fotografo)
        print 'cerre conexion TRIGGER'
    
    def guardar_configuracion(self):
        config = {}
        config['brillo']=int(self.brillo.value)
        config['contraste']=int(self.contraste.value)
        if self.iso.text == 'AUTO':
            config['iso']= 0
        else:
            config['iso']= int(self.iso.text)
        config['ev']= int(self.comp_exp.value)
        config['modo_exposicion'] = self.expo.text.upper()
        config['veldisparo'] = int(self.vel_disparo.value)
        config['rotaci'] = int(self.rotacion)
        
        if self.cam1.state == 'down':
            try:
                with open('configCamara1.txt','w') as archivo:
                    json.dump(config,archivo)
                    print 'guardo_conf camara1', config
            except:
                print 'estaba siendo usado el archivo'
                sleep(0.5)
                print 'intento de nuevo'
                try:
                    with open('configCamara1.txt','w') as archivo:
                        json.dump(config,archivo)
                except:
                    print 'No pude guardar la cnfiguracion cam1'
                        
                
        elif self.cam2.state == 'down':
            try:
                with open('configCamara2.txt','w') as archivo:
                    json.dump(config,archivo)
                    print 'guardo_conf camara2', config
            except:
                print 'estaba siendo usado el archivo'
                sleep(0.5)
                print 'intento de nuevo'
                try:
                    with open('configCamara2.txt','w') as archivo:
                        json.dump(config,archivo)
                except:
                    print 'No pude guardar la cnfiguracion cam2'
        else:
            try:
                with open('configCamara3.txt','w') as archivo:
                    json.dump(config,archivo)
                    print 'guardo_conf camara3', config
            except:
                print 'estaba siendo usado el archivo'
                sleep(0.5)
                print 'intento de nuevo'
                try:
                    with open('configCamara3.txt','w') as archivo:
                        json.dump(config,archivo)
                except:
                    print 'No pude guardar la cnfiguracion cam3'
    
    def enviar_configuracion(self,*largs):
        if self.contraste_viejo != self.contraste.value:
            self.conexion_TRIGGER.sendall(('contra'+str(int(self.contraste.value))).ljust(15,'#'))
            self.contraste_viejo = self.contraste.value
        if self.brillo_viejo != self.brillo.value:
            self.conexion_TRIGGER.sendall(('brillo'+str(int(self.brillo.value))).ljust(15,'#'))
            self.brillo_viejo = self.brillo.value
        if self.iso_viejo != self.iso.text:
            if self.iso.text == 'AUTO':
                self.conexion_TRIGGER.sendall(('iso---'+'0').ljust(15,'#'))
            else:
                self.conexion_TRIGGER.sendall(('iso---'+self.iso.text).ljust(15,'#'))
            self.iso_viejo = self.iso.text
        if self.vel_disparo_viejo != self.vel_disparo.value:
            self.conexion_TRIGGER.sendall(('veldis'+str(int(self.vel_disparo.value))).ljust(15,'#'))
            self.vel_disparo_viejo = self.vel_disparo.value
        if self.comp_exp_viejo != self.comp_exp.value:
            self.conexion_TRIGGER.sendall(('compex'+str(int(self.comp_exp.value))).ljust(15,'#'))
            self.comp_exp_viejo = self.comp_exp.value
        if self.expo_viejo != self.expo.text:
            self.conexion_TRIGGER.sendall(('modoex'+self.expo.text.lower()).ljust(15,'#'))
            self.expo_viejo = self.expo.text
        if (self.rot0.active == True) and (self.rotacion_viejo != 0):
            self.conexion_TRIGGER.sendall('rotaci'+'0'.ljust(15,'#'))
            self.rotacion_viejo = 0
            self.rotacion = 0
        if (self.rot90.active == True) and (self.rotacion_viejo != 90):
            self.conexion_TRIGGER.sendall('rotaci'+'90'.ljust(15,'#'))
            self.rotacion_viejo = 90
            self.rotacion = 90
        if (self.rot180.active == True) and (self.rotacion_viejo != 180):
            self.conexion_TRIGGER.sendall('rotaci'+'180'.ljust(15,'#'))
            self.rotacion_viejo = 180
            self.rotacion = 180
        if (self.rot270.active == True) and (self.rotacion_viejo != 270):
            self.conexion_TRIGGER.sendall('rotaci'+'270'.ljust(15,'#'))
            self.rotacion_viejo = 270
            self.rotacion = 270
        Clock.schedule_once(self.enviar_configuracion,0.5)
    
    def fotografo(self,*largs):
        """basado en procesador de fotos de pantalla operar"""
        try:
            self.conexion_TRIGGER.sendall('foto'.ljust(15,'#'))
        except:
            print 'ya cerre la conexion'
            Clock.unschedule(fotografo)
            return
        ###---------recivo imagen por socket
        image_len = struct.unpack('<L', self.conexion_imagen.read(struct.calcsize('<L')))[0]
        #condicion de salida, la genera la camara enviando un mensaje vacio
        if not image_len:
            Clock.unschedule(fotografo)
            self.conexion_imagen.close()
            return
        # Construct a stream to hold the image data and read the image
        # data from the connection
        image_stream = io.BytesIO()
        image_stream.write(self.conexion_imagen.read(image_len))
        image_stream.seek(0)
        self.preview.memory_data = image_stream
        image_stream.seek(0)
        img = PILImage.open(image_stream)
        img.save('temporales/camaraconfig.jpg',quality=95)
        self.preview.reload()
        Clock.schedule_once(self.fotografo,0.5)

        
    

class Pantalla_Calibrar(Screen):
    btn_detener = ObjectProperty()
    btn_comenzar = ObjectProperty()
    metros_recorridos = ObjectProperty()
    btn_enviar_valor_calibracion = ObjectProperty()
    valor_cte = ObjectProperty()
    
    def on_pre_enter(self):
        self.conexion_ENCODER = socket.socket()
        self.conexion_ENCODER.connect((IP_CAM1,PUERTO_ENCODER))
        self.conexion_ENCODER.sendall('valorcte')
        respuesta = self.conexion_ENCODER.recv(512)
        self.valor_cte.text = respuesta
        self.btn_detener.disabled = True
        self.metros_recorridos.disabled = True
        self.btn_enviar_valor_calibracion.disabled = True
        self.metros_recorridos.text = ''
        
    def comienzo_calibrar(self):
        self.btn_detener.disabled = False
        self.btn_comenzar.disabled = True
        self.conexion_ENCODER.sendall('calibrar')
        respuesta = self.conexion_ENCODER.recv(512)
        self.valor_cte.text = respuesta
        self.metros_recorridos.text = ''
        
    def detener_calibrar(self):
        self.conexion_ENCODER.sendall('nocalibrar')
        self.btn_detener.disabled = True
        self.metros_recorridos.disabled = False
        self.btn_enviar_valor_calibracion.disabled = False
        
        
    def configurar_constante(self):
        self.btn_comenzar.disabled = False
        self.btn_enviar_valor_calibracion.disabled = True
        self.conexion_ENCODER.sendall(self.metros_recorridos.text)
        self.valor_cte.text = self.conexion_ENCODER.recv(512)
        self.metros_recorridos.text = ''

class Pantalla_Ciclar(Screen):
    pass


####-------Fin interfaz grafica


#### -------------------------------------------------PROGRAMA PRINCIPAL
class pymonitorApp(App):
    #Configuracion de operar
    
    def build(self):
        #valores por defecto
        shutil.copy('img_default/default.jpg','temporales/camara1c.jpg')
        shutil.copy('img_default/default.jpg','temporales/camara2c.jpg')
        shutil.copy('img_default/default.jpg','temporales/camara3c.jpg')

        #CREO TODAS LAS PANTALLAS
        self.pInicio = Pantalla_Inicio(name='inicio')
        self.pApagar = Pantalla_Apagar_Camaras(name='apagar')
        self.pOperar = Pantalla_Operar(name='operar')
        self.pConfOperar = Pantalla_Conf_Operar(name='conf_operar')
        self.pConfigurar = Pantalla_Configurar(name='configurar')
      #  self.pCiclar = Pantalla_Ciclar(name='ciclar')
        self.pCalibrar = Pantalla_Calibrar(name='calibrar')
        self.pGuardar = Pantalla_Guardar(name='guardar')
        self.pRevisar = Pantalla_Revisar(name='revisar')
        self.pDiagnostico = Pantalla_Diagnostico(name='diagnostico')
        self.screenAdmin = ScreenManager()#transition=NoTransition())
        self.screenAdmin.add_widget(self.pInicio)
        self.screenAdmin.add_widget(self.pOperar)
        self.screenAdmin.add_widget(self.pConfOperar)
        self.screenAdmin.add_widget(self.pConfigurar)
       # self.screenAdmin.add_widget(self.pCiclar)
        self.screenAdmin.add_widget(self.pCalibrar)
        self.screenAdmin.add_widget(self.pGuardar)
        self.screenAdmin.add_widget(self.pDiagnostico)
        self.screenAdmin.add_widget(self.pRevisar)
        self.screenAdmin.add_widget(self.pApagar)

        
     
     
        #OBSERVER PARA EL MONITOR DEL GPS    -  no lo uso mas
        """
        self.monGPS = MonitorGPS()
        self.monGPS.config(self.pOperar.l_metros)
        self.obsGPS = Observer()
        self.obsGPS.schedule(self.monGPS, path='temporales')
        
        self.obsGPS.start()
"""
        #OPERAR###
        
        print 'fin build'
        return self.screenAdmin
    
    def comienzo_operar(self):
        global datoGps
        global camara
        #------------VALIDACION DE DATOS
        if  not self.pConfOperar.operador.text != '':
            self.pConfOperar.adv.text = 'COMPLETE EL CAMPO OPERADOR'
            return
        if not self.pConfOperar.ruta.text != '':
            self.pConfOperar.adv.text = 'COMPLETE EL CAMPO RUTA'
            return
        if not self.pConfOperar.sentido.text != '':
            self.pConfOperar.adv.text = 'COMPLETE EL CAMPO SENTIDO'
            return
        if not self.pConfOperar.progreso.text != '':
            self.pConfOperar.adv.text = 'COMPLETE EL CAMPO PROGRESIVO INICIAL'
            return
        ts = time.time()
        with open(CARPETA_FOTOS_TEMPORAL+'info.txt','w') as info:
            info.write('OPERADOR: '+ self.pConfOperar.operador.text + '\n')
            info.write('FECHA: '+ datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y_%Hh%Mm%S.%fs').rstrip('0') +'\n') 
            info.write('RUTA: '+ self.pConfOperar.ruta.text + '\n')
            info.write('SENTIDO: '+ self.pConfOperar.sentido.text+ '\n')
            info.write('DISTANCIA INICIAL: '+ self.pConfOperar.progreso.text )
        self.pOperar.l_operador = self.pConfOperar.operador.text
        self.ruta = self.pConfOperar.ruta.text
        self.sentido = self.pConfOperar.sentido.text
        self.progreso = self.pConfOperar.progreso.text
        Clock.schedule_interval(self.pOperar.recargar,0.5)
        self.q_mostrar_datos = Queue.Queue()
        self.t_fotografo = threading.Thread(target=fotografo, args = (
            self.pConfOperar.operador.text, self.pConfOperar.ruta.text,
            self.pConfOperar.sentido.text, self.pConfOperar.progreso.text, 
            self.q_mostrar_datos))
        self.t_fotografo.start()
        self.t_actualizar_datos = threading.Thread(target=actualizar_datos, args = (
            self.q_mostrar_datos, self.pOperar.l_metros, self.pOperar.l_prog, 
            self.pOperar.l_velocidad))
        self.t_actualizar_datos.start()
        
        ## PARA EL GPS
        self.queueGPS = mp.Queue()
        self.salidaGPS = mp.Event()
        self.t_GPS = threading.Thread(target=LectorGPS, args = (self.queueGPS, self.salidaGPS ) )
        self.t_GPS.start()
        Clock.schedule_once(self.actualiza_datoGPS, 0.3)
        datoGps = 'Sin-Conexion'
        
        

        ###configurar encoder: operar
        self.conexion_ENCODER = socket.socket()
        self.conexion_ENCODER.connect((IP_CAM1,PUERTO_ENCODER))
        self.conexion_ENCODER.sendall('operar')
        self.screenAdmin.current = 'operar'
        #Clock.schedule_once(self.actualiza_operador,0.5)
     
    def actualiza_datoGPS(self,*largs):
        global datoGps
        if self.screenAdmin.current == 'operar':
            if not self.queueGPS.empty():
                datoGps = self.queueGPS.get()
                #print datoGps
            Clock.schedule_once(self.actualiza_datoGPS, 0.3)
        if self.screenAdmin.current == 'diagnostico':
            if not self.queueGPS.empty():
                datoGps = self.queueGPS.get()
                self.pDiagnostico.gpstxt.text = datoGps
            Clock.schedule_once(self.actualiza_datoGPS, 0.3)
        
    def actualiza_operador(self,*largs):
        self.pOperar.l_operador.text = self.pConfOperar.operador.text
        self.pOperar.l_ruta.text = self.pConfOperar.ruta.text
        self.pOperar.l_sentido.text = self.pConfOperar.sentido.text
        
    def comienzo_conf_operar(self):

        self.pConfOperar.operador.text = ''
        self.pConfOperar.ruta.text = ''
        self.pConfOperar.sentido.text = ''
        self.pConfOperar.progreso.text = ''
        self.screenAdmin.current = 'conf_operar'
     
    
    def comienzo_configurar(self):
        self.screenAdmin.current = 'configurar'
        
    
    def comienzo_calibrar(self):
        self.screenAdmin.current = 'calibrar'
    
    def comienzo_ciclar(self):
        self.screenAdmin.current = 'ciclar'
    
    def diagnostico(self):
        global datoGps
        self.screenAdmin.current = 'diagnostico'
        ## PARA EL GPS
        datoGps = 'Sin-Conexion'
        self.queueGPS = mp.Queue()
        self.salidaGPS = mp.Event()
        self.t_GPS = threading.Thread(target=LectorGPS, args = (self.queueGPS, self.salidaGPS ) )
        self.t_GPS.start()
        Clock.schedule_once(self.actualiza_datoGPS, 0.3)
        ## PARA PINGUEAR
        checkear_conexiones(self.pDiagnostico.checkcam1, self.pDiagnostico.checkcam2, self.pDiagnostico.checkcam3)
        Clock.schedule_interval(partial(checkear_conexiones, self.pDiagnostico.checkcam1, self.pDiagnostico.checkcam2, self.pDiagnostico.checkcam3 ), 4)
        ## PARA EL ENCODER
        self.pDiagnostico.crear_conexion_encoder()
        Clock.schedule_interval(self.pDiagnostico.actualizar_encoder_diag, 0.5)

    def guardar_sesion(self):
        self.screenAdmin.current = 'guardar'
   
    #------esto es del revisador
    def dismiss_popup(self):
        self._popup.dismiss()
        
    def load(self,path,filename):
        global CARPETA_SESION_FOTOS
        print path, filename
        self.dismiss_popup()
        if filename == []:
            CARPETA_SESION_FOTOS = path + '/'
        elif filename[0].endswith('.jpg'):
            CARPETA_SESION_FOTOS = path + '/'
        else:
            CARPETA_SESION_FOTOS = filename[0]+'/'
        self.screenAdmin.current = 'revisar'
    
    def seleccion_sesion(self):
        self.content = Elegir_sesion(load=self.load, cancel=self.dismiss_popup)
        self.content.info_carpeta.text = ''
        self._popup = Popup(title="Seleccionar SESION", content=self.content,
                            size_hint=(0.9, 0.9))
        self._popup.open()
        
    def filtro_carpetas_vacias(self,folder,filename):
        print folder, filename
        return True
    ## fin del revisador 
    
    def mostar_info_carpeta(self,path,filename):
        if filename == []:
            if os.path.exists(path +'/info.txt'):
                with open(path +'/info.txt','r') as info:
                    self.content.info_carpeta.text = info.read()
            else:
                self.content.info_carpeta.text = 'NO HAY INFORMACION SOBRE LA SESION'
        elif filename[0].endswith('.jpg'):
            if os.path.exists(path +'/info.txt'):
                with open(path +'/info.txt','r') as info:
                    self.content.info_carpeta.text = info.read()
            else:
                self.content.info_carpeta.text = 'NO HAY INFORMACION SOBRE LA SESION'
        else:
            if os.path.exists(filename[0]+'/info.txt'):
                with open(filename[0] +'/info.txt','r') as info:
                    self.content.info_carpeta.text = info.read()
            else:
                self.content.info_carpeta.text = 'NO HAY INFORMACION SOBRE LA SESION'

    def terminar_operar(self):
        self.conexion_ENCODER.sendall('nooperar')
        Clock.unschedule(self.pOperar.recargar)
        self.screenAdmin.current = 'guardar'
        self.salidaGPS.set()
    
    def apagar_camaras(self):
        system("ssh pi@10.42.0.3 'sudo poweroff' ")
        system("ssh pi@10.42.0.4 'sudo poweroff' ")
        system("ssh pi@10.42.0.5 'sudo poweroff' ")
        Clock.schedule_once(self.cerrar_popup_reiniciar,5)    
        
    def salida(self,*largs):
        self.pApagar.b_apagar.disabled = False
        self.pApagar.l_apagar.text = 'YA PUEDE SALIR'
    
    def apagar_reiniciar_raspis(self):
        content = Apagar_reiniciar_popup()
        self.reiniciar_popup = Popup(title="Reiniciar - Apagar Camaras", content=content,
                            size_hint=(0.9, 0.9))
        self.reiniciar_popup.open()
    
    def cerrar_popup_reiniciar(self,*largs):
        self.reiniciar_popup.dismiss()
        
    def reiniciar_raspi(self):
        system("ssh pi@10.42.0.3 'sudo reboot' ")
        system("ssh pi@10.42.0.4 'sudo reboot' ")
        system("ssh pi@10.42.0.5 'sudo reboot' ")
        Clock.schedule_once(self.cerrar_popup_reiniciar,5)
    
    
    def volver(self):
        if self.screenAdmin.current == 'calibrar':
            self.pCalibrar.btn_detener.disabled = True
            self.pCalibrar.btn_comenzar.disabled = False
            self.pCalibrar.btn_enviar_valor_calibracion.disabled = False
            try:
                self.pCalibrar.conexion_ENCODER.sendall('salir')
                self.pCalibrar.conexion_ENCODER.close()
            except:
                pass
        if self.screenAdmin.current == 'diagnostico':
            self.salidaGPS.set()
            Clock.unschedule(checkear_conexiones)
            Clock.unschedule(self.pDiagnostico.actualizar_encoder_diag)
            self.pDiagnostico.termino_diagnostico()
        self.screenAdmin.current = 'inicio'
    
    def salir(self):
        exit()


pymonitorApp().run()
