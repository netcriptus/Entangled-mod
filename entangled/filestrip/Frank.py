#!/usr/bin/env python
# encoding: utf-8

class Frank(object):
  def __init__(self):
    self.file_name = None


  def neat(self, file_parts, save_path):
    file_out = open(save_path + self.file_name, "w")
    full_file = "".join(file_parts)
    file_out.write(full_file)
    file_out.close()
    
  def parseDescriptor(self, descriptor):
    self.file_name = descriptor[0].strip("\n")
    pieces_list = [piece.strip("\n") for piece in descriptor[1::]]
    return pieces_list