arreglo = [9,3,2,5,6,7,10,11,1,24,12]

for i in range(len(arreglo)):
    for j in range(i + 1, len(arreglo)):
        if arreglo[i] > arreglo[j]:
            arreglo[i], arreglo[j] = arreglo[j], arreglo[i]