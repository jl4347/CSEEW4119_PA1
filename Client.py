import socket
import sys
import json

TIME_OUT = 1800

class Client(object):
	def __init__(self, host, port):
		self.server_address = host
		self.server_port = port
		self.username = ''
		self.started = False
		self.authorized = False

	def start(self):
		pass

	def authenticate(self, username, password):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.server_address, self.server_port))
		userinfo = { 'command': 'AUTH',
					 'username': username,
					 'password': password }
		s.send(json.dumps(userinfo))
		response = json.loads(s.recv(1024))
		print response['status'], ': User[', username, '] ', response['message']

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
				break
		

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