#!/usr/bin/env python3
import serial
import threading
import time
import sys
import datetime  # Ajouté pour la gestion de la date et de l'heure

# --- Configuration et Initialisation ---

try:
    # Configuration commune du port série
    ser = serial.Serial('/dev/ttyACM0', 115200)
except serial.SerialException as e:
    print(f"Erreur : Impossible d'ouvrir le port /dev/ttyACM0 ({e})")
    sys.exit(1)

try:
    # Ouverture préalable du fichier en mode "append"
    f = open("/tmp/logvfd.txt", "a")
except IOError as e:
    print(f"Erreur : Impossible d'ouvrir le fichier /tmp/logvfd.txt ({e})")
    ser.close()
    sys.exit(1)

# Événement pour synchroniser l'arrêt des deux parties
stop_event = threading.Event()


# --- PREMIÈRE PARTIE : Lecture non-bloquante avec Horodatage ---

def serial_reader_thread():
    buffer = b""
    while not stop_event.is_set():
        try:
            # Vérifie si des octets sont disponibles sans bloquer
            if ser.in_waiting > 0:
                bytes_recus = ser.read(ser.in_waiting)
                buffer += bytes_recus
                
                # Si le dernier octet reçu est b"\n"
                if buffer.endswith(b"\n"):
                    # Récupération de la date et heure courante
                    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
                    
                    # Décodage et séparation par ligne pour appliquer le timestamp à chaque ligne
                    lignes = buffer.decode('utf-8', errors='ignore').splitlines()
                    for ligne in lignes:
                        f.write(f"{timestamp}{ligne}\n")
                    
                    f.flush()
                    buffer = b""  # Réinitialisation du buffer
            else:
                # Petite pause pour éviter de consommer 100% du CPU inutilement
                time.sleep(0.01)
        except Exception as e:
            print(f"\nErreur lors de la lecture série : {e}")
            break


# Lancement de la première partie dans un Thread dédié
reader_thread = threading.Thread(target=serial_reader_thread)
reader_thread.daemon = True # Permet au thread de se couper si le programme principal crash
reader_thread.start()


# --- DEUXIÈME PARTIE : Menu Utilisateur (Thread Principal) ---

def afficher_menu():
    print("\n" + "="*30)
    print("1 - Ferme contacteur")
    print("2 - Ouvre contacteur")
    print("3 - Start moteur")
    print("4 - Stop moteur")
    print("5 - Regle frequence")
    print("6 - Lit des registres")
    print("7 - Synchronise l'heure")
    print("8 - Réserve")
    print("9 - Réserve")
    print("0 - Exit")
    print("="*30)

try:
    while True:
        afficher_menu()
        choix = input("Votre choix : ").strip()

        if choix == "1":
            ser.write(b"ContactorOn\n")
            print("-> Envoyé : ContactorOn")
            
        elif choix == "2":
            ser.write(b"ContactorOff\n")
            print("-> Envoyé : ContactorOff")
            
        elif choix == "3":
            ser.write(b"MotorOn\n")
            print("-> Envoyé : MotorOn")
            
        elif choix == "4":
            ser.write(b"MotorOff\n")
            print("-> Envoyé : MotorOff")
            
        elif choix == "5":
            valeur = input("Entrez une valeur de fréquence entière (0 à 50) : ").strip()
            try:
                val_freq = int(valeur)
                if 0 <= val_freq <= 50:
                    commande = f"SetFrequency {val_freq}\n"
                    ser.write(commande.encode('utf-8'))
                    print(f"-> Envoyé : {commande.strip()}")
                else:
                    print("Erreur : La valeur doit être un entier entre 0 et 50.")
            except ValueError:
                print("Erreur : Entrée invalide (un nombre entier est attendu).")
                
        elif choix == "6":
            adresse = input("Entrez l'adresse hexadécimale (ex: 0xFFFF) : ").strip()
            quantite = input("Entrez la quantité de registres (décimal) : ").strip()
            
            if adresse.lower().startswith("0x") and quantite.isdigit():
                commande = f"ReadAnyRegister {adresse} {quantite}\n"
                ser.write(commande.encode('utf-8'))
                print(f"-> Envoyé : {commande.strip()}")
            else:
                print("Erreur : Format de l'adresse (0xFFFF) ou de la quantité invalide.")
                
        elif choix == "7":
            pc_epoch = int(time.time())
            commande = f"SetDateTime {pc_epoch}\n"
            ser.write(commande.encode('utf-8'))
                
        elif choix in ["8", "9"]:
            print("Choix en réserve. Aucune action.")
            
        elif choix == "0":
            print("Arrêt du programme...")
            break
        else:
            print("Choix invalide, veuillez recommencer.")

finally:
    # --- Nettoyage et Fermeture ---
    stop_event.set()              # Signale au thread de lecture de s'arrêter
    reader_thread.join(timeout=1) # Attend la fin du thread proprement
    f.close()                     # Fermeture du fichier de log
    ser.close()                   # Fermeture du port série
    print("Retour au prompt shell GNU/Linux. Au revoir.")
    sys.exit(0)
