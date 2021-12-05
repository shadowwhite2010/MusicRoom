import user
import json
import socket as sk
import datetime
from dateutil import parser
from timeit import default_timer as timer
import threading, wave, pyaudio, pickle,struct,os
import Pyro4

delay=0
socket_to_pass=''
user_alive=1
user_uri=''
def chritian(socket):
	request_time = timer()
 
	# receive data from the server
	server_time = parser.parse(socket.recv(1024).decode())
	response_time = timer()
	actual_time = datetime.datetime.now()
 
	print("Time returned by server: " + str(server_time))
 
	process_delay_latency = response_time - request_time
 
	print("Process Delay latency: " + str(process_delay_latency) + " seconds")
 
	print("Actual clock time at client side: " + str(actual_time))
 
	# synchronize process client clock time
	client_time = server_time + datetime.timedelta(seconds = (process_delay_latency) / 2)
 
	print("Synchronized process client time: " + str(client_time))
 
	# calculate synchronization error
	error = actual_time - client_time
	print("Synchronization error : "+ str(error.total_seconds()) + " seconds")
	return error


def get_uris(balancer, bal_port):
	'''Function that connects to the \"dns\" server of uri
and find out what are the existing chats'''
	global delay,socket_to_pass

	# Create socket which will connect to load balancer
	load_socket= sk.socket(sk.AF_INET, sk.SOCK_STREAM)
	load_socket.connect((balancer, bal_port))

	# Recieve the ip and port of server to connect
	serv_info=load_socket.recv(2048).decode('utf-8')
	print(serv_info)
	serv_ip, serv_port=tuple(map(str, serv_info.split(', ')))
	serv_port=int(serv_port)

	# Create socket which will connect to the required server
	socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
	socket.connect((serv_ip, serv_port))
	socket_to_pass=socket

	#Calculate delay
	delay=chritian(socket)

	socket.send('GET uri'.encode())

	serialized = socket.recv(4096).decode('utf-8')

	return json.loads(serialized)

def listen_music():
	global socket_to_pass
	client_socket=socket_to_pass
	
	p = pyaudio.PyAudio()
	CHUNK = 1024
	stream = p.open(format=p.get_format_from_width(2),
					channels=2,
					rate=55410,
					output=True,
					frames_per_buffer=CHUNK)
	
	data = b""
	payload_size = struct.calcsize("Q")
	while True:
		try:
			while len(data) < payload_size:
				packet = client_socket.recv(4*1024) # 4K
				# print(packet)
				if not packet: break
				data+=packet
			packed_msg_size = data[:payload_size]
			data = data[payload_size:]
			msg_size = struct.unpack("Q",packed_msg_size)[0]
			while len(data) < msg_size:
				data += client_socket.recv(4*1024)
			frame_data = data[:msg_size]
			data  = data[msg_size:]
			frame = pickle.loads(frame_data)
			stream.write(frame)

		except:
			continue


	client_socket.close()
	print('Audio closed')
	os._exit(1)

def close_socket():
	a=1
	user_client=Pyro4.Proxy(user_uri)
	while(a):
		if user_client.check_alive()==0:
			a=0
			print("client socket closed")
			socket_to_pass.close()
			print("exit")
			os._exit(1)
		

def main(server='localhost', port=25498):
	#while to find a valid username
	global socket_to_pass, user_uri
	while True:
		username = input('Username: ')

		if ':' not in username:
			break
		else:
			print("Username cannot have ':' try again")


	uris = get_uris(server, port)

	#while to select a valid chat room
	while True:
		print('Available Music rooms:')
		for n, item in enumerate(uris):
			print(f"{n}: {item[0]}")

		selection = input("Pick a music room: ")

		try:
			uri = uris[int(selection)][1]
			socket_to_pass.send((uris[int(selection)][0]+", "+username).encode())
			break
		except (IndexError, ValueError):
			print(f"'{selection}' is not a valid music room, please, try again.")

	# server listens infinitely
	t=threading.Thread(target = listen_music)
	t.start()

	#The impersonation of the user connected to the chat is instantiated
	u = user.User(uri, username, delay)
	user_uri=u.my_uri
	t=threading.Thread(target = close_socket)
	t.start()


if __name__ == '__main__':
	main()