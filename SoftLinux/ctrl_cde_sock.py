#!/usr/bin/env python3

# ce code roule de pair avec /etc/systemd/system/vfd-ctrl.service
# Si ce script plante (si par ex le pico est reset ou mis hors tension)
# donc perte de /dev/ttyPicoREPL et arret thread read serial
# systemd tentera indefiniment toutes les 10 secondes de relancer ce 
# script (StartLimitIntervalSec=0) toutes les 10 secondes
# Donc meme si le pico est hors/sous tension ce les logs, mqtt etc..
# tout devrait repartir quand le pico re-apparait.

import serial
import threading
import time
import sys
import socket
import syslog

# --- Configuration ---
SERIAL_PORT = '/dev/ttyPicoREPL'
SERIAL_BAUD = 115200
SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 12345

# Temporisation 3s pour laisser le systeme creer /dev/ttyPicoREPL au boot
print('Sleep 3s. Wait :)')
time.sleep(3)

# Verrou pour empêcher plusieurs clients socket d'écrire en même temps
ser_lock = threading.Lock()
# Événement pour synchroniser l'arrêt des threads
stop_event = threading.Event()

#  FONCTION GESTIONNAIRE DE CLIENT SOCKET
def handle(conn, addr):
    print(f"[Socket] Connexion de {addr} établie.")
    with conn:
        while not stop_event.is_set():
            try:
                data = conn.recv(1024)
                if not data:
                    break  # Le client s'est déconnecté
                    
                # Pas de timestamp ici, systemd s'en occupe
                print(f"[Socket] Reçu de {addr} : {data}")
                
                # Écriture sécurisée (un seul thread à la fois)
                with ser_lock:
                    ser.write(data)
                    
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[Socket] Erreur avec le client {addr} : {e}")
                break
    print(f"[Socket] Connexion de {addr} fermée.")

# PREMIÈRE PARTIE : Lecture Série non-bloquante (Arrière-plan)
def serial_reader_thread():
    buffer = b""
    print("[Série] Thread de lecture démarré.")
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                bytes_recus = ser.read(ser.in_waiting)
                buffer += bytes_recus
                
                if buffer.endswith(b"\n"):
                    lignes = buffer.decode('utf-8', errors='ignore').splitlines()
                    # Envoi direct des lignes de l'UART dans syslog
                    for ligne in lignes:
                        syslog.syslog(syslog.LOG_INFO, ligne)
                    buffer = b""
            else:
                time.sleep(0.01)
        except Exception as e:
            print(f"\n[Série] Erreur critique sur le port série : {e}")
            break  # Sortie du thread en cas d'I/O Error
    print("[Série] Thread de lecture arrêté.")


# --- INITIALISATION ---

# 1. Ouverture du port Série
try:
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD)
except serial.SerialException as e:
    print(f"Erreur : Impossible d'ouvrir le port {SERIAL_PORT} ({e})")
    sys.exit(1)

# 2. Initialisation de Syslog pour l'UART
# Chaque message envoyé via syslog.syslog() aura l'identifiant 'vfd-uart'
syslog.openlog(ident="vfd-uart", facility=syslog.LOG_USER)

# 3. Initialisation du Serveur Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind((SOCKET_HOST, SOCKET_PORT))
    sock.listen()
    print(f"[Serveur] Écoute TCP activée sur {SOCKET_HOST}:{SOCKET_PORT}")
except Exception as e:
    print(f"Erreur : Impossible de lancer le serveur Socket ({e})")
    ser.close()
    sys.exit(1)


# --- DÉMARRAGE THREADS ET SURVEILLANCE ---

# Lancement du lecteur série en arrière-plan
reader_thread = threading.Thread(target=serial_reader_thread, daemon=True)
reader_thread.start()

print("Système prêt. En attente de commandes via Socket... (Ctrl+C pour quitter)")

# Code de sortie par défaut (0 = succès)
exit_code = 0

try:
    while not stop_event.is_set():
        # VÉRIFICATION CRITIQUE : Le thread série est-il toujours en vie ?
        if not reader_thread.is_alive():
            raise RuntimeError("Le thread de lecture série a planté (déconnexion MCU ?).")

        sock.settimeout(1.0)
        try:
            conn, addr = sock.accept()
            threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
        except socket.timeout:
            continue

except KeyboardInterrupt:
    print("\n[Système] Arrêt demandé (Ctrl+C / SIGINT).")
    exit_code = 0  # Arrêt volontaire -> Code 0 (Systemd ne redémarre pas)

except Exception as e:
    print(f"\n[Système] Erreur fatale : {e}")
    exit_code = 1  # Crash -> Code 1 (Systemd va redémarrer le service)

finally:
    stop_event.set()
    sock.close()
    reader_thread.join(timeout=1)
    try:
        ser.close()
    except Exception:
        pass
    print(f"Fermeture du script avec le code de sortie {exit_code}.")
    sys.exit(exit_code)
