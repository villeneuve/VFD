import network
import socket
import machine
import time
import json
import uasyncio as asyncio

# --- VARIABLES GLOBALES DE CONTRÔLE ---
ap = None
serveur_tache = None  # Stockera la tâche du serveur
serveur_actif = False

# ==========================================
# FONCTIONS FACTICES (A REMPLACER)
# ==========================================
def GetStatus():
    return (True, False, False, 25.12, 33.25)

def start(): print("ACTION: Start")
def stop(): print("ACTION: Stop")
def SetF(v): print(f"ACTION: SetF {v}")

# ==========================================
# PAGE WEB HTML / JAVASCRIPT
# ==========================================
# On utilise Javascript pour :
# 1. Rafraichir les données en arrière-plan (AJAX) toutes les 5s
# 2. Générer les listes déroulantes de dates sans surcharger la RAM du Pico
# 3. Envoyer les commandes sans recharger la page
PAGE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pico Piscine</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .titre { font-weight: bold; color: black; }
        .bouton { padding: 10px 15px; margin: 5px; cursor: pointer; }
        hr { margin: 20px 0; }
    </style>
</head>
<body>
    <h2>Contrôle Piscine</h2>
    
    <div>
        <span class="titre">Etat VFD: </span><span id="vfd_etat" style="color: black;">---</span><br>
        <span class="titre">Etat POMPE: </span><span id="pompe_etat" style="color: black;">---</span><br>
        <span class="titre">Defaut: </span><span id="defaut_etat" style="color: black;">---</span><br>
        <span class="titre">Frequence mesurée: </span><span id="freq_mesuree" style="color: black;">0.00</span><br>
        <span class="titre">Consigne Frequence: </span><span id="freq_consigne" style="color: black;">0.00</span>
    </div>

    <hr>
    
    <button class="bouton" onclick="fetch('/action?cmd=start')">START</button>
    <button class="bouton" onclick="fetch('/action?cmd=stop')">STOP</button>
    
    <hr>
    
    <span class="titre">REGLAGE CONSIGNE FREQUENCE:</span><br>
    <input type="range" id="sliderF" min="0" max="50" step="0.01" value="0" oninput="document.getElementById('valF').innerText = this.value">
    <span id="valF">0</span> Hz
    <button class="bouton" onclick="fetch('/action?cmd=setf&val=' + document.getElementById('sliderF').value)">Appliquer</button>

    <hr>
    
    <span class="titre">REGLAGE DATE ET HEURE:</span><br>
    <select id="sel_jj"></select> - 
    <select id="sel_mm"></select> - 
    <select id="sel_aaaa"></select> &nbsp;
    <select id="sel_hh"></select> : 
    <select id="sel_min"></select> : 
    <select id="sel_ss"></select>
    <button class="bouton" onclick="envoyerDate()">Valider Date/Heure</button>

    <hr>

    <button class="bouton" onclick="window.location.href='/prog'">REGLAGE PROGRAMME JOURNALIER</button>

    <script>
        // Fonction de rafraichissement du statut
        function rafraichirStatut() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    let vfd = document.getElementById('vfd_etat');
                    vfd.innerText = data[0] ? "ON" : "OFF";
                    vfd.style.color = data[0] ? "green" : "black";

                    let pompe = document.getElementById('pompe_etat');
                    pompe.innerText = data[1] ? "ON" : "OFF";
                    pompe.style.color = data[1] ? "green" : "black";

                    let defaut = document.getElementById('defaut_etat');
                    defaut.innerText = data[2] ? "DISJONCTION" : "NON";
                    defaut.style.color = data[2] ? "red" : "black";

                    document.getElementById('freq_mesuree').innerText = data[3].toFixed(2);
                    document.getElementById('freq_consigne').innerText = data[4].toFixed(2);
                })
                .catch(err => console.log("Erreur de rafraîchissement"));
        }

        // Lancement immédiat puis toutes les 5 secondes
        rafraichirStatut();
        setInterval(rafraichirStatut, 5000);

        // Remplissage des listes déroulantes pour économiser la RAM du Pico
        function pop(id, min, max) {
            let s = document.getElementById(id);
            for(let i=min; i<=max; i++) {
                let v = i.toString().padStart(2, '0');
                s.options.add(new Option(v, i));
            }
        }
        pop('sel_jj', 1, 31); pop('sel_mm', 1, 12); pop('sel_aaaa', 2024, 2050);
        pop('sel_hh', 0, 23); pop('sel_min', 0, 59); pop('sel_ss', 0, 59);

        // Envoi de la date au Pico
        function envoyerDate() {
            let j = document.getElementById('sel_jj').value;
            let m = document.getElementById('sel_mm').value;
            let a = document.getElementById('sel_aaaa').value;
            let h = document.getElementById('sel_hh').value;
            let min = document.getElementById('sel_min').value;
            let s = document.getElementById('sel_ss').value;
            fetch(`/action?cmd=rtc&j=${j}&m=${m}&a=${a}&h=${h}&min=${min}&s=${s}`);
        }
    </script>
</body>
</html>
"""


# ==========================================
# LOGIQUE DU SERVEUR (ASYNCHRONE)
# ==========================================

async def gerer_client(reader, writer):
    """Gère une connexion client individuelle sans bloquer le reste."""
    try:
        request_line = await reader.readline()
        if not request_line:
            return
        
        # On vide le reste du buffer de lecture
        while await reader.readline() != b"\r\n":
            pass

        url = request_line.decode().split()[1] if len(request_line.split()) > 1 else "/"

        if url == "/":
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + PAGE_HTML
        elif url == "/status":
            response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + json.dumps(GetStatus())
        elif url.startswith("/action?"):
            # Analyse des commandes
            params = url.split('?')[1]
            param_dict = {}
            for couple in params.split('&'):
                k, v = couple.split('=')
                param_dict[k] = v
            cmd = param_dict.get('cmd')
            if cmd == 'start':
                start()
            elif cmd == 'stop':
                stop()
            elif cmd == 'setf':
                val = float(param_dict.get('val', 0))
                SetF(val)
            elif cmd == 'rtc':
                j = int(param_dict.get('j', 1))
                m = int(param_dict.get('m', 1))
                a = int(param_dict.get('a', 2024))
                h = int(param_dict.get('h', 0))
                min_ = int(param_dict.get('min', 0))
                sec = int(param_dict.get('s', 0))
                # Mise à jour de l'heure système (RTC) du Pico W
                # Format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
                rtc = machine.RTC()
                rtc.datetime((a, m, j, 0, h, min_, sec, 0))
                print(f"ACTION: RTC mis à jour: {j:02d}/{m:02d}/{a} {h:02d}:{min_:02d}:{sec:02d}")
            
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"

        writer.write(response.encode())
        await writer.drain()
    except Exception as e:
        print("Erreur client:", e)
    finally:
        await writer.wait_closed()

async def serveur_loop():
    """La boucle principale du serveur qui tourne en tâche de fond."""
    global serveur_actif
    print("Serveur Web démarré sur le port 80.")
    server = await asyncio.start_server(gerer_client, "0.0.0.0", 80)
    serveur_actif = True
    
    try:
        while serveur_actif:
            await asyncio.sleep(1) # Laisse du temps processeur aux autres tâches
    except asyncio.CancelledError:
        pass
    finally:
        server.close()
        await server.wait_closed()
        print("Serveur Web stoppé.")

# ==========================================
# COMMANDES UTILISATEUR
# ==========================================

def demarrer_serveur():
    global ap, serveur_tache, serveur_actif
    
    if serveur_actif:
        print("Le serveur tourne déjà.")
        return ap.ifconfig()[0]

    # 1. WiFi AP
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid='PicoPiscine', password='laquinta')
    ap.active(True)
    while not ap.active(): time.sleep(0.1)
    print(f"WiFi AP 'PicoPiscine' prêt. IP: {ap.ifconfig()[0]}")

    # 2. Lancement de la tâche de fond
    # Note: On utilise get_event_loop() pour injecter la tâche dans la boucle globale
    loop = asyncio.get_event_loop()
    serveur_tache = loop.create_task(serveur_loop())
    return ap.ifconfig()[0]

def stop_serveur():
    global ap, serveur_tache, serveur_actif
    
    if not serveur_actif:
        print("Le serveur n'est pas lancé.")
        return

    serveur_actif = False
    if serveur_tache:
        serveur_tache.cancel()
    
    if ap:
        ap.active(False)
    
    print("Demande d'arrêt envoyée.")


