from socket import AF_INET, socket, SOCK_STREAM, gethostname, SHUT_RDWR, SHUT_WR

from threading import Thread

from time import sleep
from json import loads
#from sys import exit

import platform, os, stat, sys
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from os import stat
from PIL import ImageGrab, ImageTk, Image
import io
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
if platform.system().lower()=='windows': 
	
	shutdown = 'shutdown /f /s'

	file_path = 'C:/client/client.zip'

else:
	shutdown = '/sbin/shutdown -P now'

	file_path = '/root/mailsd/reclient.py'

#--------------------------------------------------------------------
def refresh():
	clients_listbox.delete(0,END)
	clients_listbox.insert(0,"Trwa odświeżanie...")
	client_socket.send("check connection".encode("utf8"))
	
def get_selected_clients():
	index = clients_listbox.curselection()
	clients_list = []
	for x in index:
		clients_list.append(clients_listbox.get(x))
	return clients_list

def shutdown_clients():
	clients_list = get_selected_clients()
	if clients_list == []:
		info_text.insert(0.0, "Wybierz odbiorców!\n")
	else:
		response = messagebox.askyesno("Uwaga!","Czy na pewno chcesz wyłączyć wybrane urządzenia?")
		if response == True:
			for name in clients_list:
				client_socket.send(("shutdown /"+name).encode("utf8"))
				sleep(1)

def shutdown_all_clients():
	response = messagebox.askyesno("Uwaga!","Czy na pewno chcesz wyłączyć wszystkie urządzenia?")
	if response == True:
		client_socket.send("shutdown -all".encode("utf8"))

def msg_send():
	clients_list = get_selected_clients()
	if clients_list == []:
		info_text.insert(0.0, "Wybierz odbiorców!\n")
	else:
		msg = msg_entry.get(1.0,'end-1c')
		msg_entry.delete(1.0,END)
		if msg == "":
			info_text.insert(0.0, "Napisz wiadomość!\n")
		else:
			for name in clients_list:
				client_socket.send(("msg /"+name+" //"+msg).encode("utf8"))
				sleep(1)

def msg_send_all():
	msg = msg_entry.get(1.0,'end-1c')
	msg_entry.delete(1.0,END)
	if msg == "":
		info_text.insert(0.0, "Napisz wiadomość!\n")
	else:
		client_socket.send(("msg -all /"+msg).encode("utf8"))

def loadfile():
	filename = filedialog.askopenfilename(initialdir = "/",title = "Wybierz plik")
	filename_entry.delete(0,END)
	filename_entry.insert(0,filename)
	print(filename)

def thread_sendfile():
	sendfile_thread = Thread(target=sendfile)
	sendfile_thread.start()


def sendfile():
	global client_socket

	global isConnected
	try:
		client_name = get_selected_clients()[0]
		client_socket.send(("wanttosendfile "+client_name).encode("utf8"))
		path = filename_entry.get()
		filename = os.path.basename(path)
		client_socket.send(filename.encode("utf8"))
		sleep(1)
		filesize = stat(path).st_size
		client_socket.send(str(filesize).encode("utf8"))
		filesize = filesize/BUFSIZ
		percentage = 1
		last_percent = 0
		info_text.insert(1.0,"Wysyłanie: 0%")
		file = open(path, 'rb')
		l = file.read(BUFSIZ)
		while (l):
			client_socket.send(l)
			l = file.read(BUFSIZ)
			percentage+=1
			percent = int((percentage/filesize)*100)
			if(percent != last_percent):
				info_text.delete(1.11,END)#int((percentage/filesize)*100)
				info_text.insert(1.11, str(percent)+"%")
				last_percent = percent
		file.close()
		client_socket.shutdown(SHUT_WR)
		#client_socket.send("Koniec wysylania".encode("utf8"))
		messagebox.showinfo("","Plik wysłany!")
		isConnected=False
	except Exception as e:
		print(e)
		print('Error line: %s' %sys.exc_info()[-1].tb_lineno)

def motion(event):
	global mouse_x
	global mouse_y
	mouse_x, mouse_y = event.x, event.y
	#print('{}, {}'.format(mouse_x, mouse_y))

def clickL(event):
	global mouse_click
	mouse_click = '1'

def releaseL(event):
	global mouse_click
	mouse_click = '0'

def key(event):
	global pressed_key
	global key_click
	if event.keycode != 16 and event.keycode != 17 and event.keycode != 18:
		pressed_key = event.char
		key_click = '1'

def remote_control():
	global last_preview_width
	global last_preview_height
	global rc_window
	global img
	global rcc
	global rcc1
	rcc=1
	rcc1=1
	client_name = get_selected_clients()[0]
	client_socket.send(("wanttorcclient "+client_name).encode("utf8"))
	rc_window = Toplevel()
	rc_window.title('Zdalna kontrola')
	rc_window.minsize(960,540)
	rc_window.bind('<Motion>', motion)
	rc_window.bind('<Button-1>', clickL)
	rc_window.bind('<ButtonRelease-1>',releaseL)
	rc_window.bind("<Key>", key)
	rc_window.protocol("WM_DELETE_WINDOW", on_closing)

	last_preview_width = 960
	last_preview_height = 540
	
	#bb_img = client_socket.recv(2000000)
	#b_img = Image.open(io.BytesIO(bb_img))
	#img = ImageTk.PhotoImage(b_img)
	#img_label = Label(rc_window, image=img)
	#img_label.grid(row=0, column=0,sticky=NW)

	display_thread = Thread(target=get_display_image)
	display_thread.start()
	
	#motion_thread = Thread(target=motion)
	#motion_thread.start()


def get_display_image():
	global last_preview_width
	global last_preview_height
	global img
	global img2
	global rcc
	global rcc1
	global mouse_click
	global key_click
	rc_window.update()
	while(1):
		
			
		#preview_width = rc_window.winfo_width()
		#preview_height =rc_window.winfo_height()
		
		#if (preview_width == last_preview_width) & (preview_height == last_preview_height):
			try:
			#img = ImageGrab.grab()
				
				bb_img = client_socket.recv(250000)
				if bb_img.startswith(b'\xff\xd8\xff\xe0\x00\x10JFIF'):
					#print("odebrano 1")
					img = Image.open(io.BytesIO(bb_img))
					#img.thumbnail([preview_width-5,preview_height-5])
					#img.thumbnail([960,540])
					img = ImageTk.PhotoImage(img)
					img_label = Label(rc_window, image=img)
					img_label.grid(row=0, column=0,sticky=NW)
					im = img

				if(rcc==0):
					client_socket.send("endrc".encode("utf8"))
					rc_window.destroy()
					rcc1 = 0
					
					break
				mouse_xy = str(int(mouse_x*2))+'#$'+str(int(mouse_y*2))+'#$'+ mouse_click+'#$'+ key_click + '#$' + pressed_key
				#print(mouse_xy)
				#mouse_click = '0'
				key_click = '0'
				client_socket.send(mouse_xy.encode("utf8"))
				#client_socket.send(mouse_xy.encode("utf8"))
				#print("Wysłano mouse")

#				bb_img2 = client_socket.recv(500000)
#				if bb_img2.startswith(b'\xff\xd8\xff\xe0\x00\x10JFIF'):
#					#print("odebrano 2")
#					img2 = Image.open(io.BytesIO(bb_img2))
#					#img2.thumbnail([960,540 ])
#			
#					img2 = ImageTk.PhotoImage(img2)
#					img_label = Label(rc_window, image=img2)
#					img_label.grid(row=0, column=0,sticky=NW)
#					im2= img2
#
#				mouse_xy = str(int(mouse_x*2))+' '+str(int(mouse_y*2))+' '+ mouse_click +' '+ key_click + ' ' + pressed_key
#				#print(mouse_xy)
#				mouse_click = '0'
#				key_click = '0'
#				client_socket.send(mouse_xy.encode("utf8"))
				
				#sleep(0.1)
			except Exception as e:
				#img_label = Label(rc_window, image=img2)
				#img_label.grid(row=0, column=0,sticky=NW)
				print(e)
		
			
		#else:
			#sleep(0.5)

		#last_preview_width = preview_width
		#last_preview_height = preview_height

#--------------------------------------------------------------------

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

def send():
	while True:
		send_msg = input()

		client_socket.send(send_msg.encode("utf8"))
		#print('Recived: ')



def receive():

	global client_socket

	global isConnected
	global rcc
	global rcc1
	while True:

		try:
			if isConnected == False:
				#print("Attemping to reconnect...")

				client_socket = socket(AF_INET, SOCK_STREAM)

				client_socket.connect_ex(ADDR)

				client_socket.send(bytes(gethostname().encode("utf8")))
				
				checkUpdate()

				isConnected = True

			if(rcc1==0):
				msg = client_socket.recv(BUFSIZ).decode("utf8")
				#print("Recived: ")

				if msg == "startrc":
					rcc=1
					rcc1=1
					print("rcc=1")

				if msg == "turn off":
					 #client_socket.send(bytes('turning off'.encode("utf8")))

					#client_socket.close()

					if platform.system().lower()=='windows':
						os.system("msg %username% Niski poziom naladowania UPS. Komputer zostanie za chwile wylaczony")
						
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
				else:
					if msg.startswith("{"):
						clients_listbox.delete(0)
						connected = loads(msg)
						#for x, y in connected.items():
							#print(x,y)
						for x,y in connected.items():
							if y == '[x]':
								clients_listbox.insert(END,x)

					elif ('wanttorcclient' in msg) & (platform.system().lower()=='windows'):
						img = ImageGrab.grab()
						img.thumbnail([955,535])
						imgByteArr = io.BytesIO()
						img.save(imgByteArr, format='PNG')
						print(imgByteArr.getbuffer().nbytes)
						imgByteArr = imgByteArr.getvalue()
						
						client_socket.send(imgByteArr)

					else:
						#TK wyswietlanie 
						print("Odebrano:"+msg)

				if not msg:
					print('czas na break')
					break
			else:
				sleep(2)
				print('rcc: '+str(rcc))

		except Exception as e:
			isConnected = False
			#sleep(300)
			print(e)
			print('Error line: %s' %sys.exc_info()[-1].tb_lineno)
			#continue


def on_closing(event=None):
	global rcc
	
	rcc=0



#--------------------------------------------------------------------
rcc=0
rcc1=0
mouse_x=0
mouse_y=0
mouse_click='0'
pressed_key='a'
key_click='0'
clientVersion = '1.0'

HOST = '192.168.0.2'

PORT = 5000

BUFSIZ = 1024

ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)

#--------------------------------------------------------------------
root = Tk()
root.title('Manager')

devices_frame = LabelFrame(root, text="Podłączone urządzenia")
devices_frame.grid(row=0, column=0)

clients_frame = Frame(devices_frame)
scrollbar = Scrollbar(clients_frame)
clients_listbox = Listbox(clients_frame, height=7, width=30, selectmode=MULTIPLE, yscrollcommand=scrollbar.set)
scrollbar.pack(side=RIGHT, fill=Y)
clients_listbox.pack(side=LEFT, fill=BOTH)
clients_listbox.pack()
clients_frame.pack()
refresh_button = Button(devices_frame,text="Odśwież",command=refresh).pack()

info_frame = LabelFrame(root,text="Informacje:")
info_frame.grid(row=0, column=1, sticky=N)
info_text = Text(info_frame, width=25, height=5)
info_text.pack()

msg_frame = LabelFrame(root, text="Wyślij wiadomość")
msg_frame.grid(row=1, column=0)
msg_entry = Text(msg_frame, width=25, height=5)
msg_entry.pack()
msg_button = Button(msg_frame, text="Wyślij", command=msg_send).pack(side=LEFT)
msg_all_button = Button(msg_frame, text="Wyślij wszystkim", command=msg_send_all).pack(side=RIGHT)

sendfile_frame = LabelFrame(root, text="Wyślij plik")
sendfile_frame.grid(row=1, column=1, sticky=N)
loadfile_button = Button(sendfile_frame, text="Wybierz plik", command=loadfile).grid(row=0, column=1)
filename_entry = Entry(sendfile_frame)
filename_entry.grid(row=0, column=0)
sendfile_button = Button(sendfile_frame, text="Wyślij plik", command=thread_sendfile).grid(row=1, column=1, sticky=E)

shutdown_frame = LabelFrame(root, text="Wyłącz urządzenie")
shutdown_frame.grid(row=1, column=1, sticky=S, ipadx=30)
shutdown_button = Button(shutdown_frame, text="Wyłącz", command=shutdown_clients).pack(side=LEFT)
shutdown_all_button = Button(shutdown_frame, text="Wyłącz wszystkie",command=shutdown_all_clients).pack(side=RIGHT)

rc_frame = LabelFrame(root,text="Zdalna kontrola")
rc_frame.grid(row=2, column=0, ipadx=45)
rc_button = Button(rc_frame, text="Rozpocznij kontrolę", command=remote_control).pack()
#--------------------------------------------------------------------

while True:

	if client_socket.connect_ex(ADDR) == 0:
		break
	sleep(300)
	#print("Cannot connect")

#print("Connected")

isConnected = True

client_socket.send(bytes(gethostname().encode("utf8")))

checkUpdate()

receive_thread = Thread(target=receive)

receive_thread.start()

root.mainloop()

#Poprzednia wersja konsolowa
if gethostname() == 'IT':
	send_thread = Thread(target=send)

	send_thread.start()
	print("Type command (help - for all commands):")
