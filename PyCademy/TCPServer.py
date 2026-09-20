# TCPServer.py
# Created On: 2014/11/14
# Created By: Rohtash Singh
#
# Simple TCP Server
# http://twistedmatrix.com/trac/wiki/Downloads
# Twisted is a event-based engine that makes it easy to build web applications using TCP, UDP, SSH, IRC, or FTP.
# Twisted is built around a design pattern you may have heard of called the reactor pattern.
# This pattern is simple but powerful. It starts a loop, waits for events, and reacts to them.
#
# To test, open write the command:
# telnet localhost 1601
# you can open multiple instances and type message like "iam:rohtash" or "msg:hello"
#
# Control of the program
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor

class IPhoneChat(Protocol):
	def connectionMade(self):
		self.factory.clients.append(self)
		print "Clients are:", self.factory.clients
		print "Connection Established!"
	
	def connectionLost(self, reason):
		self.factory.clients.remove(self)

	def dataReceived(self, data):
		tokens = data.split(':')
		print tokens
		if len(tokens) > 1:
			command = tokens[0]
			contents = tokens[1]

			message = ""
			if "iam" == command:		
				self.name = contents
				message = self.name + " has joined"

			elif "msg" == command:
				message = self.name + " : " + contents
			
			print message

			for client in self.factory.clients:
				client.sendMessage(message)

	def sendMessage(self, message):
		self.transport.write(message + '\n')




factory = Factory()
factory.protocol = IPhoneChat
factory.clients = []
reactor.listenTCP(1601, factory)
print "IPhoneChat server has started!"
reactor.run()

