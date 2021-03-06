#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.dom import minidom
import time
import hashlib
import os


def escribe_log(linea, tipo, ippuerto=0):
    hora = time.strftime("%Y%m%d%H%M%S", time.localtime())
    linea = linea.replace("\r\n", " ")
    if tipo == "envio":
        linea_log = ("Sent to " + ippuerto + ": " + linea)
    elif tipo == "recibo":
        linea_log = ("Received from " + ippuerto + ": " + linea)
    elif tipo == "error":
        linea_log = ("Error: " + linea)
    else:
        linea_log = linea
    mi_log.write(hora + " " + str(linea_log) + "\r\n")


try:
    config = sys.argv[1]
    METODO = sys.argv[2]
    OPCION = sys.argv[3]
except (IndexError, ValueError):
    sys.exit("Usage: python uaclient.py config metodo opcion")

archivo_xml = minidom.parse(config)
# obtengo la informacion de mi usuario y servidor
account = archivo_xml.getElementsByTagName('account')
uaserver = archivo_xml.getElementsByTagName('uaserver')
mi_usuario = account[0].attributes['username'].value
mi_passwd = account[0].attributes['passwd'].value
mi_IP = uaserver[0].attributes['ip'].value
if mi_IP == '':
    mi_IP = "127.0.0.1"
mi_puerto = uaserver[0].attributes['puerto'].value
rtpaudio = archivo_xml.getElementsByTagName('rtpaudio')
puerto_RTP = rtpaudio[0].attributes['puerto'].value

# obtengo informacion del servidor regproxy y me conecto
regproxy = archivo_xml.getElementsByTagName('regproxy')
IP_regproxy = regproxy[0].attributes['ip'].value
puerto_regproxy = int(regproxy[0].attributes['puerto'].value)

xml_log = archivo_xml.getElementsByTagName('log')
ruta_log = xml_log[0].attributes['path'].value
xml_audio = archivo_xml.getElementsByTagName('audio')
audio_path = xml_audio[0].attributes['path'].value

# Contenido que vamos a enviar
# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:

    mi_log = open(ruta_log, "a")
    escribe_log("Starting...", "otro")
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_regproxy, puerto_regproxy))

    if METODO == "register":
        linea = ("REGISTER sip:" + mi_usuario + ":" + mi_puerto +
                 " SIP/2.0\r\n" + "Expires: " + OPCION + "\r\n")

        print("Enviando: " + linea)
        my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
        escribe_log(linea, "envio", IP_regproxy + ":" + str(puerto_regproxy))
        try:
            data = my_socket.recv(1024)
        except ConnectionRefusedError:
            escribe_log("No server listening at " + IP_regproxy + " port " +
                        str(puerto_regproxy), "error")
            sys.exit("conexion rechazada")

        print('Recibido -- ', data.decode('utf-8'))
        respuesta_server = data.decode('utf-8')
        escribe_log(respuesta_server, "recibo", IP_regproxy + ":"
                    + str(puerto_regproxy))
        if respuesta_server[:24] == ("SIP/2.0 401 Unauthorized"):
            numero = respuesta_server.split('"')[1]
            n = hashlib.sha256()
            n.update(mi_passwd.encode('utf-8'))
            n.update(numero.encode('utf-8'))
            nonce = n.hexdigest()
            linea = ("REGISTER sip:" + mi_usuario + ":" + mi_puerto +
                     " SIP/2.0\r\n" + "Expires: " + OPCION + "\r\n" +
                     'Authorization: Digest response="' + nonce + '"\r\n')
            print("Enviando: " + linea)
            my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
            escribe_log(linea, "envio", IP_regproxy + ":" +
                        str(puerto_regproxy))
            data = my_socket.recv(1024)
            print('Recibido -- ', data.decode('utf-8'))
            respuesta_server = data.decode('utf-8')
            escribe_log(respuesta_server, "recibo", IP_regproxy + ":"
                        + str(puerto_regproxy))
    elif METODO == "invite":
        linea = ("INVITE sip:" + OPCION + " SIP/2.0\r\n"
                 + "Content-type: application/sdp\r\n\r\n" +
                 "v=0\r\n" + "o=" + mi_usuario + " " + mi_IP + "\r\n" +
                 "s=misesion\r\n" + "t=0\r\n" + "m=audio " + puerto_RTP +
                 " RTP\r\n")
        print("Enviando: " + linea)
        my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
        escribe_log(linea, "envio", IP_regproxy + ":" + str(puerto_regproxy))
        data = my_socket.recv(1024)
        print('Recibido -- ', data.decode('utf-8'))
        respuesta_server = data.decode('utf-8')
        datos = respuesta_server.split(" ")
        escribe_log(respuesta_server, "recibo", IP_regproxy + ":"
                    + str(puerto_regproxy))
        if len(datos) == 11 and datos[5] == "200":
            ip_destino = datos[8].split('\r')[0]
            linea = ("ACK sip:" + OPCION + " SIP/2.0\r\n")
            print("Enviando: " + linea)
            my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
            escribe_log(linea, "envio", IP_regproxy + ":"
                        + str(puerto_regproxy))
            aEjecutar = ("mp32rtp -i " + ip_destino + " -p " + datos[9] + " < "
                         + audio_path)
            print("ejecutando " + aEjecutar)
            os.system(aEjecutar)
        else:
            msg_error = "Error, usuario no encontrado"
            escribe_log(msg_error, "error")
    elif METODO == "bye":
        linea = ("BYE sip:" + OPCION + " SIP/2.0\r\n")
        print("Enviando: " + linea)
        my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
        escribe_log(linea, "envio", IP_regproxy + ":" + str(puerto_regproxy))
        data = my_socket.recv(1024)
        print('Recibido -- ', data.decode('utf-8'))
    else:
        print("metodo no valido")

    print("Terminando socket...")
    escribe_log("Finishing...", "otro")

print("Fin.")
