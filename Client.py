import socket
import sys
import json
import thread

TIME_OUT = 1800
MAX_CONN = 100

class Client(object):
	def __init__(self, host, port):
		self.server_address = host
		self.server_port = port
		self.username = ''
		self.port = 0
		self.authorized = False
		self.started = False

	def start(self):
		'''
		Client must be authorized first.
		Start the listen thread to catch any messages coming from server
		'''
		if self.authorized:
			self.listen()
			self.started = True
		else:
			raise Exception('User not authorized!')

	def authenticate(self, username, password):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.server_address, self.server_port))
		userinfo = { 'command': 'AUTH',
					 'username': username,
					 'password': password }
		s.send(json.dumps(userinfo))
		response = json.loads(s.recv(1024).strip())
		s.close()
		print response['status'], ': User[', username, '] ', response['message']
		print response
		if response['status'] == 'SUCCESS':
			self.username = username
			self.authorized = True
			self.port = response['port']
			return True
		else:
			return False

	def listen(self):
		'''
		Create a socket binding the port assigned by the server
		Whenever receives a command from server start a new thread to process the command
		'''
		ip = socket.gethostbyname(socket.gethostname())
		listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		listen_socket.bind((ip, self.port))
		listen_socket.listen(MAX_CONN)
		while True:
			conn, addr = listen_socket.accept()
			thread.start_new_thread(self.listen_thread, (conn, addr))

	def listen_thread(self, socket, addr):
		'''
		Listen thread to process the command sent from server
		'''
		command = json.loads(socket.recv(4096).strip())

class  ClientCLI(object):
	def __init__(self, host, port):
		self.client = Client(host, port)

	def start(self):
		try:
			self.authentication()
			self.client.start()
			self.command()
		except KeyboardInterrupt, SystemExit:
			if self.client.started:
				pass
			print 'User [', self.client.username, '] has logged out.'

	def authentication(self):
		while True:
			username = raw_input('username: ')
			password = raw_input('password: ')
			if username == '' or password == '':
				print 'Please don\' leave username or password blank.'
				continue
			elif self.client.authenticate(username, password):
				return True

	def command(self):
		'''
		Take commands from client's command line interface
		'''
		while True:
			commands = raw_input('')
			print commands
		

def main():
	if len(sys.argv) != 3:
		print 'User Instruction:', \
			  'python Client.py <host> <port>'
		sys.exit()
	
	host = sys.argv[1]
	port = int(sys.argv[2])
	client = ClientCLI(host, port)
	client.start()

if __name__ == '__main__':
	main()