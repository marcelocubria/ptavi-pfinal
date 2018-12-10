#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import time
import minidom
import socketserver

def escribe_log(linea, tipo, ippuerto = 0):
    hora = time.strftime("%Y%m%d%H%M%S", time.localtime())
    linea = linea.replace("\r\n", " ")
    if tipo == "envio":
        linea_log = ("Sent to " + ippuerto + ": " + linea)
    elif tipo == "recibo":
        linea_log = ()
    elif tipo == "error":
        linea_log = ("Error: " + linea)
    else:
        linea_log = linea
    mi_log.write(hora + " " + linea_log + "\r\n")
    
class ServerHandler(socketserver.DatagramRequestHandler):
    

    def handle(self):
        self.elimina_expires()
    
    def elimina_expires(self):
        """elimina clientes que han expirado en el diccionario"""
        hora_actual = time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.gmtime(time.time()))
        for usuario in list(self.dicc_registro.keys()):
            if hora_actual >= self.dicc_registro[usuario]['expires']:
                del self.dicc_registro[usuario]

if __name__ == "__main__":
    try:
        config = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python proxy_registrar.py config")
    
    print("Server ServerFBI listening at port 5555")
    
    archivo_xml = minidom.parse(config)
    xml_log = archivo_xml.getElementsByTagName('log')
    ruta_log = xml_log[0].attributes['path'].value
    mi_log = open(ruta_log, "w")
    xml_db = archivo_xml.getElementsByTagName('database')
    ruta_db = xml_db[0].attributes['path'].value
    mi_db = open(ruta_db, "w")
    xml_server = archivo_xml.getElementsByTagName('server')
    mi_IP = xml_server[0].attributes['ip'].value
    if mi_IP == '':
        mi_IP = "127.0.0.1"
    mi_puerto = int(xml_server[0].attributes['puerto'].value)
    
    serv = socketserver.UDPServer((mi_IP, mi_puerto), ServerHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")


