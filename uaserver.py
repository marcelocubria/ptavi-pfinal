#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import socket
import sys
from xml.dom import minidom
import time
import socketserver

def escribe_log(linea, tipo, ippuerto = 0):
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
    
class UAHandler(socketserver.DatagramRequestHandler):
    
    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read().decode('utf-8')
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            datos = line.split(" ")
            ip_port_rp = (self.client_address[0] + ":" + str(self.client_address[1]))
            escribe_log(line, "recibo", ip_port_rp)
            if datos[0] == 'INVITE':
                respuesta_invite = ("SIP/2.0 100 Trying\r\n\r\n")
                respuesta_invite += ("SIP/2.0 180 Ringing\r\n\r\n")
                respuesta_invite += ("SIP/2.0 200 OK\r\n\r\n")
                sdp = ("Content-type: application/sdp\r\n\r\n" + "v=0\r\n" 
                           + "o=" + mi_usuario + " " + mi_IP +"\r\n" +
                           "s=misesion\r\n" + "t=0\r\n" + "m=audio " 
                           + mi_puerto + " RTP\r\n")
                respuesta_invite += sdp
                self.wfile.write(bytes(respuesta_invite, 'utf-8'))
                escribe_log(respuesta_invite, "envio", ip_port_rp)
                print("recibo y respondo")
if __name__ == "__main__":
    try:
        config = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit("Usage: python uaserver.py config")
        
    print("Listening...")
    
    archivo_xml = minidom.parse(config)
    xml_log = archivo_xml.getElementsByTagName('log')
    ruta_log = xml_log[0].attributes['path'].value
    mi_log = open(ruta_log, "w")
    uaserver= archivo_xml.getElementsByTagName('uaserver')
    mi_IP = uaserver[0].attributes['ip'].value
    if mi_IP == '':
        mi_IP = "127.0.0.1"
    mi_puerto = uaserver[0].attributes['puerto'].value
    account_xml = archivo_xml.getElementsByTagName('account')
    mi_usuario = account_xml[0].attributes['username'].value
    
    serv = socketserver.UDPServer((mi_IP, int(mi_puerto)), UAHandler)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")

