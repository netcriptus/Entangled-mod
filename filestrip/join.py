#!/usr/bin/env python
import os

slice = (240*1024)

desc = open("musica.mp3.desc","r")

name = desc.readline().rstrip()
file_out = open("out_"+name,"w")

lines = desc.readlines()
for line in lines:
    file_tmp = open(line.rstrip(),"r")
    piece = file_tmp.read()
    file_out.write(piece)
    file_tmp.close()
    

file_out.close()
