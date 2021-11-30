from Pyro4.core import Daemon
import server
import Pyro4
from playsound import playsound

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Chat():
	def __init__(self, name=None):
		self._name = name
		self.messages = []
		self.users = {}
		self.usernames = []
		self.user_msg=''
		self.admin=0
		self.admin_name=''
		# self.play_music('music2.wav')


	def play_music(self, music_name):
		# for playing note.mp3 file
		playsound(f'audio_files/{music_name}')
		print('playing sound using  playsound')

	def elect_admin(self):
		msg_count={}
		if len(self.messages)>0:
			for s in self.messages:
				x=s.split()
				if x[0][-1]==':':
					x[0]=x[0][ :-1]
				if x[0] in self.usernames:
					if x[0] not in msg_count:
						msg_count[x[0]]=0
					msg_count[x[0]]=msg_count[x[0]]+1

			most_msg=''
			c=0
			for name in msg_count:
				if msg_count[name]>c:
					most_msg=name
					c=msg_count[name]
			
			for i in range (0,len(self.usernames)):
				if self.usernames[i]==most_msg:
					self.admin=i
					self.admin_name=most_msg
					break
			
			print(f'{self.usernames[self.admin]} is the admin')
			# uri=''
			# for u in self.users:
			# 	if self.users[u].username==self.usernames[self.admin]:
			# 		uri=u
			# 		break
			
			# self.send_message(f'{self.usernames[self.admin]} is the admin', uri)


	def connect(self, uri):
		"""Method for remote uses to call when wants to connect to this chat."""

		#the client uri is passed so it's methods can be called later.
		client = Pyro4.Proxy(uri)

		#If username taken or uri already in the chat -> quit.
		if uri in self.users or client.username in self.usernames:
			return False

		print(f"client with username '{client.username}' has connected.")

		self._send_message(f'{client.username} has joined the chat')

		#adding client to chat's users
		self.users[uri] = client
		self.usernames.append(client.username)
		if self.admin_name=='':
			self.admin_name=client.username

		if len(self.messages) < 21:
			return self.messages
		return self.messages[-20:]

	def disconnect(self, uri):
		"""Method for remote uses to call when wants to disconnect from this chat."""
		print(f"Disconnecting {self.users[uri].username}")
		self._send_message(f"User '{self.users[uri].username}' has disconnected.", uri)

		temp=self.users[uri].username

		#clearing the data:
		self.usernames.remove(self.users[uri].username)
		self.users[uri].kill()
		del(self.users[uri])
		if self.admin_name==temp:
			self.elect_admin()
		# daemon = Pyro4.Daemon()
		# daemon.unregister(uri)

	def send_message(self, message, uri):

		#if the uri is unknown, the message must not be sent
		if uri not in self.users:
			return

		#if the uri doesn't fits the username, someone is pretending to be someone else.
		sender = message.split(':')[0]
		if sender != self.users[uri].username:
			return

		#actually sending message.
		self._send_message(message, uri)

	def _send_message(self, message, uri=None):
		"""Method invisible for remote users due to starting with '_'.
		register the message and sends to every user connected.
		If it's a system message and must be sent to everybody, no uri is provided."""

		if len(self.usernames)!=0 and message==f'{self.usernames[self.admin]}: play':
			# self.play_music('music2.wav')
			self.user_msg='play'

		self.messages.append(message)
		for user_uri, user in self.users.items():
			if user_uri == uri: continue
			user.incoming_message(message)

	def get_play_state(self):
		return self.user_msg

	def set_play_state(self):
		self.user_msg=''

	def get_usernames(self):
		return self.usernames

	def get_admin(self):
		return self.admin

	def __str__(self):
		return f"chat named {self.name}"


	@property
	def name(self):
		return self._name