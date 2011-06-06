#!/usr/bin/env python
import os

slice_size = 240*1024

desc = open("musica.mp3.desc","r")

name = desc.readline().strip("\n")
file_out = open("out_"+name,"w")

lines = desc.readlines()
desc.close()
for line in lines:
    file_tmp = open(line.strip("\n"),"r")
    piece = file_tmp.read()
    file_out.write(piece)
    file_tmp.close()
    

file_out.close()
