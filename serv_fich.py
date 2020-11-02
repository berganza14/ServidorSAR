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
	s.sendall( ("OK+{}\r\n".format( params )).encode( ) )
	#Por defecto se codifica en UTF-8
def sendER( s, code=1 ):
	s.sendall( ("ER-{}\r\n".format( code )).encode( ) )

def session( s ):
	state = State.Authentication

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
				#Comprobamos que los credenciales no contengan
				#el caracter "|"
				if ("|" not in user) and ("|" not in pswd):
					user, pswd = message[4:].split("|")
					user_id = USERS.index( user )
					pswd_id = PASSWORDS.index( pswd )
					if(user_id != pswd_id):
						sendER( s, 6 )
						continue
				else:
					sendER( s, 6 )
					continue
			except:
				sendER( s, 6 )
				continue
			else:
				sendOK( s )
				state = State.Main
				logged_user=user

        #LSUS - Solicitud de listado de usuarios
		elif message.startswith( szasar.Command.UserList ):
			if state != State.Main:
				sendER( s )
				continue
			try:
				message = "OK+"
				#Se añaden los usuarios intercalados con "|"
				message = "|".join( USERS )
			except:
				sendER( s, 7 )
			else:
				s.sendOK( message.encode(  ) )

		#LSPH - Solicitud de listado de fotos de usuario
		elif message.startswith( szasar.Command.PhotoList ):
			if state != State.Main:
				sendER( s )
				continue
			#Si no se especifica el usuario
			#se usa el actual logeado
			user = message[4:]
			if(user == ""):
				user = logged_user
			try:
				message == "OK+"
				#Se comprueba que exista la carpeta de las fotos
				if(os.listdir(FILES_PATH) != []):
					enviar = ""
					#Se iteran todos los nombres de los archivos y
					#se seleccionan solo los del usuario de acuerdo al
					#patron 00000descripcion-usuario_peso_.JPG
					for photo_name in os.listdir(FILES_PATH):
						foto_info =  photo_name.split("-")[0]
						usuario_peso = photo_name.split("-")[1]
						usuario = usuario_peso.split("_")[0]
						if(usuario == user):
							enviar = enviar + "{}|".format(foto_info)
					#Se elimina el ultimo | restante
					enviar = enviar[:-1:]
				else:
					sendER( s, 8 )

			except:
				sendER( s, 5 )
				continue
			else:
				sendOK( enviar)

        #PICT - Solicitud de compartir una foto
		elif message.startswith( szasar.Command.Picture ):
			if state != State.Main:
				sendER( s )
				continue
			state = State.Uploading

			descrp, filesize = message[4:].split("|")
			NAME = descrp + "-" + logged_user + "_" + filesize + ".JPG"

			if filesize > MAX_FILE_SIZE:
                sendER ( s, 9 )
				continue
			try:
				#Se hace un open para unicamente crear el archivo con
				#el nombre provisional con los datos actuales
				with open( os.path.join( FILES_PATH, NAME), "wb" ) as f:
					pass
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

			foto = message[4:]

			#Se contabiliza la nueva id
			new_id = int(ID)+1
			#Se comprueba que este dentro del limite
			if(new_id > 99999):
				sendER( s, 10 )
				continue
			new_id = str(new_id)
			ID = new_id
			name_upload = new_id + NAME
			try:
				#Se escriben los datos recividos en el archivo provisional
				with open(os.path.join(FILES_PATH, NAME), "wb") as f:
					f.write(foto.encode())
			except:
				sendER( s )
				continue
			#Se actualiza el nombre con los nuevos datos
			os.rename(os.path.join(FILES_PATH, NAME), os.path.join(FILES_PATH, name_upload))
			NAME = name_upload
			sendOK( s, new_id )
			state = State.Main

        #PHOT - Solicitud de descarga de una foto
		elif message.startswith( szasar.Command.Photo ):
			if state != State.Main:
				sendER( s )
				continue
			id = message[4:]
			file_size = os.path.getsize
			encontrado = False
			try:
				for photo_name in os.listdir(FILES_PATH):
					photo_id = photo_name[0:4]
					if(photo_id == id):
						nom_desc = photo_name
						encontrado = True
				if(encontrado):
					with open( os.path.join( FILES_PATH, nom_desc), "rb" ) as f:
						file = f.read()
				else:
					sendER( s, 11)
					continue
			except:
				sendER( s, 12 )
			else:
				enviar = str(filesize) + '|' + file.decode()
				s.sendall(enviar)

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
