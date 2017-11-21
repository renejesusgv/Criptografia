#!/usr/bin/python3
# -*- coding: utf-8 -*-
import math
import random
'''Implementar todas las funciones que faltan. La descripcion
   se encuentra en el pdf de la practica. Perdon por la falta de acentos.'''

def mcd(a, b):
    ''' Calcula el maximo comun divisor de a y b '''
    assert(a >= b)
    if a % b == 0:
        return b
    else:
        return mcd(b, a % b)

def xmcd(a, b):
    ''' Calcula el maximo comun divisor de a y b, ademas devuelve
        X y Y tales que mcd(a,b) = Xa + Yb '''
    assert a >= b
    if a % b == 0:
        return (b, 0, 1)
    else:
        q = a / b
        r = a % b
        d, X, Y = xmcd(b, r)
        return (d, Y, X-Y*q)

def inverso_mod(a, N):
    ''' Calcula el inverso multiplicativo de a en los enteros modulo N '''
    (d, X, Y) = xmcd(N, a)
    if d != 1:
        print(str(a) + ' no tiene inverso modulo ' + str(N))
    else:
        return Y % N

''' Dado mod N, base a en Zn y exponente b > 0,
calcula a^b mod N '''
def potencia_mod(a, b, N):
    x = a
    t = 1
    while b > 0:
        if b % 2 == 1:
            t = t*x % N
            b = b-1
        x = x**2 % N
        b = b/2
    return t

def test_fermat(p):
    ''' Si p es compuesto devuelve False. Si p es primo, puede devolver True o False
        Repetir esto varias veces da mayor certeza cuando p es primo '''
    from random import randint
    a = randint(2,p-1)
    if (a**(p-1)) % p != 1: # Exponenciacion lenta a^(p-1) mod p. Cambiar por potencia_mod
        return False
    else:
        return True

def separa_dos(N):
    ''' Separa N en una potencia de 2 y un numero impar,
        es decir, devuelve (r,u) tales que N = (2^r)*u
        donde u es impar y por tanto r es lo mayor posible '''
    if N % 2 != 0:
            return (0, N)
    else:
        r,u = separa_dos(N/2)
        return r+1, u

def raiz_entera(k, n): # suponemos n > 0
    u, s, k1 = n, n+1, k-1
    while u < s:
        s = u
        u = (k1 * u + n // u ** k1) // k
    return s

def primos(n):
    i, p, ps, m = 0, 3, [2], n // 2
    criba = [True] * m
    while p <= n:
        if criba[i]:
            ps.append(p)
            for j in range((p*p-3)//2, m, p):
                criba[j] = False
        i, p = i+1, p+2
    return ps

def es_potencia(N):
        for i in primos(int(math.ceil(math.log(N, 2)))):
                x = raiz_entera(i, N)
                if pow(x, i) == N:
                    return True
        return False

def test_miller_rabin(p, t=5):
    ''' Test de primalidad de Miller-Rabin,
    devuelve True en caso de que probablemente lo sea y
    False cuando es un numero compuesto '''
    if p & 1 == 0:        #equivalente a p % 2
        return False
    if es_potencia(p):
        return False
    r = 0
    u = p -1
    while p & 1 == 0:
        r = r+1
        u = u >> 1          #dividir entre 2
    for j in range(t):
        a = random.randint(1,p-1)
        x = potencia_mod(a,u,p)
        if x != 1 and x + 1 != p:
            for i in range(1, r-1):    #iteramos con las posibles potencias
                x = potencia_mod(x,2,p)
                if x == 1:
                    return False
                if x == p-1:
                    continue
            return False
    return True

def genera_primo(n=20):
    while True:
        possibly_prime = random.randint(2**(n-1), 2**(n)-1)
        if test_miller_rabin(possibly_prime):
            return possibly_prime

def phi(n):
    ''' funcion que calcula la phi de euler dada la multiplicacion de factores primos'''
    y = n
    i = 2
    while i <= n:
        if n & 1 == 0 and i != 2: continue #si es par, no es primo exceptuando el 2
        if n % i == 0 and test_miller_rabin(i):
            y *= 1 - 1.0/i
        i+=1
    return int(y)

def egcd(a, b):
    ''' Calcula el maximo comun divisor de a y b g, ademas devuelve
            X y Y tales que mcd(a,b) = Xa + Yb '''
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    ''' Calcula el inverso multiplicativo de a en los enteros modulo m '''
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

def genera_modulo(n=20):
    ''' Genera N = pq, un producto de primos distintos, 2^(n-1) <= p,q <= 2^n
        e = 2**16 + 1 y
        d = e^(-1) mod phi(N) '''
    p = genera_primo(n)
    q = genera_primo(n)
    while p == q:
        q = genera_primo(n)
    N = p*q
    m = int((p-1)*(q-1))
    e = (2**16) +1
    d = modinv(e, m)
    return (N,e,d)

'''Funcion que devuelve un primo aleatorio de tamaño n bytes
    apartir de leer hexadecimales aleatorios de /dev/urandom,
    y aplicar la funcion OR bit por bit con
    el numero 127 (suponiendo n = 16, 16*8 - 1 = 127), si el numero resultante
    es primo, lo devuelve, si no repite el ciclo.
'''
def funcion(n=16):
    r = open('/dev/urandom')
    p = 4
    while not test_miller_rabin(p):
        s1 = r.read(n).encode('hex')
        s2 = int(s1, 16)
        p = s2 | (1 << (n*8-1))
    return p

'''dada una tupla (N,e) y un mensaje m'''
def cifrar_rsa(tupla,m):
    return potencia_mod(m, tupla[1], tupla[0])

def descifrar_rsa(tupla, c):
    return potencia_mod(c, tupla[1], tupla[0])

def diffieHellman():
    def bob_recibe(triplet):
        print("Bob recibe p,g, X")
        b = random.randint(2, triplet[0]-2)
        print("Bob genero b: %d" %b)
        Y = potencia_mod(triplet[1], b, triplet[0])
        print("Bob calculo Y")
        k1 = potencia_mod(triplet[2], b, triplet[0])
        print("Bob calculo k1: %d" %k1)
        print("Bob envia Y")
        return Y

    def alice_envia():
        p = genera_primo()
        print("Alice genero p: %d" %p)
        g = 2
        print("Alice tomo g: %d" %g)
        a = random.randint(2, p-2)
        print("Alice genero a: %d" %a)
        X = potencia_mod(g,a,p)
        print("Alice calculo X")
        print("Alice envia p,g X")
        Y = bob_recibe((p,g,X))
        print("Alice recibe Y")
        k2 = potencia_mod(Y,a,p)
        print("Alice calculo k2: %d" %k2)

    alice_envia()

def main():
    #TEST CIFRADO RSA
    print("RSA")
    m = 51164240
    print("Mensaje: %d" %m)
    tupla = genera_modulo()
    c = cifrar_rsa((tupla[0], tupla[1]), m)
    print("Mensaje cifrado: %d" %c)
    d = descifrar_rsa((tupla[0], tupla[2]), c)
    print("Mensaje descifrado: %d" %d)
    print("\n")
    #TEST DIFFIE-HELLMAN
    print("Diffie-Hellman")
    diffieHellman()
    print("\n")
    #TEST Prints
    print(separa_dos(88))
    print(genera_modulo(20))

if __name__ == "__main__":
    main()