#!/usr/bin/env python
# -*- coding: utf-8 -*-

def isPrime(a):
    return all(a % i for i in xrange(2, a))

def factorize(n):
    factors = []

    p = 2
    while True:
        while(n % p == 0 and n > 0): #while we can divide by smaller number, do so
            factors.append(p)
            n = n / p
        p += 1  #p is not necessary prime, but n%p == 0 only for prime numbers
        if p > n / p:
            break
    if n > 1:
        factors.append(n)
    return factors

def calculateLegendre(a, p):
    """
    Calculate the legendre symbol (a, p) with p is prime.
    The result is either -1, 0 or 1
    """
    if a >= p or a < 0:
        return calculateLegendre(a % p, p)
    elif a == 0 or a == 1:
        return a
    elif a == 2:
        if p%8 == 1 or p%8 == 7:
            return 1
        else:
            return -1
    elif a == p-1:
        if p%4 == 1:
            return 1
        else:
            return -1
    elif not isPrime(a):
        factors = factorize(a)
        product = 1
        for pi in factors:
            product *= calculateLegendre(pi, p)
        return product
    else:
        if ((p-1)/2)%2==0 or ((a-1)/2)%2==0:
            return calculateLegendre(p, a)
        else:
            return (-1)*calculateLegendre(p, a)

def computeOrder(q, a, b):
    sum = 0
    for x in range(0,q):
        sum += calculateLegendre((x**3)+(a*x)+b, q)
    return q + 1 + sum

def computeComplementaryOrder(q, a, b):
    sum = 0
    for x in range(0,q):
        sum += 1 - calculateLegendre((x**3)+(a*x)+b, q)
    return 1 + sum

if __name__ == "__main__":
    import doctest
    doctest.testmod()