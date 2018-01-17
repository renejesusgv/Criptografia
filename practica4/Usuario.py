# -*- coding: UTF-8 -*-
import nacl.utils
import nacl.encoding
import nacl.signing
import socket
import sys
import json
import base64
from Configuracion import *
from nacl.public import PrivateKey, Box
from nacl.hash import sha256, sha512
from nacl.secret import SecretBox
from nacl.public import PublicKey
from nacl.encoding import RawEncoder


def int_to_bytes(n):
    """
    Función para convertir un int en dos bytes
    :param n: int a onvertir
    :return: bytearray de dos elementos con el número
    """
    b = bytearray([0, 0])
    b[1] = n & 0xFF
    n >>= 8
    b[0] = n & 0xFF
    return b


def crea_paquete(diccionario):
    """
    :param diccionario: Un diccionario de python
    :return: un json con el paquete y el tamanio de bytes que tiene al inicio
    """
    # transforma a json el diccionario
    diccionario_json = json.dumps(diccionario)
    # calcula el tamaño codificado en 2 bytes del json
    size_in_bytes = int_to_bytes(sys.getsizeof(diccionario_json))
    # crea el paquete con el tamaño en byes al inicio
    return size_in_bytes + diccionario_json


class Usuario:

    configuracion = Configuracion

    def __init__(self, nombre, configuracion):
        self.nombre = nombre
        # definimos la configuracion
        Usuario.configuracion = configuracion
        # genera la llave publica y privada
        self.sk = PrivateKey.generate()
        self.pk = self.sk.public_key
        # genera una llave para firmar
        self.sig = nacl.signing.SigningKey.generate()

        # LLAVE PARA PASAR EL RETO SI ERES "EL_CJ_100_real_no_fake_un_link"
        # nacl.signing.SigningKey(base64.b64decode("Afj+pfA5WbJeGCabSBa7kNFXzzZoeHtcuSVxs3nAxtc="))

        # genera una llave para verificar
        self.vk = self.sig.verify_key
        # genera llaves de medio uso
        self.medk_priv = PrivateKey.generate()
        self.medk_pub = self.medk_priv.public_key
        self.medk = self.sig.sign(self.medk_pub.__bytes__())

        # El secreto temporal
        self.secreto = "scrt"

        # El reto que mando el servidor para firmarlo
        self.reto = ""

        # El socket que se tendrá durante toda la conexión
        self.socket_connection = socket.socket()
        self.socket_connection.connect((configuracion.direccion, configuracion.puerto))

        # Los keviar y krecibir TEMPORALES
        self.kenv = ""
        self.krecib = ""

    def saludo(self):
        """
        genera un mensaje tipo saludo al servidor
        :return: Diccionario con tipo = reto si existe el usuario
        """
        # genera el saludo
        saludo = {'tipo': "saludo", 'nombre': self.nombre}
        paquete = crea_paquete(saludo)
        # envía el mensaje
        self.socket_connection.send(paquete)
        # Recibe la respuesta del servidor
        self.socket_connection.recv(2)
        paquete_recibido = json.loads(self.socket_connection.recv(1024))
        if paquete_recibido["ok"]:
            # Existe el usuario, cargamos las llaves
            dicc = json.load(open("keys_"+self.nombre, "r"))

            self.sk = PrivateKey(base64.b64decode(dicc["sk"]))
            self.pk = PublicKey(base64.b64decode(dicc["pk"]))
            self.sig = nacl.signing.SigningKey(base64.b64decode(dicc["sig"]))
            self.vk = nacl.signing.VerifyKey(base64.b64decode(dicc["vk"]))
            self.medk_pub = PublicKey(base64.b64decode(dicc["medk_pub"]))
            self.medk_priv = PrivateKey(base64.b64decode(dicc["medk_priv"]))
            self.medk = base64.b64decode(dicc["medk"])
            # Se asigna el reto
            self.reto = paquete_recibido["reto"]
        else:
            print "Error. El usuario " + self.nombre + " no existe."
        return paquete_recibido

    def autenticar(self):
        """
        Funcion que a partir del reto obtenido en el saludo, lo firma con firma_reto y se autentica al server.
        :param self
        :return: respuesta del servidor
        """
        return self.firma_reto(self.reto)

    def firma_reto(self, reto):
        """
        firma el mensaje reto que envio el servidor en el saludo y lo manda
        :param reto: string que envía el servidor
        :return: respuesta del servidor
        """
        # genera el mensaje
        auth = {"tipo": "telofirmo", "reto_firmado": base64.b64encode(self.sig.sign(base64.b64decode(reto)))}
        paquete = crea_paquete(auth)
        # envía
        self.socket_connection.send(paquete)
        # import pdb; pdb.set_trace()
        # recibe la respuesta
        self.socket_connection.recv(2)
        d = json.loads(self.socket_connection.recv(1024))
        if not d['ok']:
            print d['detalles']
        return d

    def registro(self):
        """
        genera un mensaje de tipo registro con llaves codificadas en base 64
        :return: diccionario oon la respuesta del servidor
        """
        # adjuntar la pre_llave_firmada correcta

        registro = {"tipo": "registro", "nombre": self.nombre,
                    "llave_identidad": base64.b64encode(self.pk.__bytes__()),
                    "llave_identidad_firmar": base64.b64encode(self.vk.__bytes__()),
                    # Cifra la llave de medio uso
                    "pre_llave_firmada": base64.b64encode(self.medk)}

        paquete = crea_paquete(registro)
        # manda por el socket
        self.socket_connection.send(paquete)
        # recibe la respuesta
        self.socket_connection.recv(2)
        resp = json.loads(self.socket_connection.recv(1024))
        if resp["ok"]:
            dicc = {"nombre": self.nombre, "sk": base64.b64encode(self.sk.__bytes__()),
                    "pk": base64.b64encode(self.pk.__bytes__()),
                    "sig": base64.b64encode(self.sig.__bytes__()),
                    "vk": base64.b64encode(self.vk.__bytes__()),
                    "medk_pub": base64.b64encode(self.medk_pub.__bytes__()),
                    "medk_priv": base64.b64encode(self.medk_priv.__bytes__()),
                    "medk": base64.b64encode(self.medk)}

            json.dump(dicc, open("keys_"+self.nombre, "w"))
        else:
            print "Error. El registro fue incorrecto\n" + resp["detalles"]
        return resp


    def solicita_llaves(self, nombre):
        """
        solicita las llaves de un usuario
        :param nombre:
        :return: las llaves en un diccionario o el error
        """
        # Solicita las llaves de usuario con quien se quiere comunicar
        solicitud = {'tipo': "datos_usuario", 'nombre': nombre}
        paquete = crea_paquete(solicitud)
        # envía la solicitud de datos al servidor
        self.socket_connection.send(paquete)
        # recibe la respuesta
        self.socket_connection.recv(2)
        a = self.socket_connection.recv(1024)
        return json.loads(a)

    def crea_sesion_a(self, nombre):
        """
        Se escribe el archivo como nombreA_nombreB_values
        :param nombre: Usuario con quien se desea establecer la comunicación
        :return: devuelve el secreto calculado a partir de las llaves del usuario con el nombre
        especificado
        """
        dicti = self.solicita_llaves(nombre)
        if not dicti["ok"]:
            return "Error:\n" + dicti["detalles"]

        ikb = PublicKey(base64.b64decode(dicti["llave_identidad"]))
        mkb = PublicKey(base64.b64decode(dicti["pre_llave"]))
        # genera la llave efimera
        efk_priv = PrivateKey.generate()
        # calcula el secreto como: DH(IKA,MKB) || DH(EKA, IKB) || DH(EKA,MKB)
        b1 = Box(self.sk, mkb).shared_key()
        b2 = Box(efk_priv, ikb).shared_key()
        b3 = Box(efk_priv, mkb).shared_key()
        secreto = b1 + b2 + b3
        # Genera un diccionario para escribir en un archivo las llaves de Bob
        dicc = {'ikb': base64.b64encode(ikb.__bytes__()), 'mkb': base64.b64encode(mkb.__bytes__()),
                'efk_pub': base64.b64encode(efk_priv.public_key.__bytes__()), 'secreto': base64.b64encode(secreto),
                'kenv': "", 'krecib': "", "establecida": False, "tipo": "A"}
        # escribe el archivo
        json.dump(dicc, open(self.nombre+"_"+nombre+"_values", "w"))
        self.secreto = secreto
        return secreto

    def crea_sesion_b(self, nombre, ek, ik):
        """
        Asigna al secreto de este objeto
        :param nombre: con quien se establece la sesión
        :param ek: Llave efímera de Alice publica
        :param ik: Lave pública de Alice publica
        :return: el secreto calculado a partir de las llaves del usuario ek, ik
        """
        ekk = PublicKey(ek)
        ikk = PublicKey(ik)
        # Se calcula DH(MKB, IKA) || DH(IKB,EKA) || DH(MKB,EKA)
        b1 = Box(self.medk_priv, ikk).shared_key()
        b2 = Box(self.sk, ekk).shared_key()
        b3 = Box(self.medk_priv, ekk).shared_key()
        secreto = b1 + b2 + b3
        # Genera un diccionario para escribir en un archivo el secreto para enviar y recibir mensajes con Alice
        dicc = {'secreto': base64.b64encode(secreto), 'kenv': "", 'krecib': "", "establecida": False, "tipo": "B"}
        # escribe el archivo
        json.dump(dicc, open(self.nombre+"_"+nombre+"_values", "w"))
        self.secreto = secreto
        return secreto

    def envia_mensaje(self, mensaje, nombre_destino, kenviar):
        """
        Envía un mensaje al usuario especificado, si no se ha iniciado una sesion
        también se envía la llave efimera y la llave identidad'''
        :param mensaje: El mensaje al usuario dado, DEBE PASARSE COMO: b'[mensaje]
        :param nombre_destino: Nombre de usuario al que se desea enviar el mensaje
        :param kenviar: La llave actual del mensaje a cifrar
        :return: Diccionario con la respuesta del servidor
        """

        # cifra el mensaje
        sbox = SecretBox(kenviar)
        msj = sbox.encrypt(mensaje)
        # Se lee el archivo entre los usuarios
        data = json.load(open(self.nombre+"_"+nombre_destino+"_values", "r"))
        establecida = data["establecida"]
        # genera el paq. de datos a enviar
        if not establecida:
            llave_efimera = data["efk_pub"]
            paq = {"tipo": "msj", "nombre_destino": nombre_destino, "mensaje": base64.b64encode(msj),
                   "llave_efimera": llave_efimera, "llave_identidad": base64.b64encode(self.pk.__bytes__())}
        else:
            paq = {"tipo": "msj", "nombre_destino": nombre_destino, "mensaje": base64.b64encode(msj)}

        paquete = crea_paquete(paq)
        # envía el msj al servidor
        self.socket_connection.send(paquete)
        self.socket_connection.recv(2)
        return self.socket_connection.recv(1024)


    def dame_mensajes(self):
        """
        Pide los mensajes al servidor
        :return: Json con los mensajes que el servidor tiene para éste usuario
        """
        paq = {'tipo': "dame_mensajes"}
        paquete = crea_paquete(paq)
        self.socket_connection.send(paquete)

        # recibe la respuesta
        self.socket_connection.recv(2)
        d = json.loads(self.socket_connection.recv(65536))  # Valor máximo provisional
        if d["ok"]:
            return d
        else:
            return "ERROR " + d["detalles"]


    def genera_kenviar_krecibir(self, secreto, alice):
        """
        Genera el par de llaves kenviar y krecibir a partir de un secerto
        Asigna los valores correspondientes al objeto
        :param alice: True si eres alice, false e.o.c
        :param secreto: El secreto en comun entre A y B para cifrar los mensajes
        :return: una lista con kenviar y krecibir en este orden
        """
        hash_val = sha512(secreto, encoder=RawEncoder)
        if alice:
            self.kenv = hash_val[:32]
            self.krecib = hash_val[-32:]
        else:
            self.kenv = hash_val[-32:]
            self.krecib = hash_val[:32]
        return hash_val[:32], hash_val[-32:]


    def deriva_kllave(self, kllave, is_kenviar):
        """
        devuelve una la siguiente kllave a partir de aplicar sha256 a una kllave
        :param kllave: Kenviar o krecibir, llaves de 32 bytes
        :param is_kenviar: true si es kenviar, flase en caso contrario
        :return: la siguiente kenviar o krecibir de acuerdo a la entrada
        """
        llave = sha256(kllave, encoder=RawEncoder)
        if is_kenviar:
            self.kenv = llave
        else:
            self.krecib = llave
        return llave


    def descifra_mensaje(self, mensaje):
        """
        Descrifra un mensaje con una Sbox
        :param mensaje: mensaje cifrado en base 64 y con Sbox
        :return: el mensaje descifrado
        """
        sb = SecretBox(self.krecib)
        dec = sb.decrypt(base64.b64decode(mensaje))
        return dec


    def cerrar_conexion(self):
        return  self.socket_connection.close()

