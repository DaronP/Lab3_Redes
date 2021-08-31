'''
Universidad del Valle de Guatemala
Redes
Jorge Andres Perez Barrios
Carnet: 16362

Andrea Maria Paniagua Acevedo
Carnet: 18733

Cristopher Jose Rodolfo Barrios Solis 
Carnet: 18207
'''

from argparse import ArgumentParser
from slixmpp import ClientXMPP, clientxmpp
import sys
import logging
import getpass
import asyncio
import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
from xml.etree import ElementTree as ET
import aioconsole
from aioconsole import ainput, aprint

loop = asyncio.get_event_loop()


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
		self.node = {'nodo': nodo, 'nodo_fuente': "", 'nodo_destino': "", 'saltos': 0, 'distancia': 0, 'mensaje': "", 'listado_nodos': listado_nodos, 'alg': 0}

		self.add_event_handler('session_start', self.session_start)
		self.add_event_handler('message', self.message)

		self.register_plugin('xep_0030') # Service Discovery		
		self.register_plugin('xep_0045') # Multi-User Chat
		self.register_plugin('xep_0004')
		self.register_plugin('xep_0060')
		self.register_plugin('xep_0199') # Ping

		self.presences_received = asyncio.Event()

	'''
	Protocolo de los mensajes
	n_f: nodo fuente
	n_d: nodo destino
	s: saltos
	d: distancia
	m: mensaje
	alg: algoritmo

	Cada linea del mensaje debe de estar separada por un slash "/".
	
	Ejemplo de un mensaje:
	n_f: G/n_d: A/s: 2/d: 3/m: Hola mundo/alg: 1
	'''

	#Funcion que recibe mensajes, tanto personales como grupales
	def message(self, msg):
		if msg['type'] == 'chat' or msg['type'] == 'normal':
			print("")
			print("De: %(from)s \n %(body)s" %(msg))
			print("")

			mens = msg['body'].split("/")
			

			self.node['nodo_fuente'] = mens[0].split(": ")[-1]
			self.node['nodo_destino'] = mens[1].split(": ")[-1]
			self.node['saltos'] = int(mens[2].split(": ")[-1])
			self.node['distancia'] = int(mens[3].split(": ")[-1])
			self.node['mensaje'] = mens[4].split(": ")[-1]
			self.node['alg'] = mens[5].split(": ")[-1]
			
			#Aqui van los algoritmos
			#1 = Flooding
			#2 = Distance Vector Routing
			#3 = 

			if (self.node['nodo_destino'] + "@alumchat.xyz") != self.node['nodo']:
				self.node['saltos'] += 1
				

				#Algoritmo Flooding en el lado de los nodos receptores
				if self.node['alg'] == "1":
					for i in self.node['listado_nodos']:
						self.node['distancia'] = self.node['distancia'] + int(i.split(" ")[-1])
						self.send_message(mto=i.split(" ")[0] + "@alumchat.xyz", mbody="n_f: " + self.node['nodo_fuente'] + "/n_d: " + self.node['nodo_destino'] + "/s: " + str(self.node['saltos']) +"/d: "+ str(self.node['distancia']) +"/m: " + self.node['mensaje'] + "/alg: " + self.node['alg'], mtype='chat')
			
				if self.node['alg'] == "2":
					dist_list = list()
					for i in self.node['listado_nodos']:
						dist_list.append(int(i.split(" ")[-1]))
					
					res = dist_list.index(min(dist_list))
					
					self.node['distancia'] = self.node['distancia'] + int(self.node['listado_nodos'].split(" ")[-1])
					self.send_message(mto=self.node['listado_nodos'][res].split(" ")[0] + "@alumchat.xyz", mbody="n_f: " + self.node['nodo_fuente'] + "/n_d: " + self.node['nodo_destino'] + "/s: " + str(self.node['saltos']) +"/d: "+ str(self.node['distancia']) +"/m: " + self.node['mensaje'] + "/alg: " + self.node['alg'], mtype='chat')

			
			else:
				print("\n\n***********Mensaje Recibido**************\nDe: " + self.node['nodo_fuente'] + "\nMensaje: " + self.node['mensaje'] + "\n*****************************************\n\n")



		if msg['type'] == 'groupchat':
			print("\n\n***********Mensaje grupal Recibido**************")
			print("De: %(from)s \n%(body)s" %(msg))
			print("************************************************\n\n")

	#Inicio: menu asincrono con asyncio
	async def session_start(self, event):
		self.send_presence()
		await self.get_roster()
		
		chat = True
		while chat:			
			
			nd = await ainput("Ingrese el nodo destino \n")
			mensaj = await ainput("Ingrese el mensaje \n")
			alg = await ainput("Ingrese el algoritmo que desea ejecutar: 1. Flooding 2. Distance Vector Routing 3.  \n")

			mnsg = "n_f: " + self.boundjid.bare + "/n_d: " + nd + "/s: 1/d: 0/m: " + mensaj + "/alg: " + alg
			
			#Algoritmo Flooding en el lado del nodo fuente
			if alg == "1":
				for i in self.node['listado_nodos']:
					self.send_message(mto=i.split(" ")[0] + "@alumchat.xyz", mbody=mnsg, mtype='chat')
			
			if alg == "2":
					dist_list = list()
					for i in self.node['listado_nodos']:
						dist_list.append(int(i.split(" ")[-1]))
					
					res = dist_list.index(min(dist_list))
					
					self.send_message(mto=self.node['listado_nodos'][res].split(" ")[0] + "@alumchat.xyz", mbody=mnsg, mtype='chat')

			

			
			#8. Desconectarse
			if alg == "8":
				chat = False
				self.disconnect()
				sys.exit()
			

			else:
				aprint("Seleccion incorrecta")



if __name__ == '__main__':
	
	parser = ArgumentParser(description=Client.__doc__)

	# Output verbosity options.
	parser.add_argument("-q", "--quiet", help="set logging to ERROR", action="store_const", dest="loglevel",
	const=logging.ERROR, default=logging.INFO)

	parser.add_argument("-d", "--debug", help="set logging to DEBUG", action="store_const", dest="loglevel",
	const=logging.DEBUG, default=logging.INFO)

	logging.basicConfig(level=logging.DEBUG,
						format='%(levelname)-8s %(message)s')
	args = parser.parse_args()

	run = True

	while run:
		opcion = input("1. Ingresar \n2. Registrarse \n3. Salir \n")
		if opcion == "1" or opcion == 1:
			jid = input("Username: ")
			jid = jid + '@alumchat.xyz'
			password = getpass.getpass("Password: ")

			node_count = input("Ingrese el numero de nodos conectados a este  \n")
			node_list =[]

			for i in range(int(node_count)):
				node = input("Ingrese el nombre del nodo " + str(i+1) + " junto con la distancia separada por un espacio. \n")
				node_list.append(node)

			xmpp = Client(jid=jid, password=password, nodo=jid, listado_nodos=node_list)
			xmpp['feature_mechanisms'].unencrypted_plain = True	
			if xmpp.connect() == None:
				
				loop.run_until_complete(xmpp.process())
				
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

