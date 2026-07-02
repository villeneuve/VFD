#!/usr/bin/env python3
import serial
import threading
import time
import sys
import datetime
import socket

# --- Configuration ---
#SERIAL_PORT = '/dev/ttyACM0' !!!!!!!!!!!!!!!!!!!!!!!!  Modif special CarbetBox
# mais modif intelligente a conserver! Mais il faut utiliser udev pour creer des liens
SERIAL_PORT = '/dev/ttyPicoREPL'
SERIAL_BAUD = 115200
SOCKET_HOST = '0.0.0.0'  # 'localhost' pour le même PC, '0.0.0.0' pour accepter le réseau
SOCKET_PORT = 12345
LOG_FILE = "/tmp/logvfd.txt"

# ---- Temporisation 3s pour laisser le systeme creer /dev/ttyPicoREPL au boot ---
print('Sleep 3s. Wait :)')
time.sleep(3)


# Verrou pour empêcher plusieurs clients socket d'écrire en même temps sur le CP
ser_lock = threading.Lock()
# Événement pour synchroniser l'arrêt des threads
stop_event = threading.Event()


# --- FONCTION GESTIONNAIRE DE CLIENT SOCKET ---

def handle(conn, addr):
    print(f"[Socket] Connexion de {addr} établie.")
    with conn:
        while not stop_event.is_set():
            try:
                data = conn.recv(1024)
                if not data:
                    break  # Le client s'est déconnecté
                    
                timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
                print(f"[Socket] {timestamp} Reçu de {addr} : {data}")
                
                # Écriture sécurisée (un seul thread à la fois)
                with ser_lock:
                    ser.write(data)
                    
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[Socket] Erreur avec le client {addr} : {e}")
                break
    print(f"[Socket] Connexion de {addr} fermée.")


# --- PREMIÈRE PARTIE : Lecture Série non-bloquante (Arrière-plan) ---

def serial_reader_thread():
    buffer = b""
    print("[Série] Thread de lecture démarré.")
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                bytes_recus = ser.read(ser.in_waiting)
                buffer += bytes_recus
                
                if buffer.endswith(b"\n"):
                    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
                    lignes = buffer.decode('utf-8', errors='ignore').splitlines()
                    
                    for ligne in lignes:
                        f.write(f"{timestamp}{ligne}\n")
                    f.flush()
                    
                    buffer = b""
            else:
                time.sleep(0.01)
        except Exception as e:
            print(f"\n[Série] Erreur lors de la lecture : {e}")
            break
    print("[Série] Thread de lecture arrêté.")


# --- INITIALISATION DES MATÉRIELS ET FICHIERS ---

# 1. Ouverture du port Série
try:
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD)
except serial.SerialException as e:
    print(f"Erreur : Impossible d'ouvrir le port {SERIAL_PORT} ({e})")
    sys.exit(1)

# 2. Ouverture du fichier de Log
try:
    f = open(LOG_FILE, "a")
except IOError as e:
    print(f"Erreur : Impossible d'ouvrir le fichier {LOG_FILE} ({e})")
    ser.close()
    sys.exit(1)

# 3. Initialisation du Serveur Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Option pour réutiliser le port immédiatement après un redémarrage
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind((SOCKET_HOST, SOCKET_PORT))
    sock.listen()
    print(f"[Serveur] Écoute TCP activée sur {SOCKET_HOST}:{SOCKET_PORT}")
except Exception as e:
    print(f"Erreur : Impossible de lancer le serveur Socket ({e})")
    f.close()
    ser.close()
    sys.exit(1)


# --- DÉMARRAGE DES THREADS ET BOUCLE PRINCIPALE ---

# Lancement du lecteur série en arrière-plan
reader_thread = threading.Thread(target=serial_reader_thread, daemon=True)
reader_thread.start()

print("Système prêt. En attente de commandes via Socket... (Ctrl+C pour quitter)")

try:
    while True:
        # Configuration d'un timeout court pour permettre à l'écoute d'être interrompue par Ctrl+C
        sock.settimeout(1.0)
        try:
            conn, addr = sock.accept()
            # Lance un thread pour chaque nouveau client connecté
            threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
        except socket.timeout:
            continue  # Permet juste de vérifier régulièrement si Ctrl+C a été pressé
except KeyboardInterrupt:
    print("\n[Système] Interruption Ctrl+C détectée. Fermeture en cours...")
finally:
    # --- Nettoyage propre ---
    stop_event.set()
    sock.close()
    reader_thread.join(timeout=1)
    f.close()
    ser.close()
    print("Retour au prompt shell GNU/Linux. Au revoir.")
    sys.exit(0)
