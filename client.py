'''
Universidad del Valle de Guatemala
Redes
Jorge Andres Perez Barrios
Carnet: 16362
'''


from slixmpp import ClientXMPP, clientxmpp
import sys
import logging
import getpass
import asyncio
import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
from xml.etree import ElementTree as ET



if sys.platform == 'win32':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#Clase para registro de usuarios
class SignUp(slixmpp.ClientXMPP):

	def __init__(self, jid, password):
		ClientXMPP.__init__(self, jid, password)

		self.add_event_handler("session_start", self.start)
		self.add_event_handler("register", self.register)

	async def start(self, event):
		self.send_presence()
		await self.get_roster()

		self.disconnect()

	async def register(self, iq):
		resp = self.Iq()
		resp['type'] = 'set'
		resp['register']['username'] = self.boundjid.user
		resp['register']['password'] = self.password
		try:
			await resp.send()
			print("Account created for %s!" % self.boundjid)
			self.disconnect()

		except IqError as e:
			print("Could not register account: %s" %
					e.iq['error']['text'])
			self.disconnect()
			
		except IqTimeout:
			print("No response from server.")
			self.disconnect()
		self.disconnect()
		sys.exit()

'''
Clase de cliente
Contiene las funcionalidades para poder utilizar el chat
-Ver usuarios
-Agregar usuarios
-Mostrar detalles de un contacto
-Mandar mensaje a un usuario
-Ingresar a un room
-Mandar mensaje a un room
-Cambiar estado
-Desconectarse
-Eliminar cuenta
'''

class Client(ClientXMPP):
	#Constructor
	def __init__(self, jid, password, nodo, listado_nodos=[]):
		ClientXMPP.__init__(self, jid, password)
		self.jid = jid
		self.password = password
		self.node = {'nodo': nodo, 'nodo_fuente': "", 'nodo_destino': "", 'saltos': 0, 'distancia': 0, 'mensaje': "", 'listado_nodos': listado_nodos, 'rec': False, 'sent': False}

		self.add_event_handler('session_start', self.session_start)
		self.add_event_handler('receive_message', self.receive)

		self.register_plugin('xep_0030') # Service Discovery		
		self.register_plugin('xep_0045') # Multi-User Chat
		self.register_plugin('xep_0004')
		self.register_plugin('xep_0060')
		self.register_plugin('xep_0199') # Ping

		self.received = set()
		self.presences_received = asyncio.Event()

	'''
	Protocolo de los mensajes
	n_f: nodo fuente
	n_d: nodo destino
	s: saltos
	d: distancia
	m: mensaje

	Cada linea del mensaje debe de estar separada por un slash "/".
	
	Ejemplo de un mensaje:
	n_f: G/n_d: A/s: 2/d: 3/m: Hola mundo
	'''

	#Funcion que recibe mensajes, tanto personales como grupales
	def receive(self, msg):
		if msg['type'] == 'chat' or msg['type'] == 'normal':
			print("***********Mensaje Recibido**************")
			print("De: %(from)s \n %(body)s" %(msg))
			print("*****************************************")
			msg.reply("Mensaje %(body)s enviado correctamente" % msg['body'])

			mens = msg['body'].split("/")

			self.node['nodo_fuente'] = int(mens[0].split(": ")[1])
			self.node['nodo_destino'] = int( mens[1].split(": ")[1])
			self.node['saltos'] = int(mens[2].split(": ")[1])
			self.node['distancia'] = int(mens[3].split(": ")[1])
			self.node['mensaje'] = mens[4].split(": ")[1]
			self.node['rec'] = True




		if msg['type'] == 'groupchat':
			print("***********Mensaje grupal Recibido**************")
			print("De: %(from)s \n %(body)s" %(msg))
			print("************************************************")
			msg.reply("Mensaje %(body)s enviado correctamente" % msg['body'])

	#Inicio: menu asincrono con asyncio
	async def session_start(self, event):
		self.send_presence()
		await self.get_roster()
		
		chat = True
		while chat:
			#if self.node['rec'] == True and self.node['nodo'] != self.node['nodo_fuente'] or self.node['nodo'] != self.node['nodo_destino'] and not self.node['sent']:
			alg = input("Ingrese el algoritmo que desea ejecutar: 1. Flooding 2. Distance Vector Routing 3. ")

			if alg == "1":
				for i in self.node['listado_nodos']:
					self.send_message(mto=i + "@alumchat.xyz", mbody=self.node['mensaje'], mtype='chat')
					self.node['sent'] == True

			
			#8. Desconectarse
			if opcion == "8":
				chat = False
				self.disconnect()
				sys.exit()
			

			else:
				print("Seleccion incorrecta")

if __name__ == '__main__':

	run = True

	while run:
		opcion = input("1. Ingresar \n2. Registrarse \n3. Salir \n")
		if opcion == "1" or opcion == 1:
			jid = input("Username: ")
			jid = jid + '@alumchat.xyz'
			password = getpass.getpass("Password: ")

			node_count = input("Ingrese el numero de nodos conectados a este")
			node_list =[]

			for i in range(node_count - 1):
				node = input("Ingrese el nombre del nodo ", i)
				node_list.append(node)

			xmpp = Client(jid=jid, password=password, nodo=jid, listado_nodos=node_list)
				
			if xmpp.connect() == None:
				xmpp.process()
				
			else:
				print("Error al conectarse")
		
		if opcion == "2" or opcion == 2:
			jid = input("Username: ")
			jid = jid + '@alumchat.xyz'
				
			password = getpass.getpass("Password: ")
			password2 = getpass.getpass("Confirm password: ")

			if password == password2:
			
				xmpp = SignUp(jid, password)
				xmpp.register_plugin('xep_0030') # Service Discovery
				xmpp.register_plugin('xep_0004') # Data forms
				xmpp.register_plugin('xep_0066') # Out-of-band Data
				xmpp.register_plugin('xep_0077') # In-band Registration
				xmpp['xep_0077'].force_registration = True
				if xmpp.connect() == None:
					xmpp.process()
					print("Success")
			else: 
				print("Las contraseñas no coinciden...")
		if opcion == 3 or opcion == "3":
			run = False

