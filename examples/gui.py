#! /usr/bin/env python
#
# This library is free software, distributed under the terms of
# the GNU Lesser General Public License Version 3, or any later version.
# See the COPYING file included in this archive
#

from os import path
import sys, gtk, gobject, cairo
sys.path.append(path.join(path.dirname(__file__), "../"))
import pygtk
pygtk.require('2.0')
import math

from twisted.internet import gtk2reactor
#import entangled.kademlia.protocol
gtk2reactor.install()
import twisted.internet.reactor
import entangled.dtuple

import entangled.kademlia.contact
import entangled.kademlia.msgtypes

import hashlib

from entangled import JackRipper


class EntangledViewer(gtk.DrawingArea):
    def __init__(self, node, *args, **kwargs):
        gtk.DrawingArea.__init__(self, *args, **kwargs)
        self.node = node
        self.timeoutID = gobject.timeout_add(5000, self.timeout)
        self.comms = {}
        self.incomingComms = {}
        # poison the node with our GUI hooks
        self.node._protocol.__gui = self
        self.node._protocol.__realSendRPC = self.node._protocol.sendRPC
        self.node._protocol.sendRPC = self.__guiSendRPC

        self.node._protocol.__realDatagramReceived = self.node._protocol.datagramReceived
        self.node._protocol.datagramReceived = self.__guiDatagramReceived
        self.msgCounter = 0
        self.printMsgCount = False

    def __guiSendRPC(self, contact, method, args, rawResponse=False):
        #print 'sending'
        self.drawComms(contact.id, method)
        self.msgCounter += 1
        return self.node._protocol.__realSendRPC(contact, method, args, rawResponse)
    
    def __guiDatagramReceived(self, datagram, address):
        msgPrimitive = self.node._protocol._encoder.decode(datagram)
        message = self.node._protocol._translator.fromPrimitive(msgPrimitive)
        if isinstance(message, entangled.kademlia.msgtypes.ErrorMessage):
            msg = 'error'
        elif isinstance(message, entangled.kademlia.msgtypes.ResponseMessage):
            msg = 'response'
        else:
            msg = message.request
        self.drawIncomingComms(message.nodeID, msg)
        return self.node._protocol.__realDatagramReceived(datagram, address)
    
    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }
    
    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        # Create the cairo context
        cr = self.window.cairo_create()
        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())
    
    def draw(self, cr, width, height):
        # draw a rectangle for the background            
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # a circle for the local node
        cr.set_source_rgb(1.0, 0.0, 0.0)
        radius = min(width/5, height/5)
        
        w = width/2
        h = height/2
        s = radius / 2.0 - 20
        radial = cairo.RadialGradient(w/2, h/2, s, w+w/2, h+h/2, s)
        radial.add_color_stop_rgb(0,  0.6, 0, 0.2)
        radial.add_color_stop_rgb(1,  0.1, 0.2, 0.9)
        
        cr.arc(w, h, s, 0, 2 * math.pi)
        cr.set_source(radial)
        cr.fill()
        
        if len(self.comms):
            cr.set_line_width(5)
            cr.set_source_rgba(0, 0.7, 0.8, 0.5)
        else:
            cr.set_source_rgba(0.0, 0.0, 0.4, 0.7)
        cr.arc(w, h, s+1, 0, 2 * math.pi)
        
        cr.stroke()
        cr.set_line_width(2)
        
        blips = []
        kbucket = {}
        for i in range(len(self.node._routingTable._buckets)):
            for contact in self.node._routingTable._buckets[i]._contacts:    
                blips.append(contact)
                kbucket[contact.id] = i
        # ...and now circles for all the other nodes
        if len(blips) == 0:
            spacing = 180
        else:
            spacing = 360/(len(blips))
        degrees = 0
        radius = min(width/6, height/6) / 3 - 20
        if radius < 5:
            radius = 5
        r = width/2.5
        for blip in blips:
            x = r * math.cos(degrees * math.pi/180)
            y = r * math.sin(degrees * math.pi/180)    

            w = width/2 + x
            h = height/2 + y
            if w < 0:
                w = radius
            elif w > width:
                w = width-radius
            if h < 0:
                h = radius
            elif h > height:
                h = height - radius
                

            radial = cairo.RadialGradient(w-w/2, h-h/2, 5, w+w/2, h+h/2, 10)
            radial.add_color_stop_rgb(0,  0.4, 1, 0)
            radial.add_color_stop_rgb(1,  1, 0, 0)
            cr.arc(w, h, radius, 0, 2 * math.pi)
            cr.set_source(radial)
            cr.fill()
            
            cr.set_source_rgb(0.2,0.2,0.2)
            cr.set_font_size(12.0)
            cr.move_to(w+radius+5, h-10)
            cr.set_font_size(12.0)
            cr.show_text(blip.address)
            cr.move_to(w+radius+5, h+5)
            cr.show_text(str(blip.port))
            cr.set_source_rgb(1,1,1)
            
            cr.set_font_size(8.0)
            cr.set_source_rgb(0.4,0.4,0.4)
            cr.move_to(w+radius+5, h+17)
            cr.show_text('k-bucket: %d' % kbucket[blip.id])
            cr.set_font_size(14.0)
            cr.stroke()
            
            if blip.id in self.incomingComms:
                cr.set_source_rgba(0.8, 0.0, 0.0, 0.6) 
                cr.move_to(width/2, height/2)
                cr.line_to(w, h)
                cr.stroke()
                
                cr.move_to(width/2+x/3, height/2+y/3)
                cr.show_text(self.incomingComms[blip.id])
                cr.stroke()
                cr.set_line_width(5)
            
            else:
                cr.set_source_rgba(0.4, 0.0, 0.0, 0.7)
                
            cr.arc(w, h, radius+1, 0, 2 * math.pi)
            cr.stroke()
             
            if blip.id in self.comms:
                cr.set_line_width(5)
                cr.set_source_rgba(0.0, 0.7, 0.8, 0.4)
                cr.move_to(width/2, height/2)
                cr.line_to(w, h)
                cr.stroke()
                
                cr.set_source_rgba(0.0, 0.3, 0.8, 0.7)
                cr.move_to(width/2+x/1.2, height/2+y/1.2)
                cr.show_text(self.comms[blip.id])
                cr.stroke()
            cr.set_line_width(2)
            degrees += spacing
        
        cr.set_line_width(5)
        cr.set_source_rgba(0.6, 0.6, 0.6, 0.4)
        i = 0
        for lostComm in self.comms:
            if lostComm not in blips:
                cr.move_to(width/2, height/2)
                cr.line_to(100*i, 0)
                cr.stroke()
            i += 1
        
        if self.printMsgCount == True:
            cr.set_source_rgb(0.2,0.2,0.2)
            cr.set_font_size(12.0)
            cr.move_to(20, 20)
            cr.show_text('Messages sent: %d' % self.msgCounter)
            cr.stroke()
        

    def timeout(self):
        """ Timeout handler to update the GUI """
        #print 'timeout'
        self.window.invalidate_rect(self.allocation, False)
        return True
    
    def drawMsgCounter(self):
        self.printMsgCount = True
        gobject.timeout_add(3000, self.removeMsgCount)
        
    def drawComms(self, contactID, msg):
        if contactID not in self.comms:
            self.comms[contactID] = msg
            gobject.timeout_add(750, self.removeComm, contactID)
            self.window.invalidate_rect(self.allocation, False)
    
    def drawIncomingComms(self, contactID, msg):
        if contactID not in self.incomingComms:
            self.incomingComms[contactID] = msg
            gobject.timeout_add(750, self.removeIncomingComm, contactID)
            self.window.invalidate_rect(self.allocation, False)
    
    def removeIncomingComm(self, contactID):
        try:
            del self.incomingComms[contactID]
        finally:
            self.window.invalidate_rect(self.allocation, False)
            return False
    
    def removeComm(self, contactID):
        try:
            del self.comms[contactID]
        finally:
            self.window.invalidate_rect(self.allocation, False)
            return False
        
    def removeMsgCount(self):
        if self.printMsgCount == True:
            self.printMsgCount = False
            self.msgCounter = 0
            self.window.invalidate_rect(self.allocation, False)
        return False
        
    

class EntangledViewerWindow(gtk.Window):
    def __init__(self, node):
        gtk.Window.__init__(self)
        
        self.node = node
        self.connect("delete-event", gtk.main_quit)
        
        # Layout the window
        vbox = gtk.VBox(spacing=3)
        self.add(vbox)
        vbox.show()
    
        # Add the view screen
        self.viewer = EntangledViewer(node)
        self.viewer.show()
        vbox.pack_start(self.viewer)
    
        # Add the controls
        notebook = gtk.Notebook()
        notebook.set_tab_pos(pos=gtk.POS_TOP)
        notebook.show()
        vbox.pack_start(notebook,expand=False, fill=False)

        #trabalho
        trabalhoVbox = gtk.VBox(spacing=3)
        trabalhoVbox.show()
        notebook.append_page(trabalhoVbox, gtk.Label('Trabalho Kademlia'))
        frame = gtk.Frame()
        frame.set_label('Armazenamento')
        frame.show()
        trabalhoVbox.pack_start(frame)
        
        trabalhoTabVbox = gtk.VBox(spacing=3)
        trabalhoTabVbox.show()
        frame.add(trabalhoTabVbox)

        # Armazena
        hbox = gtk.HBox(False, 8)
        hbox.show()
        label = gtk.Label("Arquivo:")
        hbox.pack_start(label, False, False, 0)
        label.show()
        #entryKey = gtk.Entry()
        #hbox.pack_start(entryKey, expand=True, fill=True)
        #entryKey.show()
        dialog = chooser = gtk.FileChooserDialog("Selecione...",action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        file_button = gtk.FileChooserButton(dialog)
        file_button.set_width_chars(10)
        hbox.pack_start(file_button, False, False, 0)
        file_button.show()
        button = gtk.Button('Enviar')
        hbox.pack_start(button, expand=False, fill=False)
        button.connect("clicked", self.armazenaArquivo, dialog.get_filename)
        button.show()
        trabalhoTabVbox.pack_start(hbox, expand=False, fill=False)

        # Busca
        hbox = gtk.HBox(False, 8)
        hbox.show()
        label = gtk.Label("Palavra Chave:")
        hbox.pack_start(label, False, False, 0)
        label.show()
        entryKey = gtk.Entry()
        hbox.pack_start(entryKey, expand=True, fill=True)
        entryKey.show()
        button = gtk.Button('Procurar')
        hbox.pack_start(button, expand=False, fill=False)
        vbox = gtk.VBox(False, 5)
        vbox.show()
        button.connect("clicked", self.showSearch, vbox, entryKey.get_text)
        button.show()
        trabalhoTabVbox.pack_start(hbox, expand=False, fill=False)
        trabalhoTabVbox.pack_start(vbox, expand=False, fill=False)
                
        
    def showSearch(self, sender, trabalhoVbox, getKey):
        key = getKey()
        h = hashlib.sha1()
        h.update(key)
        hKey = h.digest()

        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def showValue(result):
            val = result.values()
            print val
            # limpa a busca
            for child in trabalhoVbox:
                trabalhoVbox.remove(child)
            # mostra a busca
            for i in result.values():
                hbox = gtk.HBox(False, 4)
                hbox.show()
                palavra = i[0]
                label = gtk.Label(palavra)
                hbox.pack_start(label, False, False, 0)
                label.show()
                button = gtk.Button("Baixar")
                button.connect("clicked", self.getFile, i[1], i[0])
                hbox.pack_start(button, False, False, 0)
                button.show()
                trabalhoVbox.pack_start(hbox, expand=False, fill=False)

        def error(failure):
            #print 'GUI: an error occurred:', failure.getErrorMessage()
            sender.set_sensitive(True)
            for child in trabalhoVbox:
                trabalhoVbox.remove(child)
            hbox = gtk.HBox(False, 4)
            hbox.show()
            label = gtk.Label('Nao foi encontrado')
            hbox.pack_start(label, False, False, 0)
            label.show()
            trabalhoVbox.pack_start(hbox, expand=False, fill=False)
            
        df = self.node.iterativeFindValue(hKey)
        df.addCallback(showValue)
        df.addErrback(error)
  
    def getFile(self, sender, filekey, nomeFunc):
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        nome_arq = nomeFunc


        def getValue(result):
            self.viewer.printMsgCount = True
            fp = open(nome_arq,"a+")
            for item in  result.values():
                fp.write(item)
            fp.close()

        def showValue(result):
            self.viewer.printMsgCount = True
            for items in result.values():
                for item in eval(items):
                    df1 = self.node.iterativeFindValue(item)
                    df1.addCallback(getValue)
                    df1.addErrback(error)

        def error(failure):
            print 'GUI: an error occurred:', failure.getErrorMessage()
        
        if not path.exists(nome_arq):
            df = self.node.iterativeFindValue(filekey)
            df.addCallback(showValue)
            df.addErrback(error)
    
    def armazenaArquivo(self, sender, valueFunc):        
        nome_arq = valueFunc()
        
        jack = JackRipper()

        def completed(result):
            self.viewer.printMsgCount = True
            print "enviado"

        for piece in jack.rip(nome_arq):
            hKey = piece[0]
            value = piece[1]

            self.viewer.msgCounter = 0
            self.viewer.printMsgCount = False

            df = self.node.iterativeStore(hKey, value)
            df.addCallback(completed)

        # ------ Chaves
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False

        nome_arq = path.basename(nome_arq)
        value = []
        value.append(nome_arq)
        value.append(hKey)
        h = hashlib.sha1()
        h.update(nome_arq)
        cKey = h.digest()

        df = self.node.iterativeStore(cKey, value)
        df.addCallback(completed)

    def publishData(self, sender, nameFunc, valueFunc):
        name = nameFunc()
        value = valueFunc()
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def completed(result):
            self.viewer.printMsgCount = True
        df = self.node.publishData(name, value)
        df.addCallback(completed)
    
    def storeValue(self, sender, keyFunc, valueFunc):
        key = keyFunc()
        
        h = hashlib.sha1()
        h.update(key)
        hKey = h.digest()
        
        value = valueFunc()
        
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        
        def completed(result):
            self.viewer.printMsgCount = True
        df = self.node.iterativeStore(hKey, value)
        df.addCallback(completed)

    def getValue(self, sender, entryKey, showFunc):
        sender.set_sensitive(False)
        key = entryKey.get_text()
        entryKey.set_sensitive(False)
        h = hashlib.sha1()
        h.update(key)
        hKey = h.digest()
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def showValue(result):
            sender.set_sensitive(True)
            entryKey.set_sensitive(True)
            if type(result) == dict:
                value = result[hKey]
                if type(value) != str:
                    value = '%s: %s' % (type(value), str(value))
            else:
                value = '---not found---'
            showFunc(value)
            self.viewer.printMsgCount = True
        def error(failure):
            print 'GUI: an error occurred:', failure.getErrorMessage()
            sender.set_sensitive(True)
            entryKey.set_sensitive(True)
        
        df = self.node.iterativeFindValue(hKey)
        df.addCallback(showValue)
        df.addErrback(error)
    
    def deleteValue(self, sender, keyFunc):
        key = keyFunc()
        
        h = hashlib.sha1()
        h.update(key)
        hKey = h.digest()
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def completed(result):
            self.viewer.printMsgCount = True
        df = self.node.iterativeDelete(hKey)
        df.addCallback(completed)
        
    def searchForKeywords(self, sender, entryKeyword, showFunc):
        sender.set_sensitive(False)
        keyword = entryKeyword.get_text()
        entryKeyword.set_sensitive(False)
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def showValue(result):
            sender.set_sensitive(True)
            entryKeyword.set_sensitive(True)
            sourceListString = ''
            for name in result:
                sourceListString += '%s\n' % name
            result = sourceListString[:-1]
            showFunc(result)
            self.viewer.printMsgCount = True
        def error(failure):
            print 'GUI: an error occurred:', failure.getErrorMessage()
            sender.set_sensitive(True)
            entryKeyword.set_sensitive(True)
        
        df = self.node.searchForKeywords(keyword)
        df.addCallback(showValue)
        df.addErrback(error)
        
    def removeData(self, sender, nameFunc):
        name = nameFunc()
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def completed(result):
            self.viewer.printMsgCount = True
        df = self.node.removeData(name)
        df.addCallback(completed)

    ###### Tuple Space Controls ######
    def putTuple(self, sender, tupleFunc):
        dTuple = self._tupleFromStr(tupleFunc())
        if dTuple == None:
            return
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def completed(result):
            self.viewer.printMsgCount = True
        df = self.node.put(dTuple)
        df.addCallback(completed)
        
    def _tupleFromStr(self, text):
        tp = None
        try:
            exec 'tp = %s' % text
            if type(tp) != tuple:
                raise Exception
        except Exception:
            dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                        "Please enter a valid Python tuple,\ne.g. (1, 'abc', 3.14)")
            dialog.set_title('Error')
            dialog.run()
            dialog.destroy()
        finally:
            return tp
        
    def getTuple(self, sender, entryTemplate, showFunc, blocking):
        template = self._tupleFromStr(entryTemplate.get_text())
        if template == None:
            return
        sender.set_sensitive(False)
        entryTemplate.set_sensitive(False)
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def showValue(result):
            sender.set_sensitive(True)
            entryTemplate.set_sensitive(True)
            if result == None:
                result = '---no matching tuple found---'
            else:
                result = str(result)
            showFunc(result)
            self.viewer.printMsgCount = True
        def error(failure):
            print 'GUI: an error occurred:', failure.getErrorMessage()
            sender.set_sensitive(True)
            entryTemplate.set_sensitive(True)
        
        if blocking == True:
            df = self.node.get(template)
        else:
            df = self.node.getIfExists(template)
        df.addCallback(showValue)
        df.addErrback(error)
        
    def readTuple(self, sender, entryTemplate, showFunc, blocking):
        template = self._tupleFromStr(entryTemplate.get_text())
        if template == None:
            return
        sender.set_sensitive(False)
        entryTemplate.set_sensitive(False)
        self.viewer.msgCounter = 0
        self.viewer.printMsgCount = False
        def showValue(result):
            sender.set_sensitive(True)
            entryTemplate.set_sensitive(True)
            if result == None:
                result = '---no matching tuple found---'
            else:
                result = str(result)
            showFunc(result)
            self.viewer.printMsgCount = True
        def error(failure):
            print 'GUI: an error occurred:', failure.getErrorMessage()
            sender.set_sensitive(True)
            entryTemplate.set_sensitive(True)
        
        if blocking == True:
            df = self.node.read(template)
        else:
            df = self.node.readIfExists(template)
        df.addCallback(showValue)
        df.addErrback(error)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage:\n%s UDP_PORT  [KNOWN_NODE_IP  KNOWN_NODE_PORT]' % sys.argv[0]
        print 'or:\n%s UDP_PORT  [FILE_WITH_KNOWN_NODES]' % sys.argv[0]
        print '\nIf a file is specified, it should containg one IP address and UDP port\nper line, seperated by a space.'
        sys.exit(1)
    try:
        int(sys.argv[1])
    except ValueError:
        print '\nUDP_PORT must be an integer value.\n'
        print 'Usage:\n%s UDP_PORT  [KNOWN_NODE_IP  KNOWN_NODE_PORT]' % sys.argv[0]
        print 'or:\n%s UDP_PORT  [FILE_WITH_KNOWN_NODES]' % sys.argv[0]
        print '\nIf a file is specified, it should contain one IP address and UDP port\nper line, seperated by a space.'
        sys.exit(1)
    
    if len(sys.argv) == 4:
        knownNodes = [(sys.argv[2], int(sys.argv[3]))]
    elif len(sys.argv) == 3:
        knownNodes = []
        f = open(sys.argv[2], 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            ipAddress, udpPort = line.split()
            knownNodes.append((ipAddress, int(udpPort)))
    else:
        knownNodes = None

    node = entangled.dtuple.DistributedTupleSpacePeer( udpPort=int(sys.argv[1]) )
    
    window = EntangledViewerWindow(node)

    window.set_default_size(640, 640)
    window.set_title('Entangled Viewer - DHT on port %s' % sys.argv[1])

    window.present()
    
    node.joinNetwork(knownNodes)
    twisted.internet.reactor.run()
