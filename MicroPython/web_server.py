import network
import socket
import machine
import time
import json
import asyncio
import gc
import common

# --- VARIABLES GLOBALES DE CONTRÔLE ---
ap = None
serveur_tache = None  
serveur_actif = False
vfd = None


def unquote(string):
    """Décode les caractères %XX d'une URL."""
    parts = string.split('%')
    res = parts[0]
    for part in parts[1:]:
        try:
            res += chr(int(part[:2], 16)) + part[2:]
        except Exception:
            res += '%' + part
    return res


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
# PAGES WEB HTML / JAVASCRIPT
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

PAGE_PROG_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Programme Journalier - Pico Piscine</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .titre { font-weight: bold; color: black; }
        .bouton { padding: 10px 15px; margin: 5px; cursor: pointer; }
        .explications {
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin-bottom: 20px;
            white-space: pre-wrap;
            font-size: 14px;
        }
        .ligne-prog {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            background: #f1f1f1;
            padding: 8px 12px;
            border-radius: 5px;
            flex-wrap: wrap;
        }
        .bouton-poubelle {
            background: none;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 18px;
            cursor: pointer;
            padding: 4px 8px;
        }
        .bouton-poubelle:hover {
            background-color: #ffdddd;
            border-color: red;
        }
        .bouton-plus {
            font-size: 24px;
            font-weight: bold;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background-color: #28a745;
            color: white;
            border: none;
            cursor: pointer;
            margin: 10px 0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .bouton-plus:hover {
            background-color: #218838;
        }
        hr { margin: 20px 0; }
    </style>
</head>
<body>
    <h2>Édition du Programme Journalier</h2>
    
    <button class="bouton" onclick="window.location.href='/'">Retour au contrôle</button>

    <hr>

    <div class="explications">Sur cette page tu peux modifier le programme journalier. 
Il sera pris en compte immediatement et à la prochaine heure correspondante l'action sera executée.
Mettre la fréquence à 0 est un ordre de STOP: arret moteur, puis apres 10 minutes ouverture contacteur.
La frequence est reglable de 20 a 50Hz seulement:
Si le VFD est online la frequence est immédiatement prise en compte.
Si le VFD est offline il y aura la sequence de demarrage suivante:
Fermeture contacteur immediate, attente 1 minute, 
Reglage frequence à 45Hz, attente 1 minute
Démarrage moteur, attente 5 minutes (5mn a 45Hz pour amorcage pompe)
Reglage frequence à valeur demandée. fin</div>

    <hr>

    <div id="zone_edition">
        <h3>Programme journalier :</h3>
        <div id="lignes_prog"></div>
        <div>
            <button class="bouton-plus" onclick="ajouterLigne()" title="Ajouter une ligne">+</button>
        </div>
        <br>
        <button class="bouton" style="background-color: #007bff; color: white; border: none; font-size: 16px;" onclick="enregistrerProgr()">Enregistrer</button>
        <span id="msg_statut" style="margin-left: 10px; font-weight: bold;"></span>
    </div>

    <script>
        const initialProgr = {{PROGR_DATA}};

        function creermenu(select, min, max) {
            for (let i = min; i <= max; i++) {
                let opt = document.createElement('option');
                opt.value = i;
                opt.textContent = String(i).padStart(2, '0');
                select.appendChild(opt);
            }
        }

        function creerMenuFreq(select) {
            let opt0 = document.createElement('option');
            opt0.value = 0;
            opt0.textContent = "0 (STOP)";
            select.appendChild(opt0);
            for (let i = 20; i <= 50; i++) {
                let opt = document.createElement('option');
                opt.value = i;
                opt.textContent = i + " Hz";
                select.appendChild(opt);
            }
        }

        function ajouterLigne(h = 0, m = 0, f = 0) {
            const container = document.getElementById('lignes_prog');
            const div = document.createElement('div');
            div.className = 'ligne-prog';

            div.innerHTML = `
                <span>Heures :</span>
                <select class="sel_h"></select>
                <span>Minutes :</span>
                <select class="sel_m"></select>
                <span>Fréquence :</span>
                <select class="sel_f"></select>
                <button class="bouton-poubelle" type="button" onclick="supprimerLigne(this)" title="Supprimer la ligne">🗑️</button>
            `;

            const selH = div.querySelector('.sel_h');
            const selM = div.querySelector('.sel_m');
            const selF = div.querySelector('.sel_f');

            creermenu(selH, 0, 23);
            creermenu(selM, 0, 59);
            creerMenuFreq(selF);

            selH.value = h;
            selM.value = m;
            selF.value = f;

            container.appendChild(div);
        }

        function supprimerLigne(btn) {
            btn.parentElement.remove();
        }

        function initialiserPage() {
            if (Array.isArray(initialProgr)) {
                initialProgr.forEach(triplet => {
                    ajouterLigne(triplet[0], triplet[1], triplet[2]);
                });
            }
        }

        function enregistrerProgr() {
            const lignes = document.querySelectorAll('.ligne-prog');
            let progr = [];
            lignes.forEach(ligne => {
                let h = parseInt(ligne.querySelector('.sel_h').value, 10);
                let m = parseInt(ligne.querySelector('.sel_m').value, 10);
                let f = parseInt(ligne.querySelector('.sel_f').value, 10);
                progr.push([h, m, f]);
            });

            const msg = document.getElementById('msg_statut');
            msg.style.color = 'black';
            msg.innerText = "Enregistrement en cours...";

            fetch('/save_prog?data=' + encodeURIComponent(JSON.stringify(progr)))
                .then(response => response.text())
                .then(res => {
                    if (res === 'OK') {
                        msg.style.color = 'green';
                        msg.innerText = "Enregistré avec succès !";
                    } else {
                        msg.style.color = 'red';
                        msg.innerText = "Erreur lors de l'enregistrement.";
                    }
                })
                .catch(err => {
                    msg.style.color = 'red';
                    msg.innerText = "Erreur réseau.";
                });
        }

        initialiserPage();
    </script>
</body>
</html>
"""

# Découpage et conversion unique en bytes pour économiser la RAM
_part1, _part2 = PAGE_PROG_HTML.split("{{PROGR_DATA}}")
PAGE_PROG_BYTES_1 = _part1.encode('utf-8')
PAGE_PROG_BYTES_2 = _part2.encode('utf-8')
PAGE_HTML_BYTES = PAGE_HTML.encode('utf-8')

# Libération immédiate des temporaires
del _part1, _part2, PAGE_HTML, PAGE_PROG_HTML
gc.collect()

# ==========================================
# LOGIQUE DU SERVEUR (ASYNCHRONE)
# ==========================================
async def gerer_client(reader, writer):
    """Gère une connexion client de manière économe en mémoire RAM."""
    gc.collect()  # Libère la mémoire inutilisée dès le début de la requête
    
    try:
        request_line = await reader.readline()
        if not request_line:
            return

        while await reader.readline() != b"\r\n":
            pass

        url = request_line.decode().split()[1] \
            if len(request_line.split()) > 1 else "/"

        if url == "/":
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            writer.write(PAGE_HTML_BYTES)
            await writer.drain()

        elif url == "/prog":
            # Envoi par morceaux (stream) : AUCUNE création de grosse chaîne en mémoire
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            writer.write(PAGE_PROG_BYTES_1)
            writer.write(json.dumps(common.progr).encode('utf-8'))
            writer.write(PAGE_PROG_BYTES_2)
            await writer.drain()

        elif url.startswith("/save_prog?"):
            try:
                raw_params = url.split("?", 1)[1]
                params_dict = {}
                for couple in raw_params.split("&"):
                    if "=" in couple:
                        k, v = couple.split("=", 1)
                        params_dict[k] = v
                
                data_str = unquote(params_dict.get("data", "[]"))
                data = json.loads(data_str)
                
                new_progr = []
                for item in data:
                    if len(item) == 3:
                        h = int(item[0])
                        m = int(item[1])
                        f = int(item[2])
                        if 0 <= h <= 23 and 0 <= m <= 59 and (f == 0 or 20 <= f <= 50):
                            new_progr.append((h, m, f))
                
                if common.progr != new_progr:
                    common.progr = new_progr
                    print("[Webserver] ACTION: Programme journalier mis à jour :", common.progr)
                else:
                    print("[Webserver] ACTION: Programme journalier inchangé.")
                
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
                await writer.drain()
            except Exception as e:
                print("[Webserver] Erreur enregistrement programme :", e)
                writer.write(b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nERR")
                await writer.drain()

        elif url == "/status":
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            writer.write(json.dumps(GetStatus()).encode('utf-8'))
            await writer.drain()

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
                common.time_has_changed = True

            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
            await writer.drain()
        else:
            writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
            await writer.drain()

    except Exception as e:
        print("[Webserver] Erreur client:", e)
    finally:
        await writer.wait_closed()
        gc.collect()  # Nettoyage systématique après la fermeture du socket




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
