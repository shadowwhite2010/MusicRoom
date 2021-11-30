import chat
import json
import time
import Pyro4
import threading
import socket as sk
import datetime
import threading, wave, pyaudio,pickle,struct


class Lobby():
	def __init__(self, hostname='localhost', port=25501):
		"""hostname : str (default='localhost') - address which the daemon should run.
		- port : int (default=25501) - port which the daemon should run.
		- logs chats and hosts it. use 'register' to create new chats."""
		self.chats = []
		self.daemon = Pyro4.Daemon(host=hostname, port=port)

	def daemon_loop(self):
		"""Starts the daemon"""
		self.d_thread = threading.Thread(target=self.daemon.requestLoop)
		self.d_thread.daemon = True
		self.d_thread.start()


	def register(self, chat_p=None):
		"""Logs a new chat to the daemon and hosts it.
		- chat_p : None - A nameless chat is created and hosted.
		- chat_p : str - creates a chat named as {chat_p} and registers it.
		- chat_p : chat.Chat - registers the chat."""
		if isinstance(chat_p, str):
			chat_p = chat.Chat(name=chat_p)
			self.register(chat_p)
		elif chat_p is None:
			chat_p = chat.Chat()
			self.register(chat_p)
		elif isinstance(chat_p, chat.Chat):
			uri = str(self.daemon.register(chat_p))
			self.chats.append((chat_p.name, uri))

class Server():
	def __init__(self, hostname='localhost', port=25500, lobby_port=25501):
		"""This class works as a DNS server for the chats.
		- hostname : str (default='localhost') - address which the server should run.
		- port : int (default=25500) - port which the server should run.
		- lobby_port : int (default=25501) - port which the daemon should run."""
		self.rooms_and_client={}

		print("Setting up daemon")
		self.lobby = Lobby(hostname=hostname, port=lobby_port)
		self.lobby.daemon_loop()

		print("Setting up server")
		self._server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		self._server.bind((hostname, port))

	def run(self):
		self.s_thread = threading.Thread(target=self._run)
		self.s_thread.daemon=True
		self.s_thread.start()

	def _run(self):
		print("Running server")
		self._server.listen()

		while True:
			con, cliente = self._server.accept()

			# Respond the client with server clock time
			con.send(str(datetime.datetime.now()).encode())
			
			mensagem = con.recv(2048).decode('utf-8')

			if mensagem == 'GET uri':
				con.send(json.dumps(self.lobby.chats).encode())

			#recieving the selected music room name and username
			client_string=con.recv(2048).decode('utf-8')
			client_room, client_name=tuple(map(str, client_string.split(', ')))
			
			# finding uri of users room
			temp_uri=''
			for item in self.lobby.chats:
				if item[0]==client_room:
					temp_uri=item[1]
					break
			
			# getting object of that room
			music_room=Pyro4.Proxy(temp_uri)

			#Appending client to particular room
			if client_room not in self.rooms_and_client:
				
				self.rooms_and_client[client_room]=(music_room, [])
			
			self.rooms_and_client[client_room][1].append((client_name,con))

			# create thread to watch music room by client
			if len(self.rooms_and_client[client_room][1])==1:
				self.th=threading.Thread(target = self.watch_rooms, args=(client_room, ))
				self.th.start()
				self.rooms_and_client[client_room][0].elect_admin()

			# con.close()

	def watch_rooms(self, room):
		while True:
			if len(self.rooms_and_client)!=0:
				# print(self.rooms_and_client[room][0].get_play_state())

				if self.rooms_and_client[room][0].get_play_state()=='play':
					for c in self.rooms_and_client[room][1]:
						if c[0] not in self.rooms_and_client[room][0].get_usernames():
							self.rooms_and_client[room][1].remove(c)

					for c in self.rooms_and_client[room][1]:
						self.t=threading.Thread(target = self.send_music(c[1], 'audio_files/music4.wav'))
						self.t.start()
						self.rooms_and_client[room][0].set_play_state()


	# def watch_rooms(self):
	# 	while True:
	# 		if len(self.rooms_and_client)!=0:
	# 			for room in self.rooms_and_client:
	# 				# print(self.rooms_and_client[room][0].get_play_state())
	# 				if self.rooms_and_client[room][0].get_play_state()=='play':
	# 					print('play me ghus gaya')
	# 					for c in self.rooms_and_client[room][1]:
	# 						self.t=threading.Thread(target = self.send_music(c[1], 'audio_files/music2.wav'))
	# 						self.t.start()
	# 						self.rooms_and_client[room][0].set_play_state()
	# 						print("music sent to one client")
						
						

	def send_music(self, client_socket, music_file):
		CHUNK = 1024
		wf = wave.open(music_file, 'rb')

		data = None
		while True:
			if client_socket:
				while True:
				
					data = wf.readframes(CHUNK)
					
					if data==b'':
						break

					a = pickle.dumps(data)
					message = struct.pack("Q",len(a))+a
					client_socket.sendall(message)
			break

		


	def create_chat(self, chat_name):
		self.lobby.register(chat_name)

if __name__=="__main__": 
	server = Server()
	server.create_chat('Music Room 1')
	server.create_chat('Music Room 2')
	server.create_chat('Music Room 3')

	# # create thread to watch music room by client
	# server.th=threading.Thread(target = server.watch_rooms)
	# server.th.start()

	server.run()

	#keeping server alive
	while True:
		time.sleep(30)