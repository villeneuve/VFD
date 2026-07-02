import network
import socket
import machine
import time
import json
import asyncio

# --- VARIABLES GLOBALES DE CONTRÔLE ---
ap = None
serveur_tache = None  
serveur_actif = False
vfd = None


def GetStatus():
    global vfd
    cs = vfd.contactor_status
    ol = vfd.isonline
    ms = vfd.MotorStatus()
    if ms is not None:
        if ms == 1: m_s = 'ON'
        elif ms == 3: m_s = 'OFF'
        else: m_s = '?'
    else: m_s = '?'
    
    if ol:
        try:
            fm = int(vfd.frequency_measured) / 100  
            fs = int(vfd.frequency_setpoint) / 200  
        except:
            fm = '?'
            fs = '?'
    else:
        fm = '?'  
        fs = '?'  
    ds = vfd.disj_status
    
    # Récupération de la date et heure courante du Pico
    rtc = machine.RTC()
    now = rtc.datetime() # (YYYY, MM, DD, WD, HH, MM, SS, MS)
    
    return (ol, m_s, ds, fm, fs, now, cs)


def start():
    global vfd
    print("[Webserver] ACTION: Start. Result :", vfd.StartMotor())


def stop():
    global vfd
    print("[Webserver] ACTION: Stop. Result :", vfd.StopMotor())


def SetF(v):
    global vfd
    # Sécurité matérielle stricte au cas où la requête URL tenterait de passer outre le slider HTML
    if v < 20: v = 20
    if v > 50: v = 50
    print(f"[Webserver] ACTION: SetF {v}. Result :", vfd.SetFreq(int(v * 200)))

# ==========================================
# PAGE WEB HTML / JAVASCRIPT
# ==========================================

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
        <span class="titre">Etat Contacteur: </span><span id="contacteur_etat" style="color: black;">---</span><br>
        <span class="titre">Etat VFD: </span><span id="vfd_etat" style="color: black;">---</span><br>
        <span class="titre">Etat POMPE: </span><span id="pompe_etat" style="color: black;">---</span><br>
        <span class="titre">Defaut: </span><span id="defaut_etat" style="color: black;">---</span><br>
        <span class="titre">Frequence mesurée: </span><span id="freq_mesuree" style="color: black;">0.00</span> Hz<br>
        <span class="titre">Consigne Frequence: </span><span id="freq_consigne" style="color: black;">0.00</span> Hz
    </div>

    <hr>
    
    <button class="bouton" onclick="fetch('/action?cmd=start')">START</button>
    <button class="bouton" onclick="fetch('/action?cmd=stop')">STOP</button>
    <button class="bouton" onclick="fetch('/action?cmd=con_on')">Contacteur ON</button>
    <button class="bouton" onclick="fetch('/action?cmd=con_off')">Contacteur OFF</button>
    
    <hr>
    
    <span class="titre">REGLAGE CONSIGNE FREQUENCE (20 à 50Hz):</span><br>
    <input type="range" id="sliderF" min="20" max="50" step="0.01" value="20" oninput="document.getElementById('valF').innerText = this.value">
    <span id="valF">20</span> Hz
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
        let dateInitialisee = false;

        // Fonction de rafraichissement du statut
        function rafraichirStatut() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    // indices data : 0:ol, 1:m_s, 2:ds, 3:fm, 4:fs, 5:now, 6:cs
                    
                    // 1. Etat Contacteur
                    let contacteur = document.getElementById('contacteur_etat');
                    contacteur.innerText = data[6] ? "ON" : "OFF";
                    contacteur.style.color = data[6] ? "green" : "black";
                    contacteur.style.fontWeight = data[6] ? "bold" : "normal";

                    // 2. Etat VFD
                    let vfd = document.getElementById('vfd_etat');
                    vfd.innerText = data[0] ? "ON" : "OFF";
                    vfd.style.color = data[0] ? "green" : "black";
                    vfd.style.fontWeight = data[0] ? "bold" : "normal";

                    // 3. Etat Pompe (ON/OFF/?)
                    let pompe = document.getElementById('pompe_etat');
                    pompe.innerText = data[1];
                    if (data[1] === "ON") {
                        pompe.style.color = "green";
                        pompe.style.fontWeight = "bold";
                    } else {
                        pompe.style.color = "black";
                        pompe.style.fontWeight = "normal";
                    }

                    // 4. Defaut Disjoncteur
                    let defaut = document.getElementById('defaut_etat');
                    defaut.innerText = data[2] ? "DISJONCTION" : "NON";
                    defaut.style.color = data[2] ? "red" : "black";
                    defaut.style.fontWeight = data[2] ? "bold" : "normal";

                    // 5. Frequences (Securisées si string '?')
                    document.getElementById('freq_mesuree').innerText = (typeof data[3] === 'number') ? data[3].toFixed(2) : data[3];
                    document.getElementById('freq_consigne').innerText = (typeof data[4] === 'number') ? data[4].toFixed(2) : data[4];

                    // 6. Initialisation de la date courante à l'ouverture (une seule fois)
                    if (!dateInitialisee && data[5]) {
                        document.getElementById('sel_jj').value = data[5][2];
                        document.getElementById('sel_mm').value = data[5][1];
                        document.getElementById('sel_aaaa').value = data[5][0];
                        document.getElementById('sel_hh').value = data[5][4];
                        document.getElementById('sel_min').value = data[5][5];
                        document.getElementById('sel_ss').value = data[5][6];
                        dateInitialisee = true;
                    }
                })
                .catch(err => console.log("Erreur de rafraîchissement"));
        }

        // Remplissage initial des listes déroulantes
        function pop(id, min, max) {
            let s = document.getElementById(id);
            for(let i=min; i<=max; i++) {
                let v = i.toString().padStart(2, '0');
                s.options.add(new Option(v, i));
            }
        }
        pop('sel_jj', 1, 31); pop('sel_mm', 1, 12); pop('sel_aaaa', 2024, 2050);
        pop('sel_hh', 0, 23); pop('sel_min', 0, 59); pop('sel_ss', 0, 59);

        // Lancement immédiat puis toutes les 5 secondes
        rafraichirStatut();
        setInterval(rafraichirStatut, 5000);

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

        while await reader.readline() != b"\r\n":
            pass

        url = request_line.decode().split()[1] \
            if len(request_line.split()) > 1 else "/"

        if url == "/":
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + \
                PAGE_HTML
        elif url == "/status":
            response = \
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + \
                json.dumps(GetStatus())
        elif url.startswith("/action?"):
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
            elif cmd == 'con_on':
                global vfd
                vfd.CloseContactor()
                print("[Webserver] ACTION: Contacteur ON")
            elif cmd == 'con_off':
                global vfd
                vfd.OpenContactor()
                print("[Webserver] ACTION: Contacteur OFF")
            elif cmd == 'setf':
                val = float(param_dict.get('val', 20))
                SetF(val)
            elif cmd == 'rtc':
                j = int(param_dict.get('j', 1))
                m = int(param_dict.get('m', 1))
                a = int(param_dict.get('a', 2026))
                h = int(param_dict.get('h', 0))
                min_ = int(param_dict.get('min', 0))
                sec = int(param_dict.get('s', 0))
                
                rtc = machine.RTC()
                rtc.datetime((a, m, j, 0, h, min_, sec, 0))
                print("[Webserver] ACTION: RTC mis à jour:",
                    f"{j:02d}/{m:02d}/{a} {h:02d}:{min_:02d}:{sec:02d}")

            response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"

        writer.write(response.encode())
        await writer.drain()
    except Exception as e:
        print("[Webserver] Erreur client:", e)
    finally:
        await writer.wait_closed()


async def serveur_loop():
    """La boucle principale du serveur qui tourne en tâche de fond."""
    global serveur_actif
    print("[Webserver] Serveur Web démarré sur le port 80.")
    server = await asyncio.start_server(gerer_client, "0.0.0.0", 80)
    serveur_actif = True

    try:
        while serveur_actif:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        server.close()
        await server.wait_closed()
        print("[Webserver] Serveur Web stoppé.")


def demarrer_serveur(v):
    global ap, serveur_tache, serveur_actif, vfd

    vfd = v

    if serveur_actif:
        print("[Webserver] Le serveur tourne déjà.")
        return ap.ifconfig()[0]

    ap = network.WLAN(network.AP_IF)
    ap.config(ssid='PicoPiscine', password='laquinta')
    ap.active(True)
    while not ap.active():
        time.sleep(0.1)
    print(f"[Webserver] WiFi AP 'PicoPiscine' prêt. IP: {ap.ifconfig()[0]}")

    loop = asyncio.get_event_loop()
    serveur_tache = loop.create_task(serveur_loop())
    return ap.ifconfig()[0]


def stop_serveur():
    global ap, serveur_tache, serveur_actif

    if not serveur_actif:
        print("[Webserver] Le serveur n'est pas lancé.")
        return

    serveur_actif = False
    if serveur_tache:
        serveur_tache.cancel()

    if ap:
        ap.active(False)

    print("[Webserver] Demande d'arrêt envoyée.")
