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
		self.listen_socket = None
		self.authorized = False
		self.started = False

	def start(self):
		'''
		Client must be authorized first.
		Start the listen thread to catch any messages coming from server
		'''
		if self.authorized:
			thread.start_new_thread(self.listen, ())
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
		response = json.loads(s.recv(4096).strip())
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
		self.listen_socket = listen_socket
		while True:
			conn, addr = listen_socket.accept()
			thread.start_new_thread(self.listen_thread, (conn, addr))

	def listen_thread(self, socket, addr):
		'''
		Listen thread to process the command sent from server
		'''
		response = json.loads(socket.recv(4096).strip())
		if response['status'] == 'SUCCESS':
			if response['command'] == 'WHOELSE':
				print 'who else: ', response['message']
			if response['command'] == 'WHOLAST':
				print 'who last: ', response['message']
			if response['command'] == 'MESSAGE':
				print response['from'], ': ', response['message']
		elif response['status'] == 'WARNING':
			if response['command'] == 'MESSAGE_FEEDBACK':
				print response['status'], ': ', response['message']

		socket.close()

	def logout(self):
		request = { 'command': 'LOGOUT',
					 'username': self.username }
		self.send_request(request)
		# close the listening socket
		self.listen_socket.close()

	def online_users(self):
		request = { 'command': 'WHOELSE',
					 'username': self.username }
		self.send_request(request)

	def who_last(self, time_frame):
		request = { 'command': 'WHOLAST',
					'username': self.username,
					'time_frame': time_frame }
		self.send_request(request)

	def send_message(self, command, to, message):
		request = { 'command': '',
					'username': self.username,
					'to': to,
					'message': message }
		# Distinguish between private and broadcast message
		if command == 'message':
			request['command'] = 'MESSAGE_PRIVATE'
		else:
			request['command'] = 'MESSAGE_BROAD'
		self.send_request(request)

	def send_request(self, request):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.server_address, self.server_port))
		s.send(json.dumps(request))
		s.close()

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
				self.client.logout()
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
		print 'Command:'
		while True:
			commands = raw_input('')
			if len(commands) == 0:
				continue
			command = commands.split(' ', 1)
			print command
			if command[0] == 'logout':
				self.client.logout()
				print 'User [', self.client.username, '] has logged out.'
				sys.exit()

			elif command[0] == 'whoelse':
				self.client.online_users()

			elif command[0] == 'wholast':
				if len(command) < 2:
					print 'Please enter the time frame you would like to trace back'
					continue
				# TODO catch the value error
				time_frame = int(command[1])
				if time_frame > 0 and time_frame <= 60:
					self.client.who_last(int(command[1]))
				else:
					print 'Warning: you can only trace back an hour'

			elif command[0] == 'message':
				if len(command) < 2:
					print 'Wrong command format', \
						  'message <user> <message message>'
					continue
				to = []
				user_message = command[1].split(' ', 1)
				to.append(user_message[0])
				if len(user_message) < 2:
					print 'Wrong command format:', \
						  'message <user> <message message>'
					continue
				self.client.send_message(command[0], to, user_message[1])

			elif command[0] == 'broadcast':
				pass

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