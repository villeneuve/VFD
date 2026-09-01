import subprocess
import json
import ast
import sys
import paho.mqtt.client as mqtt

BROKER = "localhost"
TOPIC = "LaQuinta/poolbox/"

KEYS = [
    "vfd_status", "Running_frequency", "Set_frequency", "Bus_voltage",
    "Output_voltage", "Output_current", "Output_power", "Output_torque",
    "Load_speed", "Feedback_frequency", "Power_on_time", "Running_time",
    "VFD_temperature", "Motor_status", "Contactor_status", "Disjoncteur_status",
    "Fan_duty_u16", "Temperature_PicoBox", "crc_err_PicoBox", "other_err_PicoBox",
    "Temperature_Motor", "crc_err_Motor", "other_err_Motor", "Temperature_Eau",
    "crc_err_Eau", "other_err_Eau", "Total_access_to_each_sensor"
]

def parse_value(val):
    if val == 'online':
        return 1
    elif val == 'offline':
        return 0
    # Modif guy ne pas renvoyer "None" qui donne un "null" en json
    # car fuxa affichera la derniere valeur connue. On garde le "?".
    #  elif val == '?':
    #      return None
    
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val

def main():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()

    try:
        client.connect(BROKER, 1883, 60)
        client.loop_start()
        print(f"Connecté au broker {BROKER}. En attente des données de systemd...")
        sys.stdout.flush()
    except Exception as e:
        print(f"Erreur de connexion MQTT : {e}")
        return

    # stdbuf -oL force journalctl à vider son flux ligne par ligne immédiatement
    # Utilisation de -t (syslog tag) au lieu de -u (unit name)
    cmd = ["stdbuf", "-oL", "journalctl", "-t", "vfd-uart", "-f", "-n", "0", "--no-pager"]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        for line in iter(process.stdout.readline, ''):
            if "Data: [" in line:
                try:
                    list_str = line.split("Data: ")[1].strip()
                    data_list = ast.literal_eval(list_str)
                    
                    if len(data_list) == len(KEYS):
                        processed_data = [parse_value(v) for v in data_list]
                        payload = dict(zip(KEYS, processed_data))
                        json_payload = json.dumps(payload)
                        
                        client.publish(TOPIC, json_payload)
                        print(f"Trame publiée : {json_payload}")
                        sys.stdout.flush()
                    else:
                        print(f"Alerte : Nombre de valeurs reçu ({len(data_list)}) au lieu de {len(KEYS)}.")
                        sys.stdout.flush()
                        
                except Exception as e:
                    print(f"Erreur de traitement : {e}")
                    sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur.")
    finally:
        process.terminate()
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
