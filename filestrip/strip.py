#!/usr/bin/env python
import os
import hashlib
from os.path import getsize

slice = (240*1024)
arq = "musica.mp3"

file = open(arq,"r")

size = getsize(arq)

num_files = size / (slice)

descriptor = open(arq+".desc","w")
descriptor.write(arq+"\n")

for i in range(0,num_files+1):
    piece = file.read(slice)
    key = hashlib.sha1()
    key.update(piece)
    name=key.hexdigest()
    descriptor.write(name+".dat\n")
    print name
    new_file = open(str(name)+".dat","w")
    new_file.write(piece)
    new_file.close()

file.close()
descriptor.close()
