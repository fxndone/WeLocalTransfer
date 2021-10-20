import socket
import hashlib
import netifaces
import sys
import threading
import os
import readline
import time


def SHA(bts):
	return hashlib.sha256(bts).hexdigest()

def GetIp():
	addrs = netifaces.ifaddresses('wlan0')
	return addrs[netifaces.AF_INET][0]["addr"]

def GetMask():
	addrs = netifaces.ifaddresses('wlan0')
	return addrs[netifaces.AF_INET][0]["netmask"]

def SendFile(file, host):
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 4096

	port = 5050
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

def RecvFile():
	SERVER_HOST = "0.0.0.0"
	SERVER_PORT = 2020

	BUFFER_SIZE = 4096
	SEPARATOR = "<SEPARATOR>"

	s = socket.socket()

	s.bind((SERVER_HOST, SERVER_PORT))

	s.listen(5)
	print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

	client_socket, address = s.accept()

	print(f"[+] {address} is connected.")

	received = client_socket.recv(BUFFER_SIZE).decode()
	filename, filesize = received.split(SEPARATOR)

	filename = os.path.basename(filename)
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
		print(f"[+]Hashes matches, saving {filename}")
	client_socket.close()
	s.close()

def PrintDict(dico):
	bestK = bestV = 0
	for k, v in dico.items():
		if len(str(k)) > bestK:
			bestK = len(str(k))
		if len(str(v)) > bestV:
			bestV = len(str(v))
	bestK += 2
	bestV += 2
	cut = "+"+"-"*(bestK)+"+"+"-"*(bestV)+"+"
	print(cut)
	for k,v in dico.items():
		string    = "|"
		length    = len(str(k))
		total     = length
		length    = bestK-length
		string   += " "*(length//2)
		total    += length//2
		string   += str(k)
		string   += " "*(bestK-total)
		string   += "|"
		length    = len(str(v))
		total     = length
		length    = bestV-length
		string   += " "*(length//2)
		total    += length//2
		string   += str(v)
		string   += " "*(bestV-total)
		string   += "|"
		print(string)
		print(cut)

def IsServer(ip, servers, ips):
	s = socket.socket()
	try:
		version = GetVersion(ip)
		if version != "WeLocalTransfer Server version 1.0 beta":
			if version != "Error":
				print(f"[!]Found server with ip {ip} but it is not using our current version !")
			raise Exception("except")
		s.connect((ip, 8080))
		s.send("NAME".encode())
		name = s.recv(2048).decode()
		print(f"[+]Found server of {name}")
		servers.append(ip)
	except KeyboardInterrupt:
		s.close()
		IsServer(ip, servers, ips)
		return None
	except:
		pass
	ips.remove(ip)
	s.close()

def GetVersion(ip):
	try:
		s = socket.socket()
		s.connect((ip, 8080))
		s.send("SERVICE".encode())
		output = s.recv(2048).decode()
		s.close()
		return output
	except KeyboardInterrupt:
		s.close()
		return GetVersion(ip)
	except:
		return "Error"

def GetName(ip):
	try:
		s = socket.socket()
		s.connect((ip, 8080))
		s.send("NAME".encode())
		output = s.recv(2048).decode()
		s.close()
		return output
	except KeyboardInterrupt:
		s.close()
		return GetName(ip)

def GetFiles(ip):
	try:
		s = socket.socket()
		s.connect((ip, 8080))
		s.send("FILES".encode())
		output = s.recv(2048).decode().split(spliter)
		s.close()
		return output
	except KeyboardInterrupt:
		s.close()
		return GetFiles(ip)

def GetFile(filename):
	try:
		s = socket.socket()
		s.connect((ip, 8080))
		s.send(spliter.join(["SEND", filename, GetIp()]).encode())
		s.close()
		RecvFile()
	except KeyboardInterrupt:
		s.close()
		GetFile(filename)

def complete(text, state):
	for opt in options:
		if opt.startswith(text):
			if not state:
				return opt
			else:
				state -= 1


readline.parse_and_bind("tab: complete")
readline.set_completer(complete)
print("[+]Scanning for local servers...")
ip   = GetIp()
print(f"[+]Local IP address : {ip}")
mask = GetMask()
print(f"[+]Local Netmask    : {mask}")
ips  = []
base = ""
servers = []
events = []
spliter = "<SPLIT>"
for i in range(4):
	if mask.split(".")[i] == "255":
		base += ip.split(".")[i]
		base += "."
print(f"[+]Base IP          : {base}")
print()
try:
	if base.count(".") == 1:
		for a in range(256):
			for b in range(256):
				for c in range(256):
					ip = base+str(a)+"."+str(b)+"."+str(c)
					ips.append(ip)
					#print(f"[+]Scanning {ip}")
					event = threading.Event()
					events.append(event)
					threading.Thread(target=IsServer, args=(ip, servers, ips), daemon=True).start()
	elif base.count(".") == 2:
		for a in range(256):
			for b in range(256):
				ip = base+str(a)+"."+str(b)
				ips.append(ip)
				#print(f"[+]Scanning {ip}")
				event = threading.Event()
				events.append(event)
				threading.Thread(target=IsServer, args=(ip, servers, ips), daemon=True).start()
	else:
		for a in range(256):
			ip = base+str(a)
			ips.append(ip)
			#print(f"[+]Scanning {ip}")
			event = threading.Event()
			events.append(event)
			threading.Thread(target=IsServer, args=(ip, servers, ips), daemon=True).start()
	while len(ips):
		pass
except KeyboardInterrupt:
	print("[!]Exiting")
	for event in events:
		event.set()
	sys.exit(1)

print()

print("[+]IPs scanned !")

if len(servers) == 0:
	print("\n[!]Could not find any servers :( Exiting")
	sys.exit(1)

dict_servers = {}
names = []
dict_names = {"ID":"Name"}

for serv in servers:
	name = GetName(serv)
	dict_servers[name] = serv
	names.append(name)

for i in range(len(names)):
	dict_names[i+1] = names[i]

PrintDict(dict_servers)
print("\n")
PrintDict(dict_names)
print("\n")
options = list(dict_names)
options.remove("ID")
try:
	chx = input("[?]Server ID to connect : ")
	good = False
	while not good:
		try:
			chx = int(chx)
		except:
			chx = input("[?]Server ID to connect : ")
		else:
			if chx in dict_names.keys():
				good = True
			else:
				chx = input("[?]Server ID to connect : ")
except KeyboardInterrupt:
	print("[+]Exiting ")
	sys.exit(1)
ip = dict_servers[dict_names[chx]]
print(f"[+]Choice : {dict_names[chx]}")
print(f"[+]Connecting to {dict_servers[dict_names[chx]]}")
print()

print("""[ACTIONS]
\t1. Send file to server
\t2. Get file from server
\t3. QUIT
""")

options = ["1", "2", "3"]

try:
	chx = input(">> ")
	good = False
	while not good:
		try:
			chx = int(chx)
		except:
			chx = input(">> ")
		else:
			if chx > 0 and chx < 4:
				good = True
			else:
				chx = input(">> ")
except KeyboardInterrupt:
	print("[+]Exiting")
	sys.exit(1)

while 1:
	if chx == 1:
		try:
			options = os.listdir()
			filepath = input("[?]Filepath : ")
			while not os.path.isfile(filepath):
				filepath = input("[?]Filepath : ")
			SendFile(filepath, ip)
		except KeyboardInterrupt:
			print("[+]Exiting")
			sys.exit(1)
	elif chx == 2:
		try:
			alls = GetFiles(ip)
			if len(alls):
				files = {}
				for i in range(len(alls)):
					files[i+1] = alls[i]
				PrintDict(files)
			else:
				print("[!]There is no files in server !")
				sys.exit(1)
			options = list(files.keys())
			file = input("[?]File ID : ")
			good = False
			while not good:
				try:
					file = int(file)
				except:
					file = input("[?]File ID : ")
				else:
					if file in files.keys():
						good = True
					else:
						file = input("[?]File ID : ")
			GetFile(files[file])
		except KeyboardInterrupt:
			print("[+]Exiting")
			sys.exit(1)
	try:
		options = ["y", "yes", "ok", "oui", "yep"] + ["n", "no", "non", "nop", "niet"]
		chx = input("[?]Continue ? : ")
		while not chx in options:
			chx = input("[?]Continue ? : ")
		if chx in ["n", "no", "non", "nop", "niet"]:
			break
	except KeyboardInterrupt:
		print("[+]Exiting")
		sys.exit(1)
sys.exit(0)
