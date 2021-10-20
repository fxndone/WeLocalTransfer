import os
import socket
import hashlib
import threading
import time

def SHA(bts):
	"""Return sha256 of bytes passed as arg"""
	return hashlib.sha256(bts).hexdigest()

def Alls(path):
	alls = []
	for ele in os.listdir(path):
		if os.path.isfile(os.path.join(path, ele)):
			alls.append(os.path.join(path, ele))
		else:
			alls += Alls(os.path.join(path, ele))
	return alls

def ListDir(path):
	"""Return all files in a dir (except .env)"""
	listdir = Alls(path)
	cleaned = []
	for ele in [".env", ".", "..", "./", "../"]:
		try:
			listdir.remove(ele)
		except:
			pass
	for ele in listdir:
		cleaned.append(ele[len(dirname):])
	return cleaned

def Send(file, host):
	"""Send <file> to <host>"""
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 4096

	port = 2020
	filename = file
	filesize = os.path.getsize(filename)

	s = socket.socket()
	print(f"[+]Connecting to {host}:{str(port)}")
	s.connect((host, port))
	print("[+]Connected")

	s.send(f"{filename}{SEPARATOR}{filesize}".encode())

	with open(filename, "rb") as r:
		s.send(SHA(r.read()).encode())
		r.close()
	time.sleep(1)
	with open(filename, "rb") as f:
		while True:
			bytes_read = f.read(BUFFER_SIZE)
			if not bytes_read:
				break
			s.sendall(bytes_read)
		f.close()
	s.close()

def ServGetFile():
	"""Receive file and store in dirname"""
	SERVER_HOST = "0.0.0.0"
	SERVER_PORT = 5050

	BUFFER_SIZE = 4096
	SEPARATOR = "<SEPARATOR>"

	s = socket.socket()
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	s.bind((SERVER_HOST, SERVER_PORT))

	s.listen(5)

	client_socket, address = s.accept()

	print(f"[+] {address} is connected.")

	received = client_socket.recv(BUFFER_SIZE).decode()
	try:
		filename, filesize = received.split(SEPARATOR)
	except:
		print(received)

	filename = os.path.join(dirname,os.path.basename(filename))
	filesize = int(filesize)

	hashed = client_socket.recv(BUFFER_SIZE).decode()

	with open(filename, "wb") as f:
		print(f"[+]Receiving {os.path.basename(filename)}")
		while True:
			bytes_read = client_socket.recv(BUFFER_SIZE)
			if not bytes_read:
				break
			f.write(bytes_read)
	print("[+]Calculating hashes")
	with open(filename, "rb") as r:
		hashed2 = SHA(r.read())
	if hashed != hashed2:
		print("[!]Hashes doesn't match !")
		print("[!]Received   :",hashed)
		print("[!]Calculated :",hashed2)
		os.remove(filename)
	else:
		print(f"[+]Hashes corespond, saving file {filename}")
	client_socket.close()
	s.close()

def ServGetAllFiles(event):
	"""while true receive files"""
	while not event.is_set():
		ServGetFile()

servEvent = threading.Event()
spliter = "<SPLIT>"

name = input("[?]Server name : ")
s = socket.socket()
s.bind(("0.0.0.0", 8080))
s.listen()
print("[+]Binded on port 8080")

dirname = "files"
if not dirname.endswith("/"):
	dirname += "/"
good = False
while not good:
	try:
		os.mkdir(dirname)
	except:
		good = True #dirname += "1"
	else:
		good = True

threading.Thread(target=ServGetAllFiles, args=(servEvent,), daemon=True).start()

while True:
	try:
		conn, add = s.accept()
		print(f"[+]Connected to {add}")
		content = conn.recv(2048).decode()
		if content == "SERVICE":
			print("[+]User asking for service name")
			conn.send("WeLocalTransfer Server version 1.0 beta".encode())
		elif content == "NAME":
			print("[+]User asking for server name")
			conn.send(name.encode())
		elif content == "FILES":
			print("[+]User asking for files list")
			conn.send(spliter.join(ListDir(dirname)).encode())
		elif content == "DIRNAME":
			print("[+]User asking for dirname")
			conn.send(dirname.encode())
		elif content.startswith("SEND"):
			print("[+]User asking for sending a file")
			_, filename, host = content.split(spliter)
			if os.path.isfile(os.path.join(dirname, filename)):
				Send(os.path.join(dirname, filename), host)
			else:
				print(f"[!]File {os.path.join(dirname, filename)} doesn't exist !")
				with open("null", "w+"):
					pass
				Send("null", host)
				os.remove("null")
		elif os.path.isfile(content):
			print(f"[+]User wanting file {content}")
			Send(content)
	except Exception as e:
		print(e)
		break
servEvent.set()
s.close()
