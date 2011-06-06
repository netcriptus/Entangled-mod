#!/usr/bin/env python
# encoding: utf-8

import hashlib
from os.path import getsize

class JackReaper(object):
  def __init__(self):
    self.slice_size = 256*1024 #256 kb
    

  def reap(self, arq):
    fp = open(arq,"r")
    size = getsize(arq)
    num_files = size / slice_size
    descriptor = ""
    
    for i in range(num_files+1):
      piece = fp.read(slice_size)
      yield piece
      key = hashlib.sha1()
      key.update(piece)
      name=key.hexdigest()
      descriptor += name + ".dat\n"
      
    yield descriptor
  
  