#!/usr/bin/env python
# encoding: utf-8

class Frank(object):
  """This class is supposed to mount again a file separeted in many small files"""
  def __init__(self):
    self.file_name = None


  def neat(self, file_parts, save_path):
    """
    Given the parts of the file, and a path to save, this function creates
    a new file, which is the assembly of all the file_parts
    
    @file_parts: the parts of a bigger file, already sorted
    @save_path: the complete path in the system to save the new file. Remember
    to put a / in the end
    """
  
    file_out = open(save_path + self.file_name, "w")
    full_file = "".join(file_parts)
    file_out.write(full_file)
    file_out.close()
    
  def parseDescriptor(self, descriptor):
    """Given a descriptor, this function parses its information, keeps the
    filename and returns a list of keys that form that file."""
    
    self.file_name = descriptor[0].strip("\n")
    pieces_list = [piece.strip("\n") for piece in descriptor[1::]]
    return pieces_list