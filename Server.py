import sys
import socket
import json
import thread
import datetime
import random

BLOCK_TIME = 60
DEAD_ALIVE = 60
MAX_USERS = 10

class Server:
	"""
	Simple chat room Server
	"""
	def __init__(self, port):
		# Listening port
		self.port = port
		# User info
		self.online_users = []
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
											 'last_command': None,
											 'last_seen': None }

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
				sys.exit()

	def client_thread(self, socket, address):
		print 'Connection from ', address
		request = json.loads(socket.recv(4096).strip())
		command = request['command']
		print command

		if command == 'AUTH':
			self.authenticate(socket, request, address)
		elif command == 'LOGOUT':
			self.logout(request)
		elif command == 'WHOELSE':
			self.online(request)
		elif command == 'WHOLAST':
			self.who_last(request)
		elif command[:7] == 'MESSAGE':
			self.process_messages(request)
			
		socket.close()

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

	def logout(self, data):
		'''
		Remove the user from the self.online_users list, and change the user's status
		to offline
		'''
		self.online_users.remove(data['username'])
		user = self.users[data['username']]
		user['ip'] = ''
		user['online'] = False
		user['port'] = 0
		user['last_command'] = datetime.datetime.now()

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

		if not request['to']:
			# broadcast to everyone online
			message_to = list(self.online_users)
		else:
			not_exist = []
			not_online = []
			for reciever in request['to']:
				if reciever not in self.users:
					not_exist.append(reciever)
				elif self.users[reciever]['online'] == False:
					not_online.append(reciever)
				else:
					message_to.append(reciever)
			# Send feedback to the sender
			if not_online or not_exist:
				response = { 'status': 'WARNING',
							 'command': 'MESSAGE_FEEDBACK',
							 'message': 'Users ' + str(not_exist) + ' do not exist\n' +
							 			'\tUsers ' + str(not_online) + ' not online.'}
				self.send_response(self.users[request['username']], response)

		if request['command'][8:] == 'BROAD':
			print 'reciever: ', message_to
			print 'online users: ', self.online_users
			if request['username'] in message_to:
				message_to.remove(request['username'])
		# Send message to each available user
		for reciever in message_to:
			self.send_message(reciever, request)

	def send_message(self, reciever, request):
		message = { 'status': 'SUCCESS',
					'command': 'MESSAGE',
					'from': request['username'],
					'message': request['message'] }
		self.send_response(self.users[reciever], message)


	def send_response(self, user, response):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((user['ip'], user['port']))
		s.send(json.dumps(response))
		s.close()
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