import sys
import socket
import json
import select

BLOCK_TIME = 60
LAST_HOUR = 3600
MAX_USERS = 10

class Server:
	"""
	Simple chat room Server
	"""
	def __init__(self, port):
		# Listening port
		self.port = port
		# User info
		self.users = {}
		self.load_userinfo()
		# list of connected sockets
		self.connection = []

	def load_userinfo(self):
		with open('user_pass.txt') as file:
			for line in file:
				user_info = line.split()
				self.users[user_info[0]] = { 'password': user_info[1],
											 'ip_address': '',
											 'online': False,
											 'logout_time': None,
											 'inactive_time': None,
											 'blocked' : None,
											 'login_attempts': 0 }

	def start(self):
		ip_address = socket.gethostbyname(socket.gethostname())
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.bind((ip_address, self.port))
		server_socket.listen(MAX_USERS)
		self.connection.append(server_socket)
		print 'Chat room server is ready to process messages!'
		while True:
			try:
				read_socket, output_socket, error_socket = select.select(self.connection, [], [])
				for input_socket in read_socket:
					if input_socket == server_socket:
						self.authenticate(input_socket)
					else:
						pass
				# connection_socket, addr = server_socket.accept()
				
			except KeyboardInterrupt, SystemExit:
				server_socket.close()
				print 'Chat room shut down....'

	def authenticate(self, server_socket):
		connection, address = server_socket.accept()
		data = json.loads(connection.recv(1024).strip())
		self.connection.append(connection)

		if data['username'] in self.users:
			if data['password'] == self.users[data['username']]['password']:
				response = { 'status': 'SUCCESS',
						 	 'message': 'login successful' }
				connection.send(json.dumps(response))
				# TODO jump out the function to wait for further commands
			elif self.users[data['username']]['login_attempts'] < 2:
				self.users[data['username']]['login_attempts'] += 1
				response = { 'status': 'ERROR',
						 	 'message': 'wrong combination of username and password' }
				connection.send(json.dumps(response))
				print self.users[data['username']]['login_attempts']
			else:
				# TODO blocking the user
				pass
		else:
			response = { 'status': 'ERROR',
						 'message': 'username does not exist' }
			connection.send(json.dumps(response))
			self.connection.remove(connection)
			connection.close()
 
def main():
	if len(sys.argv) != 2:
		print 'User instruction:\n', \
		 	  'python Server.py <port>'
		sys.exit();
	port = int(sys.argv[1])
	server = Server(port)
	server.start()
	

if __name__ == "__main__":
	main()