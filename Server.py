import sys
import socket
import json
import thread
import datetime
import random

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

	def load_userinfo(self):
		with open('user_pass.txt') as file:
			for line in file:
				user_info = line.split()
				self.users[user_info[0]] = { 'password': user_info[1],
											 # ip is a dict since we are blocking on the 
											 # (ip, username) pair
											 'ip_address': {},
											 'ip': '',
											 'port': 0,
											 'online': False,
											 'logout_time': None,
											 'last_command': None }

	def start(self):
		ip_address = socket.gethostbyname(socket.gethostname())
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.bind((ip_address, self.port))
		server_socket.listen(MAX_USERS)
		print 'Chat room server is ready to process messages!'
		while True:
			try:
				conn, addr = server_socket.accept()
				thread.start_new_thread(self.client_thread, (conn, addr))
			except KeyboardInterrupt, SystemExit:
				server_socket.close()
				print 'Chat room shut down....'

	def client_thread(self, socket, address):
		print 'Connection from ', address
		data = json.loads(socket.recv(4096).strip())
		command = data['command']

		if command == 'AUTH':
			self.authenticate(socket, data, address)

	def authenticate(self, client_socket, data, address):
		'''
		Authenticate user
		After three unsuccessful login attempts from the same IP address, block the user from
		that IP address for BLOCK_TIME seconds.

		If the user/password combination is valid, assign the user a random port and sends system
		message to the user. The user should listen on the server assigned port for any incoming
		message.

		If user/password combination is valid but the user is already online, reject the connection
		'''
		username = data['username']
		ip = address[0]
		response = {}
		if username in self.users:
			user = self.users[username]
			# create the new user-ip pair if not exist
			if ip not in user['ip_address']:
				user['ip_address'][ip] = { 'login_attempts': 0,
										   'last_attempt' : datetime.datetime.now() }

			user_ip = user['ip_address'][ip]
			if user_ip['login_attempts'] == 3:
				since_last = (datetime.datetime.now() - user_ip['last_attempt']).total_seconds()
				if since_last >= BLOCK_TIME:
					user_ip['login_attempts'] = 0
					user_ip['last_attempt'] = datetime.datetime.now()
				else:
					response = { 'status': 'ERROR',
								 'message': 'too many login attempts,' + \
								 ' please wait ' + str(BLOCK_TIME - since_last) + 's to have another try.' }

			if user_ip['login_attempts'] < 3: 
				if data['password'] == user['password']:
					# If user is already online
					if user['online']:
						response = { 'status': 'ERROR',
								 	 'message': 'user is already online.' }
					else:
						user['online'] = True
						user['ip'] = ip
						user['last_command'] = datetime.datetime.now()
						# reset the login attempts
						user_ip['login_attempts'] = 0
						user_ip['last_attempt'] = datetime.datetime.now()
						user['port'] = random.randint(10000, 50000)
						response = { 'status': 'SUCCESS',
									 'port': user['port'],
								 	 'message': 'Welcome to the simple chat server!' }

				else:
					user_ip['login_attempts'] += 1
					user_ip['last_attempt'] = datetime.datetime.now()
					response = { 'status': 'ERROR',
							 	 'message': 'wrong combination of username and password' }
		else:
			response = { 'status': 'ERROR',
						 'message': 'username does not exist' }
			
		print user
		client_socket.send(json.dumps(response))
		# Close the client_socket at the end
		client_socket.close()
 
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