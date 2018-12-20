#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import time
from xml.dom import minidom
import socketserver
import hashlib
import json
import random

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
    mi_log.write(hora + " " + linea_log + "\r\n")

    
class ServerHandler(socketserver.DatagramRequestHandler):
    
    dicc_registro = {}
    passwords = {}
    nonce = []
    
    def handle(self):
        while 1:
            self.json2passwd()
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read().decode('utf-8')
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            datos = line.split(" ")
            info_usuario = {}
            if datos[0] == 'REGISTER':
                print("Llega " + line[:-4])
                receptor = datos[1].split(':')[1].split('@')[0]
                usuario = datos[1].split(':')[1]
                ip_ua = datos[1].split('@')[1]
                expires = datos[3].split('\r')[0]
                escribe_log(line, "recibo", ip_ua)
                if line[:-4] == ("REGISTER sip:" + receptor + "@" + ip_ua +
                                 " SIP/2.0\r\nExpires: " + expires):
                    passwd_cliente = self.passwords[usuario]
                    numero = str(random.getrandbits(128))
                    n = hashlib.sha256()
                    n.update(passwd_cliente.encode('utf-8')) 
                    n.update(numero.encode('utf-8'))
                    self.nonce.append(n.hexdigest())
                    respuesta_reg = "SIP/2.0 401 Unauthorized\r\n"
                    respuesta_reg += 'WWW Authenticate: Digest nonce="'
                    respuesta_reg += (numero + '"\r\n\r\n')
                    self.wfile.write(bytes(respuesta_reg, 'utf-8'))
                    escribe_log(respuesta_reg, "envio", ip_ua)
                    if expires == 0:
                        del self.dicc_registro[usuario]
                elif line[:-4] == ("REGISTER sip:" + receptor + "@" + ip_ua +
                                 " SIP/2.0\r\nExpires: " + expires + "\r\n" +
                                 'Authorization: Digest response="' + self.nonce[0] + '"'):
                    respuesta_ok = "SIP/2.0 200 OK\r\n\r\n"
                    self.wfile.write(bytes(respuesta_ok, 'utf-8'))
                    escribe_log(respuesta_ok, "envio", ip_ua)
                    
                    info_usuario['usuario'] = usuario
                    info_usuario["IP"] = self.client_address[0]
                    info_usuario['puerto'] = self.client_address[1]
                    self.dicc_registro[usuario] = info_usuario
                    tiempo_inicio = time.strftime('%Y-%m-%d %H:%M:%S',
                                               time.gmtime(time.time()))
                    self.dicc_registro[usuario]["inicio"] = tiempo_inicio
                    tiempo_fin = time.strftime('%Y-%m-%d %H:%M:%S',
                                               time.gmtime(time.time() + int(expires)))
                    self.dicc_registro[usuario]["expires"] = tiempo_fin
                else:
                    self.wfile.write(b"SIP/2.0 400 Bad request\r\n\r\n")  
            elif datos[0] == 'INVITE':
                print("Llega " + line[:-4])
                info = line.split('=')
                ua_envia = info[2].split(' ')[0]
                ua_recibe = datos[1].split(':')[1]
                print(self.dicc_registro)
                if ua_envia in self.dicc_registro:
                    print("esta registrado el que envia")
                    if ua_recibe in self.dicc_registro:
                        print("esta registrado el que recibe")
                        print(ua_recibe)
            elif datos[0] == 'ACK':
                print("llega " + line)
                aEjecutar = ('mp32rtp -i 127.0.0.1 -p 23032 < ' + FICH_AUDIO)
                print("ejecutando " + aEjecutar)
                os.system(aEjecutar)
            elif datos[0] == 'BYE':
                print("llega " + line)
                receptor = datos[1].split(':')[1].split('@')[0]
                ip_ua = datos[1].split('@')[1]
                if line[:-4] == (datos[0] + " sip:" + receptor + "@" + ip_ua +
                                 " SIP/2.0"):
                    self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                else:
                    self.wfile.write(b"SIP/2.0 400 Bad request\r\n\r\n")
            else:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed")
    
    def elimina_expires(self):
        """elimina clientes que han expirado en el diccionario"""
        hora_actual = time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.gmtime(time.time()))
        for usuario in list(self.dicc_registro.keys()):
            if hora_actual >= self.dicc_registro[usuario]['expires']:
                del self.dicc_registro[usuario]
    
    def json2passwd(self):
        try:
            with open("passwords.json") as f:
                datos_json = json.load(f)
                self.passwords = datos_json
        except:
            pass

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
    escribe_log("Starting...", "otro")
    
    serv = socketserver.UDPServer((mi_IP, mi_puerto), ServerHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")


