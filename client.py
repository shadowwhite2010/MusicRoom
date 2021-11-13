import user
import json
import socket as sk
import datetime
from dateutil import parser
from timeit import default_timer as timer

delay=0
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


def get_uris(server, port):
	'''Função que se conecta ao servidor \"dns\" de uri
	e descobre quais são os chats existentes'''
	global delay
	socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
	socket.connect((server, port))

	#Calculate delay
	delay=chritian(socket)

	socket.send('GET uri'.encode())

	serialized = socket.recv(4096).decode('utf-8')

	return json.loads(serialized)

def main(server='localhost', port=25500):
	#while para encontrar um nome de usuário válido
	while True:
		username = input('Username: ')

		if ':' not in username:
			break
		else:
			print("Nome de usuario não pode ter ':'. tente novamente")


	uris = get_uris(server, port)

	#while para selecionar uma sala de bate-papo válidada
	while True:
		print('Chats disponíveis:')
		for n, item in enumerate(uris):
			print(f"{n}: {item[0]}")

		selection = input("Pick a chat: ")

		try:
			uri = uris[int(selection)][1]
			break
		except (IndexError, ValueError):
			print(f"'{selection}' is not a valid chat, please, try again.")

	#A representação do usuário conectada ao bate-papo é instanciada
	u = user.User(uri, username, delay)


if __name__ == '__main__':
	main()