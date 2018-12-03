#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys

# Cliente UDP simple.

try:
    PETICION = sys.argv[1]
    UA_RECEPTOR = sys.argv[2]
    RECEPTOR = UA_RECEPTOR.split('@')[0]
    IP = UA_RECEPTOR.split('@')[1].split(':')[0]
    PORT = int(UA_RECEPTOR.split(':')[1])
except (IndexError, ValueError):
    sys.exit("Usage: python3 client.py method receiver@IP:SIPport")


# Contenido que vamos a enviar
# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP, PORT))

    linea = (PETICION + " sip:" + RECEPTOR + "@" + IP + " SIP/2.0\r\n")

    print("Enviando: " + linea)
    my_socket.send(bytes(linea, 'utf-8') + b'\r\n')
    data = my_socket.recv(1024)

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
