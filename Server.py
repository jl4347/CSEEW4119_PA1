import sys
import socket

BLOCK_TIME = 60
LAST_HOUR = 3600
TIME_OUT = 1800
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
											 'ip_address': '',
											 'online': False,
											 'logout_time': None,
											 'inactive_time': None,
											 'blocked' : None,
											 'login_attempts': 0 }
		#print self.users
	def start(self):
		ip_address = socket.gethostbyname(socket.gethostname())
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.bind((ip_address, self.port))
		server_socket.listen(MAX_USERS)
		print 'Chat room server is ready to process messages!'
		while True:
			try:
				connection_socket, addr = server_socket.accept()
				connection_socket.send('Message received')
				connection_socket.close()
			except KeyboardInterrupt:
				server_socket.close()
				print 'Chat room shut down....'
				sys.exit()
				return
			
		


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