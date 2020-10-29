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
					if(message == "OK+"):
						message += username
					else:
						message += "|{}".format( username )
				message += "\r\n"
			except:
				sendER( s, 7 )
			else:
				s.sendall( message.encode( "ascii" ) )

		#LSPH - Solicitud de listado de fotos de usuario
		elif message.startswith( szasar.Command.PhotoList ):
			if state != State.Main:
				sendER( s )
        				continue
			filename = os.path.join( FILES_PATH, message[4:] )
			try:
				filesize = os.path.getsize( filename )
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
                #UPLO
		elif message.startswith( szasar.Command.Upload ):
			if state != State.Main:
				sendER( s )
				continue
			if user == 0:
				sendER( s, 7 )
				continue
			filename, filesize = message[4:].split('?')
			filesize = int(filesize)
			if filesize > MAX_FILE_SIZE:
				sendER( s, 8 )
				continue
			svfs = os.statvfs( FILES_PATH )
			if filesize + SPACE_MARGIN > svfs.f_bsize * svfs.f_bavail:
				sendER( s, 9 )
				continue
			sendOK( s )
			state = State.Uploading
                #PHOT
		elif message.startswith( szasar.Command.Photo ):
			if state != State.Uploading:
				sendER( s )
				continue
			state = State.Main
			try:
				with open( os.path.join( FILES_PATH, filename), "wb" ) as f:
					filedata = szasar.recvall( s, filesize )
					f.write( filedata )
			except:
				sendER( s, 10 )
			else:
				sendOK( s )

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
