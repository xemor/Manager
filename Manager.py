


from socket import AF_INET, socket, SOCK_STREAM, SHUT_WR, SHUT_RDWR, SHUT_RD
import telnetlib
import threading
from os import system, stat
from threading import Thread
from sys import exit, exc_info
from datetime import datetime
from time import sleep
from json import dumps
import configparser
def logging(msg):
	date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	with open(logFilePath, 'a+') as file:
		file.write('%s - %s\n' % (date, msg))

def errorLogging(msg, err):
	date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	error = str(err)

	with open(logFilePath, 'a+') as file:
		file.write('--------------Error--------------\n')

		file.write('%s - %s\n' % (date, msg))

		file.write(error)

		file.write('\n-------------------------------\n')


def getBatteryCap():
	tn = telnetlib.Telnet(upsHOST)


	tn.write((user + "\r\n").encode('ascii'))

	tn.write((password + "\r\n").encode('ascii'))

	tn.write(("detstatus -soc\r\n").encode('ascii'))

	out = tn.read_until(("Battery State Of Charge: ").encode('ascii'),5)

	out = tn.read_until((" ").encode('ascii'),5)

	tn.write(("exit\r\n").encode('ascii'))

	batteryCap = float(out.decode('ascii'))

	return batteryCap


def checkBatteryCap():
	global batteryErrorCount

	try:
		batteryCap = getBatteryCap()

		if batteryCap <= lowBatteryCap:
			print("Battery capacity is lower than %.0f percent" % lowBatteryCap)

			logging("Battery capacity is lower than %.0f percent" % lowBatteryCap)

			broadcast('turn off')

			sleep(10)

			system('shutdown /f /s')

			logging("Main server is shutting down")

			print("Main server is shutting down")
		else:
			threading.Timer(batteryCapCheckInterval,checkBatteryCap).start()
			
	except Exception as e:
		batteryErrorCount += 1

		if batteryErrorCount == 2:
			print("Battery Exception:")

			print(e)
	
			print('Error line: %s' % exc_info()[-1].tb_lineno)
		
			errorLogging("Battery Exception: Error line: %s" % exc_info()[-1].tb_lineno, e)

			batteryErrorCount = 0

		threading.Timer(batteryCapCheckInterval,checkBatteryCap).start()
		
def accept_incoming_connections():
	
	while True:

		client, client_address = SERVER.accept()

		addresses[client] = client_address

		name = client.recv(BUFSIZ).decode("utf8")

		client.send(bytes(clientVersion, "utf8"))
		
		for sock in list(clients):
			if clients[sock] == name:
				print('Deleting %s' % clients[sock])
				try:
					sock.send(bytes('exit', "utf8"))
				except:
					pass
				del clients[sock]
				sock.close()

		clients[client] = name
		connected[name] = "[ ]"
		print("%s:%s(%s) has connected." % (client_address[0],client_address[1], name))

		logging("%s:%s(%s) has connected." % (client_address[0],client_address[1], name))

		Thread(target=handle_client, args=(client,)).start()





def handle_client(client):
	shutdown_all_confirm = 0
	global rc_client
	global rcc

	while True:
		try:
			if rcc==0:
				msg = client.recv(BUFSIZ).decode("utf8")
			
				if not msg:
					logging(clients[client])
					break

				print("Recived: '%s' from %s " % (msg, clients[client]))

				logging("Recived: '%s' from %s " % (msg, clients[client]))

				if 'need update linux' in msg:
					file = open('E:\server\client.py', 'rb')
					filesize = stat('E:\server\client.py').st_size
					client.send(str(filesize).encode("utf8"))
					l = file.read(BUFSIZ)
					while (l):
						print('Sending...')
						client.send(l)
						l = file.read(BUFSIZ)
					client.shutdown(SHUT_WR)
					print("sent!")
					break

				elif 'need update win' in msg:
					file = open('E:\server\client.zip', 'rb')
					filesize = stat('E:\server\client.zip').st_size
					client.send(str(filesize).encode("utf8"))
					l = file.read(BUFSIZ)
					while (l):
						client.send(l)
						l = file.read(BUFSIZ)
					client.shutdown(SHUT_WR)
					print("sent!")
					break

				if msg == "turning off":
					ip = client.getpeername()[0]

					if ip in serverList:
						downServers.append(client.getpeername()[0])

						print("Zamkniete serwery: " + str(downServers))

						logging("Zamkniete serwery: " + str(downServers))

					client.close()
				
					print("%s has disconnected" % clients[client])

					logging("%s has disconnected" % clients[client])
				
					print("Delete: " + clients[client])

					logging("Delete: " + clients[client])

					del clients[client]
					break
				elif msg == "help":
					client.send("1. 'check connection' - Display a list of connected devices(wait 10s for response)\n\
	2. 'shutdown -all' - Shutdown all connected devices including server\n\
	3. 'shutdown /name' - Shutdown one device specified by name\n\
	4. 'cap' - Prints battery capacity\n\
	5. 'msg -all /text' - Show MessageBox on all devices\n\
	6. 'msg /name //text' - Show MessageBox on a specified device".encode("utf8"))

				elif msg == "check connection":
					for x in connected:
						connected[x] = "[ ]"

					connected[clients[client]] = "[x]"

					for sock in list(clients):
						if sock is not client:
							try:
								sock.send("check".encode("utf8"))

								print("Sending message 'check' to %s" % (clients[sock]))

								logging("Sending message 'check' to %s" % (clients[sock]))

							except Exception as e:
								print("Exception: Cannot send message to: %s" % clients[sock])

								print(e)
								print('Error line: %s' % exc_info()[-1].tb_lineno)
								errorLogging("Exception: Cannot send message to: %s Error line: %s" % (clients[sock], exc_info()[-1].tb_lineno), e)
					sleep(5)
					connectedSer = dumps(connected)	#dict as string		
					client.send(connectedSer.encode("utf8"))
				elif msg == "online":
					connected[clients[client]] = "[x]"
			

				elif msg == "shutdown -all":
					client.send("Are you sure? (y/n):".encode("utf8"))
					shutdown_all_confirm = 1

				elif msg == "y" and shutdown_all_confirm == 1:
					shutdown_all_confirm = 0

					broadcast('turn off')

					sleep(10)

					system('shutdown /f /s')

				elif 'shutdown /' in msg:
					found_client = 0

					client_name = msg[10:]

					for sock in list(clients):
						if client_name == clients[sock]:
							sock.send("turn off".encode("utf8"))

							found_client = 1

					if found_client == 0:
						client.send(("%s not found." % client_name).encode("utf8"))

				elif msg == "cap":
					bc = str(getBatteryCap())
					client.send(("Battery Cap: %s" % bc).encode("utf8"))

				elif 'msg /' in msg:
					found_client = 0

					a = msg.find('/')

					b = msg.find('//')

					if a is not -1 & b is not -1 & a < b:

						client_name = msg[a + 1:b - 1]

						for sock in list(clients):
							if client_name == clients[sock]:
								sock.send(("msg /" + msg[b + 2:]).encode("utf8"))

								found_client = 1

						if found_client == 0:
							client.send(("%s not found." % client_name).encode("utf8"))

				elif 'msg -all //' in msg:
					a = msg.find('//')

					broadcast("msg /" + msg[a + 2:])

				elif msg == "message read":

					for sock in list(clients):
						if (clients[sock] == "IT"):

							sock.send((clients[client] + " - message read").encode("utf8"))

				elif 'wanttosendfile' in msg:
					name = msg[15:]
					filename = client.recv(BUFSIZ).decode("utf8")
					file = open("E:/server/pliki/%s" %filename,'wb')
					filesize = int(client.recv(BUFSIZ).decode("utf8"))
					print(filesize)
					l = client.recv(BUFSIZ)
					while(l):
						file.write(l)
						l = client.recv(BUFSIZ)
					file.close()
					logging("Odebrano plik")
					for sock in list(clients):
						if name == clients[sock]:
							logging("Znaleziono klienta")
							sock.send(("wanttosendfile "+filename).encode("utf8"))
							file = open("E:/server/pliki/%s" %filename, 'rb')
							l = file.read(BUFSIZ)
							while (l):
								sock.send(l)
								l = file.read(BUFSIZ)
							file.close()
							sock.shutdown(SHUT_WR)
							logging("Plik wyslany")

				elif 'wanttorcclient' in msg:
					rcc=1
					rc_client = client
					name = msg[15:]
					for sock in list(clients):
						if name == clients[sock]:
							sock.send(("wanttorcclient").encode("utf8"))
						

				elif msg == 'startrc':
					rc_client.send('startrc'.encode('utf8'))
					while(1):
						#logging("przed odebraniem ss")
						ss = client.recv(250000)
						#logging("po odebraniu ss")
						rc_client.send(ss)
						#logging("po wyslaniu ss")
						mouse_xy = rc_client.recv(BUFSIZ)
						#logging("po odebraniu mouse_xy")
						client.send(mouse_xy)
						if (mouse_xy.decode("utf8").startswith("endrc")):
							rcc=0
							#logging("Ustawiam rss spowrotem na 0")
							break
						#logging("po wysłaniu ss")
						#sleep(0.1)

				else:
					logging("Cos takiego:"+msg)
					client.send("Command not found or canceled.".encode("utf8"))

					shutdown_all_confirm = 0
			else:
				sleep(2)

		except Exception as e:
			#client.close()
			addresses[client]
			if client in clients:
				print("Exception: %s has disconnected" % clients[client])
				errorLogging("Exception: %s has disconnected. Error line: %s" % (clients[client], exc_info()[-1].tb_lineno),e)
				del clients[client]
			else:
				print('Exception: %s - disconnected' % addresses[client][0])
				errorLogging('Exception: %s - disconnected Error line: %s' % (addresses[client][0], exc_info()[-1].tb_lineno),e)
			print(e)
			if '[WinError 10054]' in str(e):
				print("To ten blad")
			print('Error line: %s' % exc_info()[-1].tb_lineno)

			break 
def broadcast(msg):

	for sock in list(clients):
		try:
			sock.send(bytes(msg, "utf8"))

			print("Sending message '%s' to %s" % (msg, clients[sock]))

			logging("Sending message '%s' to %s" % (msg, clients[sock]))

		except Exception as e:
			print("Exception: Cannot send message to: %s" % clients[sock])

			print(e)
			print('Error line: %s' % exc_info()[-1].tb_lineno)
			errorLogging("Exception: Cannot send message to: %s Error line: %s" % (clients[sock], exc_info()[-1].tb_lineno), e)
      
#------------------------------
Config = configparser.ConfigParser()
Config.read("config.ini")
clientVersion = Config.get('config', 'clientVersion')
HOST = Config.get('config', 'host')
PORT = Config.getint('config', 'port')
BUFSIZ = Config.getint('config', 'bufsiz')
lowBatteryCap = Config.getfloat('config', 'lowBatteryCap')
batteryCapCheckInterval = Config.getfloat('config', 'batteryCapCheckInterval')
logFilePath = Config.get('config', 'logFilePath')
clients = {}
connected = {}
addresses = {}
downServers = []
#------------------------------
upsHOST = "192.168.0.2"

user = "user"

password = "password"
#----------------------------------------
rcc=0

ADDR = (HOST, PORT)
rc_client = socket()
SERVER = socket(AF_INET, SOCK_STREAM)

SERVER.bind(ADDR)

#lowBatteryCap = 18.0

#batteryCapCheckInterval = 300.0

batteryErrorCount = 0
serverList = ["192.168.0.3", "192.168.0.4"]

if __name__ == "__main__":

	checkBatteryCap()

	SERVER.listen(10)

	print("Waiting for connection...")

	logging("Waiting for connection...")

	ACCEPT_THREAD = Thread(target=accept_incoming_connections)

	ACCEPT_THREAD.start()

	ACCEPT_THREAD.join()

	SERVER.close()
