#!/usr/bin/env python3

import socket, sys, os, signal
import szasar

PORT = 6012
FILES_PATH = "files"
USERS_PATH = "users"
MAX_FILE_SIZE = 10 * 1 << 20 # 10 MiB
SPACE_MARGIN = 50 * 1 << 20  # 50 MiB
USERS = ("anonimous", "sar", "sza")
PASSWORDS = ("", "sar", "sza")
logged_user=""
NAME = ""
ID = "00000"
class State:
	Authentication, Main, Downloading, Uploading = range(4)

def sendOK( s, params="" ):
	s.sendall( ("OK+{}\r\n".format( params )).encode( "ascii" ) )

def sendER( s, code=1 ):
	s.sendall( ("ER-{}\r\n".format( code )).encode( "ascii" ) )

def session( s ):
	state = State.Identification

	while True:
		message = szasar.recvline( dialog ).decode( "ascii" )
		if not message:
			return

        #AUTH - Abrir sesion
		if message.startswith( szasar.Command.Authenticate ):
			if( state != State.Authentication ):
				sendER( s )
				continue
			try:
				user, pswd = USERS.index( message[4:].split("|"))
			except:
				sendER( s, 6 )
			else:
				#El user y pswd no pueden tener el caracter "|"
				if "|" not in pswd:
					if "|" not in pswd:
						sendOK( s )
						state = State.Main:
						logged_user=user
					else:
				else:
					sendER( s, 6)
					state = State.Identification

        #LSUS - Solicitud de listado de usuarios
		elif message.startswith( szasar.Command.UserList ):
			if state != State.Main:
				sendER( s )
				continue
			try:
				message = "OK+"
				for username in os.listdir( USERS_PATH ):
                                        #usr1|usr2|usr3|...|usrn|\r\n
                                        #Como hacer para q no quede la ultima barra?
										#Pones la barra antes y empiezas msg con user

				message += "{}|".format( username ) #comprobar ultimo
				message += "\r\n"
			except:
				sendER( s, 7 )
			else:
				s.sendOK( message.encode( "ascii" ) )

		#LSPH - Solicitud de listado de fotos de usuario
		elif message.startswith( szasar.Command.PhotoList ):
			if state != State.Main:
				sendER( s )
				continue
			user = message[4:]
			if(user == ""):
				user = logged_user
			try:
				message == "OK+"
				if(FILES_PATH != ""): #comprobamos que la carpeta de fotos no este vacia(FALTA COMPLETAR)
					enviar = ""
					for photo_name in os.listdir(FILES_PATH):
						usuario = photo_name.split("|")[1]
						foto_info =  photo_name.split("|")[0]
						usuario = usuario.split("/")[0]
						if(usuario == user):
							enviar = enviar + "{}|".format(foto_info) #falta primera instancia
				else:
					sendER( s, 8 )

			except:
				sendER( s, 5 )
				continue
			else:
				sendOK( s, filesize )
				state = State.Downloading
                #PICT - Solicitud de compartir una foto
		elif message.startswith( szasar.Command.Picture ):
			if state != State.Main:
				sendER( s )
				continue
			state = State.Uploading

			descrp, filesize = message[4:].split("|")

			if filesize > MAX_FILE_SIZE:
                                sendER ( s, 9 )

			try:
				with open( os.path.join( FILES_PATH, filename), "wb" ) as f:
					f.write( filedata )
			except:
				sendER( s, 6 )
			else:
				sendOK( s )
				s.sendall( filedata )

		#UPLO - Subida de una foto
		elif message.startswith( szasar.Command.Upload ):
			if state != State.Uploading:
				sendER( s )
				continue
			if user == 0:
				sendER( s, 7 )
				continue

			new_id = int(ID)+1
			if(new_id > 99999):
				sendER( s, 10 )
				continue
			new_id = str(new_id)
			ID = new_id
			name_upload = new_id + NAME
			try:
				with open(os.path.join(FILES_PATH, NAME), "wb") as f:
					f.write(file.encode("ascii"))
			except:
				sendER( s )
				continue
			os.rename(os.path.join(FILES_PATH, NAME), os.path.join(FILES_PATH, name_upload))
			NAME = name_upload
			sendOK( s, new_id )
			state = State.Main

        #PHOT - Solicitud de descarga de una foto
		elif message.startswith( szasar.Command.Photo ):
			if state != State.Uploading:
				sendER( s )
				continue
			state = State.Main
			file_size = os.path.getsize
			try:
				with open( os.path.join( FILES_PATH, filename), "rb" ) as f:
					filedata = szasar.recvall( s, filesize )
					file = f.read()
			except:
				sendER( s, 10 )
			else:
				enviar = str(filesize) + '|' + file.decode()
				sendOK( s , enviar)

                #QUIT
		elif message.startswith( szasar.Command.Quit ):
			sendOK( s )
			return
                #Si llega aquí, comando desconocido (ERR 2)
		else:
			sendER( s, 2 )



if __name__ == "__main__":
	s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )

	s.bind( ('', PORT) )
	s.listen( 5 )

	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	while True:
		dialog, address = s.accept()
		print( "Conexión aceptada del socket {0[0]}:{0[1]}.".format( address ) )
		if( os.fork() ):
			dialog.close()
		else:
			s.close()
			session( dialog )
			dialog.close()
			exit( 0 )
