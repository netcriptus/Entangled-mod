#!/usr/bin/env python
# encoding: utf-8

import hashlib
from os.path import getsize

slice_size = 240*1024
arq = "musica.mp3"

fp = open(arq,"r")

size = getsize(arq)

num_files = size / slice_size

descriptor = open(arq+".desc","w")
descriptor.write(arq+"\n")

for i in range(0,num_files+1):
    piece = fp.read(slice_size)
    key = hashlib.sha1()
    key.update(piece)
    name=key.hexdigest()
    descriptor.write(name+".dat\n")
    new_file = open(str(name)+".dat","w")
    new_file.write(piece)
    new_file.close()

fp.close()
descriptor.close()
