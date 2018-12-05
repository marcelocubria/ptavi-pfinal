#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.dom import minidom

# Cliente UDP simple.

try:
    config = sys.argv[1]
    METODO = sys.argv[2]
    OPCION = sys.argv[3]
except (IndexError, ValueError):
    sys.exit("Usage: python uaclient.py config metodo opcion")


# Contenido que vamos a enviar
# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    archivo_xml = minidom.parse(config)
    #obtengo la informacion de mi usuario y servidor
    account = archivo_xml.getElementsByTagName('account')
    uaserver= archivo_xml.getElementsByTagName('uaserver')
    mi_usuario = account[0].attributes['username'].value
    mi_server = uaserver[0].attributes['ip'].value
    if mi_server == '':
        mi_server = "127.0.0.1"
    mi_puerto = uaserver[0].attributes['puerto'].value
    
    #obtengo informacion del servidor regproxy y me conecto
    regproxy = archivo_xml.getElementsByTagName('regproxy')
    IP_regproxy = regproxy[0].attributes['ip'].value
    puerto_regproxy = int(regproxy[0].attributes['puerto'].value)
    
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_regproxy, puerto_regproxy))

    linea = (METODO + " sip:" + mi_usuario + "@" + mi_server +
             ":" + mi_puerto + " SIP/2.0\r\n" + "Expires: " + OPCION + "\r\n")

    print("Enviando: " + linea)
    my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
    try:
        data = my_socket.recv(1024)
    except ConnectionRefusedError:
        sys.exit("conexion rechazada")

    print('Recibido -- ', data.decode('utf-8'))
    respuesta_server = data.decode('utf-8')
    if respuesta_server == ("SIP/2.0 100 Trying\r\n\r\n" +
                            "SIP/2.0 180 Ringing\r\n\r\n" +
                            "SIP/2.0 200 OK\r\n\r\n"):
        linea = ("ACK sip:" + RECEPTOR + "@" + IP + " SIP/2.0\r\n")
        print("Enviando: " + linea)
        my_socket.send(bytes(linea, 'utf-8') + b'\r\n')

    print("Terminando socket...")

print("Fin.")
