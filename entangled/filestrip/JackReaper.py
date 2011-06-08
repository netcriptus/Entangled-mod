#!/usr/bin/env python
# encoding: utf-8

import hashlib
from math import ceil
from os.path import getsize

class JackReaper(object):
  """This class is supposed to tear a tear apart a large file into many 256kb
  files, and creator a descriptor which gives us the names of each part"""
  def __init__(self):
    self.slice_size = 256*1024 #256 kb
    


  def __getKey(self, value):
    """Given a value, it will return a sha1 digest for that value"""
    sha = hashlib.sha1()
    sha.update(value)
    return sha.digest()

  def reap(self, arq):
    """Given a file, it will be cut down to 256kb pieces. A descriptor will be
    created and yielded"""
    
    fp = open(arq,"r")
    size = getsize(arq)
    num_files = ceil(size / float(self.slice_size))
    descriptor = []
    
    for i in range(num_files):
      value = fp.read(self.slice_size)
      key=self.__getKey(value)
      yield (key, value)
      descriptor.append(key)
      
    fp.close()
    descriptor = descriptor
    key = self.__getKey(str(descriptor))
    yield (key, str(descriptor))
  
  
