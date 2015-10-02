import sys
import socket
import json
import thread
import datetime
import random
import errno
import time

BLOCK_TIME = 60
TIME_OUT = 600
CHECK_INTERVAL = 5
MAX_USERS = 10
BUFFSIZE = 4096

class Server:
	"""
	Simple chat room Server
	"""
	def __init__(self, port):
		# Listening port
		self.port = port
		# User info
		self.online_users = []
		self.connections = []
		# Create the listening socket to wait for connection from clients
		ip_address = socket.gethostbyname(socket.gethostname())
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((ip_address, self.port))
		self.server.listen(MAX_USERS)
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
											 'online': False,
											 'last_command': None,
											 'socket': None }

	def start(self):
		print 'Chat room server is ready to process messages!'
		thread.start_new_thread(self.status_check, ())
		while True:
			try:
				print 'waiting for new connections'
				conn, addr = self.server.accept()
				print 'connection accepted'
				thread.start_new_thread(self.client_listen_thread, (conn, addr))
			except KeyboardInterrupt, SystemExit:
				print 'Server shutting down....'
				for conn in self.connections:
					conn.close()

				self.server.close()
				sys.exit(0)

	def status_check(self):
		'''
		Perform regular status check for user inactivity every CHECK_INTERVAL seconds
		Logout the user if he/she has stayed idle for more than 30min
		'''
		response = { 'status': 'ERROR',
					 'command': 'LOGOUT',
					 'message': 'Automatic logout due to inactivity.'}
		while True:
			for username in self.users:
				user = self.users[username]
				if user['online']:
					idle_time = (datetime.datetime.now() - user['last_command']).total_seconds()
					if idle_time > TIME_OUT:
						user['socket'].send(json.dumps(response))
			time.sleep(CHECK_INTERVAL)

	def client_listen_thread(self, client_socket, address):
		print 'Connection from ', address
		username = ''
		while True:
			try:
				request = json.loads(client_socket.recv(BUFFSIZE).strip())
			except ValueError:
				print 'Client crashes and automatically logout'
				self.logout(username, client_socket)
				break

			command = request['command']
			username = request['username']
			print request
			if command == 'AUTH':
				self.authenticate(client_socket, request, address)
			elif command == 'LOGOUT':
				self.logout(request['username'], client_socket)
				break
			elif command == 'WHOELSE':
				self.online(request)
			elif command == 'WHOLAST':
				self.who_last(request)
			elif command[:7] == 'MESSAGE':
				self.process_messages(request)

	def authenticate(self, client_socket, data, address):
		'''
		Authenticate user
		After three unsuccessful login attempts from the same IP address, block the user from
		that IP address for BLOCK_TIME seconds.

		If the user/password combination is valid, assign the user a random port and sends system
		message to the user. Server adds the user to the self.online_users to keep track of online
		users. The user should listen on the server assigned port for any incoming
		message.

		If user/password combination is valid but the user is already online, reject the connection
		'''

		username = data['username']
		ip = address[0]
		response = {}
		user = {}
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
						self.online_users.append(username)
						print 'Users online:', str(self.online_users)
						user['online'] = True
						user['last_command'] = datetime.datetime.now()
						# reset the login attempts
						user_ip['login_attempts'] = 0
						user_ip['last_attempt'] = datetime.datetime.now()
						response = { 'status': 'SUCCESS',
								 	 'message': 'Welcome to the simple chat server!' }
						self.connections.append(client_socket)
						user['socket'] = client_socket

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

	def logout(self, username, client_socket):
		'''
		Remove the user from the self.online_users list, and change the user's status
		to offline
		'''
		if username in self.users:
			self.online_users.remove(username)
			user = self.users[username]
			self.connections.remove(user['socket'])
			user['online'] = False
			user['last_command'] = datetime.datetime.now()
			user['socket'] = None
		client_socket.close()
		print 'User [', username, '] logout successfully' 

	def online(self, data):
		'''
		'whoelse' command:

 		Retrieve the list of online users and remove the client who requested.
		Send the list back to the client via client's listening socket
		'''
		online_list = list(self.online_users)
		online_list.remove(data['username'])

		user = self.users[data['username']]
		response = { 'status': 'SUCCESS',
					 'command': 'WHOELSE',
					 'message': online_list }
		self.send_response(user, response)

	def who_last(self, data):
		user_list = []
		for user in self.users:
			user_dict = self.users[user]
			if user_dict['online']:
				user_list.append(user)
			else:
				if user_dict['last_command'] != None:
					since_last = (datetime.datetime.now() - user_dict['last_command']).total_seconds()
					if since_last <= data['time_frame']*60:
						user_list.append(user)

		user = self.users[data['username']]
		user_list.remove(data['username'])
		response = { 'status': 'SUCCESS',
					 'command': 'WHOLAST',
					 'message': user_list }
		self.send_response(user, response)

	def process_messages(self, request):
		message_to = []
		not_found = []
		if not request['to']:
			# broadcast to everyone online
			message_to = list(self.online_users)
		else:
			for reciever in request['to']:
				if reciever not in self.users:
					not_found.append(reciever)
				elif self.users[reciever]['online'] == False:
					not_found.append(reciever)
				else:
					message_to.append(reciever)

		if request['command'][8:] == 'BROAD':
			print 'reciever: ', message_to
			print 'online users: ', self.online_users
			# client could broadcast to oneself when sending message to user group
			if request['username'] in message_to and request['username'] not in request['to']:
				message_to.remove(request['username'])
		# Send message to each available user
		for reciever in message_to:
			if not self.send_message(reciever, request):
				not_found.append(reciever)

		# Send feedback to the sender
		if not_found:
			response = { 'status': 'WARNING',
						 'command': 'MESSAGE_FEEDBACK',
						 'message': 'Users ' + str(not_found) + ' not found' }
			self.send_response(self.users[request['username']], response)

	def send_message(self, reciever, request):
		message = { 'status': 'SUCCESS',
					'command': 'MESSAGE',
					'from': request['username'],
					'message': request['message'] }
		if not self.send_response(self.users[reciever], message):
			return False
		else:
			return True

	def send_response(self, user, response):
		try:
			user['socket'].send(json.dumps(response))
			return True
		except:
			print 'Unable to deliver message to ', user['ip'], ':', user['port']
			if user['online']:
				self.logout(user['username'], user['socket'], True)
				print 'Log out User:', user['username']
			return False
		# update user info
		user['last_command'] = datetime.datetime.now()
 
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