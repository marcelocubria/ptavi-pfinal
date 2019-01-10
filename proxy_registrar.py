#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import time
from xml.dom import minidom
import socketserver
import hashlib
import json
import random
import socket


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
    mi_log.write(hora + " " + linea_log + "\r\n")


class ServerHandler(socketserver.DatagramRequestHandler):

    dicc_registro = {}
    passwords = {}
    nonce = []

    def handle(self):
        while 1:
            self.json2passwd()
            self.json2registered()
            self.elimina_expires()
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read().decode('utf-8')
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            datos = line.split(" ")
            info_usuario = {}
            ip_port_ua = (self.client_address[0] + ":"
                          + str(self.client_address[1]))
            if datos[0] == 'REGISTER':
                print("Llega " + line)
                receptor = datos[1].split(':')[1].split('@')[0]
                usuario = datos[1].split(':')[1]
                ip_ua = datos[1].split('@')[1]
                expires = datos[3].split('\r')[0]
                escribe_log(line, "recibo", ip_port_ua)
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
                    escribe_log(respuesta_reg, "envio", ip_port_ua)
                    if expires == 0:
                        del self.dicc_registro[usuario]
                elif line[:-4] == ("REGISTER sip:" + receptor + "@" + ip_ua +
                                   " SIP/2.0\r\nExpires: " + expires + "\r\n" +
                                   'Authorization: Digest response="' +
                                   self.nonce[0] + '"'):
                    respuesta_ok = "SIP/2.0 200 OK\r\n\r\n"
                    self.wfile.write(bytes(respuesta_ok, 'utf-8'))
                    escribe_log(respuesta_ok, "envio", ip_port_ua)
                    info_usuario['usuario'] = usuario
                    info_usuario["IP"] = self.client_address[0]
                    info_usuario['puerto'] = datos[1].split(":")[2]
                    self.dicc_registro[usuario] = info_usuario
                    tiempo_inicio = time.strftime('%Y-%m-%d %H:%M:%S',
                                                  time.gmtime(time.time()))
                    self.dicc_registro[usuario]["inicio"] = tiempo_inicio
                    tiempo_fin = time.strftime('%Y-%m-%d %H:%M:%S',
                                               time.gmtime(time.time() +
                                                           int(expires)))
                    self.dicc_registro[usuario]["expires"] = tiempo_fin
                    del(self.nonce[0])
                else:
                    self.wfile.write(b"SIP/2.0 400 Bad request\r\n\r\n")
                self.register2json()
            elif datos[0] == 'INVITE':
                print("Llega " + line)
                ua_recibe = datos[1].split(':')[1]
                escribe_log(line, "recibo", ip_port_ua)
                try:
                    ip_recibe = self.dicc_registro[ua_recibe]['IP']
                    puerto_recibe = self.dicc_registro[ua_recibe]['puerto']
                    with socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        my_socket.connect((ip_recibe, int(puerto_recibe)))
                        escribe_log(line, "envio", ip_recibe + ':' +
                                    str(puerto_recibe))
                        my_socket.send(bytes(line, 'utf-8'))
                        try:
                            data = my_socket.recv(1024)
                            print('Recibido -- ', data.decode('utf-8'))
                            respuesta_ua = data.decode('utf-8')
                            escribe_log(respuesta_ua, "recibo", ip_recibe + ":"
                                        + str(puerto_recibe))
                            self.wfile.write(data)
                            escribe_log(respuesta_ua, "envio", ip_port_ua)
                        except ConnectionRefusedError:
                            escribe_log("No server listening at " + ip_recibe +
                                        " port " + str(puerto_recibe), "error")
                            pass
                except KeyError:
                    respuesta_ua = "SIP/2.0 404 User not found\r\n\r\n"
                    self.wfile.write(bytes(respuesta_ua, 'utf-8'))
                    escribe_log(respuesta_ua, "envio", ip_port_ua)

            elif datos[0] == 'ACK':
                print("Llega " + line)
                ua_recibe = datos[1].split(':')[1]
                escribe_log(line, "recibo", ip_port_ua)
                ip_recibe = self.dicc_registro[ua_recibe]['IP']
                puerto_recibe = self.dicc_registro[ua_recibe]['puerto']
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sckt2:
                    sckt2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sckt2.connect((ip_recibe, int(puerto_recibe)))
                    escribe_log(line, "envio", ip_recibe + ':' +
                                str(puerto_recibe))
                    sckt2.send(bytes(line, 'utf-8'))
            elif datos[0] == 'BYE':
                print("Llega " + line)
                ua_recibe = datos[1].split(':')[1]
                escribe_log(line, "recibo", ip_port_ua)
                ip_recibe = self.dicc_registro[ua_recibe]['IP']
                puerto_recibe = self.dicc_registro[ua_recibe]['puerto']
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sckt:
                    sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sckt.connect((ip_recibe, int(puerto_recibe)))
                    escribe_log(line, "envio", ip_recibe + ':' +
                                str(puerto_recibe))
                    sckt.send(bytes(line, 'utf-8'))
                    try:
                        data = sckt.recv(1024)
                        print('Recibido -- ', data.decode('utf-8'))
                        respuesta_ua = data.decode('utf-8')
                        escribe_log(respuesta_ua, "recibo", ip_recibe + ":"
                                    + str(puerto_recibe))
                        self.wfile.write(data)
                        escribe_log(respuesta_ua, "envio", ip_port_ua)
                    except ConnectionRefusedError:
                        escribe_log("No server listening at " + ip_recibe +
                                    " port " + str(puerto_recibe), "error")
                        pass
            else:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed")
            self.elimina_expires()

    def elimina_expires(self):
        """elimina clientes que han expirado en el diccionario"""
        hora_actual = time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.gmtime(time.time()))
        for usuario in list(self.dicc_registro.keys()):
            if hora_actual >= self.dicc_registro[usuario]['expires']:
                del self.dicc_registro[usuario]

    def json2passwd(self):
        try:
            with open("passwords") as f:
                datos_json = json.load(f)
                self.passwords = datos_json
        except FileNotFoundError:
            print("error al cargar las contraseñas, fichero erroneo")
            pass

    def json2registered(self):
        try:
            with open("registered.json") as f:
                datos_json = json.load(f)
                self.dicc_registro = datos_json
        except FileNotFoundError:
            print("el fichero de registered.json no existe")
            pass

    def register2json(self):
        with open("registered.json", 'w') as file:
            json.dump(self.dicc_registro, file)


if __name__ == "__main__":
    try:
        config = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python proxy_registrar.py config")

    archivo_xml = minidom.parse(config)
    xml_log = archivo_xml.getElementsByTagName('log')
    ruta_log = xml_log[0].attributes['path'].value
    mi_log = open(ruta_log, "a")
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
    print("Server ServerFBI listening at port " + str(mi_puerto))
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
        escribe_log("Finishing...", "otro")
