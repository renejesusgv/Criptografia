# -*- coding: UTF-8 -*-
import base64
import json
import time
import unicodedata
import os
import sys
from Configuracion import Configuracion
from Usuario import Usuario

##################Configuracion#####################
'''
    * direccion_ip : (string) xxx.xxx.xxx.xxx (IPv4)
    * puerto : (int)
'''

direccion_ip = "187.236.215.36"
puerto = 3001

################Variables Globales##################

configuracion = Configuracion(direccion_ip, puerto)

####################################################

def bienvenida():
    print "..####...##..##...####...######."
    print ".##..##..##..##..##..##....##..."
    print ".##......######..######....##..."
    print ".##..##..##..##..##..##....##..."
    print "..####...##..##..##..##....##..."
    print "................................"
    print\
        ".#####...#####....####...##..##..######...####...######...####...........######..######..##..##...####...##." \
        "...."
    print\
        ".##..##..##..##..##..##...####...##......##..##....##....##..##..........##........##....###.##..##..##..##." \
        "...."
    print\
        ".#####...#####...##..##....##....####....##........##....##..##..........####......##....##.###..######..##." \
        "...."
    print\
        ".##......##..##..##..##....##....##......##..##....##....##..##..........##........##....##..##..##..##..##." \
        "...."
    print\
        ".##......##..##...####.....##....######...####.....##.....####...........##......######..##..##..##..##..###" \
        "###."
    print"..........................................................................................................." \
         ".....\n"
    return

def menu_principal():
    """
    Despliega el menu principal del chat.
    Ejecuta la funcion ejecutar_accion con la opción elegida.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    bienvenida()
    print "Escribe una opción:"
    print "1.- ¿Registrarte?"
    print "2.- Ya cuentas con un usuario."
    opcion = raw_input("\t>> ")
    ejecutar_accion(opcion)
    return

def ejecutar_accion(opcion):
    """
    Ejecuta la accion escogida por el usuario.
    :param opcion La opcion escogida
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    if opcion == '1':  # registrar al usuario
        registra_nuevo_usuario()
        return
    if opcion == '2':
        inicia_sesion()
        os.system('cls' if os.name == 'nt' else 'clear')
        return
    print "Opción invalida, intenta de nuevo"
    time.sleep(2)
    menu_principal()
    return

def pedir_mensajes(user):
    """
    Muestra los mensajes de este objeto usuario
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("**********************MENSAJES**********************\n")
    msjs = user.dame_mensajes()["mensajes"]
    if len(msjs) > 0:
        for m in msjs:
            # Vemos si ya existe el archivo entre estos usuarios
            if os.path.exists(user.nombre + "_" + m['origen'] + "_values"):
                f = json.load(open(user.nombre + "_" + m['origen'] + "_values", "r"))
                user.krecib = gestiona_llave(user, m['origen'], f, False)

            else:  # Se crea el archivo de sesión, nunca se envió un mensaje a ese usuario
                user.crea_sesion_b(m['origen'], base64.b64decode(m['llave_efimera']),
                                   base64.b64decode(m['llave_identidad']))
                f = json.load(open(user.nombre + "_" + m['origen'] + "_values", "r"))
                user.genera_kenviar_krecibir(user.secreto, False)
                # Se escriben kenv y krecib
                f['kenv'] = base64.b64encode(user.kenv)
                f['krecib'] = base64.b64encode(user.krecib)
                json.dump(f, open(user.nombre + "_" + m['origen'] + "_values", "w"))

            descifrado = user.descifra_mensaje(m['mensaje'])
            print "-----------------------------------------------------------------"
            print "\tHora: " + m['hora']
            print "\tOrigen: " + m['origen']
            print "\tMensaje : " + descifrado
            print ".---------------------------------------------------------------*"

        raw_input("presiona una tecla para continuar...")
        return menu_sesion(user)
    else:
        print "- No tienes mensajes pendientes -"
        time.sleep(1.5)
        return menu_sesion(user)


def gestiona_llave(user, destino, dic_info, is_envio):
    """
    Gestiona qué llave se debe enviar para continuar con la conversación
    :param is_envio: True si la llave a derivar e spara enviar
    :param user: quien envía
    :param destino: cadena con el nombre destino
    :param dic_info: el diccionaro con los datos entre los usuarios
    :return: la llave para envío de mensaje
    """
    if dic_info['establecida']:
        if is_envio:
            dic_info['kenv'] = \
                user.deriva_kllave(base64.b64decode(dic_info["kenv"]), True)
            res = dic_info['kenv']
            dic_info['kenv'] = base64.b64encode(dic_info['kenv'])
        else:
            dic_info['krecib'] = \
                user.deriva_kllave(base64.b64decode(dic_info["krecib"]), False)
            res = dic_info['krecib']
            dic_info['krecib'] = base64.b64encode(dic_info['krecib'])
        # Se actualiza el archivo
        json.dump(dic_info, open(user.nombre+"_"+destino+"_values", "w"))
        return res
    else:  # Si no está establecida la comunicación
        if is_envio:
            if dic_info['tipo'] == "B":
                dic_info['establecida'] = True
                json.dump(dic_info, open(user.nombre + "_" + destino + "_values", "w"))
            return base64.b64decode(dic_info["kenv"])
        else:
            if dic_info['tipo'] == "A":
                dic_info['establecida'] = True
                json.dump(dic_info, open(user.nombre + "_" + destino + "_values", "w"))
            return base64.b64decode(dic_info["krecib"])


def enviar_mensaje(user, destino):
    """
    Envía un mensaje desde este usuario al destino
    :param user: El objeto usuario
    :param destino: Al usuario al que se pretende que vaya
    :return:
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    # Se verifica si el usuario existe
    verif = user.solicita_llaves(destino)
    if verif['ok']:  # Usuario existente
        # Se verifica si ya se estableció la conexión previamente con el otro usuario y user fue alic
        if os.path.exists(user.nombre+"_"+destino+"_values"):
            f = json.load(open(user.nombre+"_"+destino+"_values", "r"))
            print "Escribe tu mensaje:\n"
            mensaje = raw_input("\t>> ")
            if len(mensaje) > 0:
                llave = gestiona_llave(user, destino, f, True)
                print "mensaje"
                print mensaje
                user.envia_mensaje(mensaje, destino, llave)
                print "¡Mensaje enviado!"
                time.sleep(1.5)
                return menu_sesion(user)
            else:
                print " - No se pueden enviar mensajes de longitud 0 - "
                time.sleep(1.5)
                return enviar_mensaje(user, destino)

        # Si no hay sesion con el otro usuario se crea siendo alice
        else:
            scrt = user.crea_sesion_a(destino)
            print "Escribe tu mensaje:\n"
            mensaje = raw_input("\t>> ")
            if len(mensaje) > 0:
                print "Enviando mensaje..."
                time.sleep(0.2)
                di = json.load(open(user.nombre+"_"+destino+"_values", 'r'))
                user.genera_kenviar_krecibir(scrt, True)
                # Se guardan las nuevas llaves
                di["kenv"] = base64.b64encode(user.kenv)
                di["krecib"] = base64.b64encode(user.krecib)
                # Se actualizan las llaves
                json.dump(di, open(user.nombre+"_"+destino+"_values", 'w'))
                # Envía el mensaje con la primer derivacion
                user.envia_mensaje(mensaje, destino, user.kenv)
                print "¡Mensaje enviado!"
                time.sleep(3)
                return menu_sesion(user)
            else:
                print " - No se pueden enviar mensajes de longitud 0 - "
                time.sleep(1.5)
                return enviar_mensaje(user, destino)

    else:  # Usuario inexistente
        print "Usuario inexistente, regresando..."
        time.sleep(1.5)
        return menu_sesion(user)


def menu_sesion(user):
    """
    Gestiona el menú dentro de la sesion de un usuario
    :param user: Objeto Usuario que inició la sesión
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print "¿Qué quieres hacer?"
    time.sleep(0.2)
    print "1.- Ver tus mensajes pendientes"
    time.sleep(0.2)
    print "2.- Enviar un mensaje a un usuario"
    time.sleep(0.2)
    print "3.- Terminar programa"
    time.sleep(0.2)
    opcion = raw_input("\t>> ")
    if opcion == '1':
        pedir_mensajes(user)
    elif opcion == '2':
        print "\t¿Cuál es su nombre de usuario?"
        destino = raw_input("\t\t>> ")
        if destino == user.nombre:
            print "No te puedes enviar mensajes a tí mismo"
            time.sleep(1.5)
            return menu_sesion(user)
        else:
            enviar_mensaje(user, destino)
    elif opcion == '3':
        print "Cerrando..."
        user.cerrar_conexion()
        time.sleep(1.5)
        return sys.exit()
    else:
        print "Opción inválida"
        time.sleep(1)
        return menu_sesion(user)


def logguear_usuario(nombre):
    """
    La vista par logguear al usuario
    :param nombre: El nombre con el que se autentica
    """
    print "conectando con el servidor..."
    time.sleep(0.2)
    user = Usuario(nombre, configuracion)
    print "Saludando al servidor..."
    time.sleep(0.2)
    if user.saludo()['ok']:
        print "Usuario reconocido, autenticando..."
        time.sleep(0.2)
        if user.autenticar()['ok']:
            print "Identidad verificada correctamente"
            time.sleep(0.2)
            print "Redirigiendo al menú de sesión..."
            time.sleep(0.5)
            return menu_sesion(user)
        else:
            print "Identida no verificada. Desconectando"
            raw_input("presiona alguna tecla terminar...")
            return sys.exit()
    else:
        print "Problemas con el usuario. Desconectando"
        time.sleep(0.2)
        user.cerrar_conexion()
        raw_input("presiona alguna tecla para terminar...")
        return sys.exit()


def inicia_sesion():
    os.system('cls' if os.name == 'nt' else 'clear')
    print "Ingresa tu nombre de usuario"
    nombre = raw_input("\t>> ")
    if nombre:
        logguear_usuario(nombre)
        return
    else:
        print "No especificaste un nombre valido, intentalo de nuevo"
        time.sleep(1.5)
        inicia_sesion()
    return "pass"


def registra_nuevo_usuario():
    os.system('cls' if os.name == 'nt' else 'clear')
    print "Ingresa tu nombre de usuario"
    nombre = raw_input("\t>> ")
    if nombre:
        usuario = Usuario(nombre, configuracion)
        if usuario.registro()['ok']:
            print "Usuario registrado... esperando respuesta del servidor"
            if usuario.saludo()['ok']:
                print "Registro completado. Redireccionando al menú principal"
                time.sleep(3)
                usuario.cerrar_conexion()
                return menu_principal()
            else:
                print "Error al registrarse, intentalo mas tarde"
                return menu_principal()
        else:
            print("Nombre invalido, intenta de nuevo")
            time.sleep(3)
            return registra_nuevo_usuario()
    else:
        print "Nombre inválido, intenta de nuevo"
        time.sleep(3)
        return registra_nuevo_usuario()


if __name__ == '__main__':
    menu_principal()

