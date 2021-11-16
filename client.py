from socket import AF_INET, socket, SOCK_STREAM, gethostname, SHUT_RDWR

from threading import Thread

from time import sleep

#from sys import exit

import platform, os, stat, sys, ctypes
import getpass

from PIL import ImageGrab, Image
import io
from ctypes import windll
from pynput.keyboard import Key, Controller as KController
from pynput.mouse import Button,  Controller as MController
if platform.system().lower()=='windows':
	
	shutdown = 'shutdown /f /s'

	file_path = 'C:/client/client.zip'

else:
	shutdown = '/sbin/shutdown -P now'

	file_path = '/root/client.py'

def checkUpdate():
	msg = client_socket.recv(BUFSIZ).decode("utf8")

	if clientVersion not in msg:
		if platform.system().lower()=='windows':
			client_socket.send('need update win'.encode("utf8"))
			file = open(file_path,'wb')
			filesize = client_socket.recv(BUFSIZ).decode("utf8")
			l = client_socket.recv(BUFSIZ)
			while(l):
				file.write(l)
				l = client_socket.recv(BUFSIZ)
			file.close()
			os.system("C:/client/update/update.exe")

			#subprocess.call("C:/client/update/update.exe", shell=False)

			sys.exit()
			
		else:
			client_socket.send('need update linux'.encode("utf8"))
			file = open(file_path,'wb')
			filesize = client_socket.recv(BUFSIZ).decode("utf8")
			l = client_socket.recv(BUFSIZ)
			while(l):
				file.write(l)
				l = client_socket.recv(BUFSIZ)
			file.close()
			os.chmod(file_path,stat.S_IRWXU)
			print("updated")
			python = sys.executable
			os.execl(python, python, * sys.argv)

def showMsg(m):
	if (ctypes.windll.user32.MessageBoxW(0, m, "Komunikat", 4096)):
		client_socket.send("message read".encode("utf8"))

def receive():

	global client_socket

	global isConnected

	while True:

		try:
			if isConnected == False:
				#print("Attemping to reconnect...")

				client_socket = socket(AF_INET, SOCK_STREAM)

				client_socket.connect_ex(ADDR)

				client_socket.send(bytes(gethostname().encode("utf8")))

				checkUpdate()

				isConnected = True
				print("Connected")
			else:
				msg = client_socket.recv(BUFSIZ).decode("utf8")
				
				if msg == "turn off":
					 #client_socket.send(bytes('turning off'.encode("utf8")))

					#client_socket.close()

					if platform.system().lower()=='windows':
						#os.system("msg %username% Niski poziom naladowania UPS. Komputer zostanie za chwile wylaczony")
						
						sleep(10)

					if os.system(shutdown) == 0:
						client_socket.send(bytes('turning off'.encode("utf8")))##

						client_socket.close()##
					else:
						client_socket.send(bytes("Shutdown failed!".encode("utf8")))##

						client_socket.close()##
					#print("Wylaczony :)")

					exit()

				elif msg == "exit":
					client_socket.shutdown(SHUT_RDWR)
					client_socket.close()
					break

				elif msg == "check":
					client_socket.send("online".encode("utf8"))

				elif ('msg /' in msg) & (platform.system().lower()=='windows'):
					#os.system("msg %username% "+ msg[5:])
					Thread(target=showMsg, args=(msg[5:],)).start()

				elif ('wanttosendfile' in msg) & (platform.system().lower()=='windows'):
					filename = msg[15:]
					username = getpass.getuser()
					os.makedirs("C:/Users/"+username+"/Desktop/Odebrane", exist_ok=True)
					file = open("C:/Users/"+username+"/Desktop/Odebrane/"+filename,'wb')
					l = client_socket.recv(BUFSIZ)
					while(l):
						file.write(l)
						l = client_socket.recv(BUFSIZ)
					file.close()
					Thread(target=showMsg, args=("Odebrano plik: "+filename+"\n Sprawdź folder Odebrane na pulpicie.",)).start()

				elif ('wanttorcclient' in msg) & (platform.system().lower()=='windows'):
					client_socket.send("startrc".encode("utf8"))
					keyboard = KController()
					mouse = MController()
					while(1):
						try:
							img = ImageGrab.grab()
							img.thumbnail([960,540])
							imgByteArr = io.BytesIO()
							img.save(imgByteArr, format='jpeg')
							imgByteArr = imgByteArr.getvalue()
							client_socket.send(imgByteArr)
							#print("Przed odebraniem mouse")
							mouse_xy = client_socket.recv(BUFSIZ).decode("utf8")
							#print(mouse_xy)
							if (mouse_xy.startswith("endrc")):
								break
							mouse_xy = mouse_xy.split('#$')
							mouse_x = int(mouse_xy[0])
							mouse_y = int(mouse_xy[1])
							mouse_click = mouse_xy[2]
							key_click = mouse_xy[3]
							key_pressed = mouse_xy[4]
							#print(mouse_x)
							#print(mouse_y)
							#ctypes.windll.user32.SetCursorPos(mouse_x,mouse_y)
							mouse.position = (mouse_x, mouse_y)
							if mouse_click == '1':
								#ctypes.windll.user32.mouse_event(2, 0, 0, 0,0) # left down
								#ctypes.windll.user32.mouse_event(4, 0, 0, 0,0) # left up
								mouse.press(Button.left)
							if mouse_click == '0':
								mouse.release(Button.left)
						
							if key_click == '1':
								keyboard.press(key_pressed)
								print("pressed: "+key_pressed)
								keyboard.release(key_pressed)
							#sleep(0.1)

						except:
							print("Bad char")

				else:
					print(msg)

				if not msg:
					print('czas na break')
					isConnected = False
					#break

		except Exception as e:
			isConnected = False
			
			print(e)
			print('Error line: %s' %sys.exc_info()[-1].tb_lineno)
			sleep(300)
			#continue


def on_closing(event=None):

	my_msg.set("turning off")


clientVersion = '1.1'

HOST = '192.168.0.2'

PORT = 5000

BUFSIZ = 1024

ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)

while True:

	if client_socket.connect_ex(ADDR) == 0:
		break
	sleep(300)
	#print("Cannot connect")

#print("Connected")

isConnected = True
errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2) #Skalowanie ekranu nie zmienia współrzędnych myszki
client_socket.send(bytes(gethostname().encode("utf8")))

checkUpdate()

receive_thread = Thread(target=receive)

receive_thread.start()
