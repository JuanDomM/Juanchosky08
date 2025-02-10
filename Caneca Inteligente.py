import network
import socket
import machine
import time
import _thread

# Configuración del servomotor
servo = machine.PWM(machine.Pin(14), freq=50)
servo.duty(26)  # Inicializar en 0°

# Configuración del sensor ultrasónico
trigger = machine.Pin(13, machine.Pin.OUT)
echo = machine.Pin(12, machine.Pin.IN)

# Conectar a la red WiFi
SSID = "POCO"
PASSWORD = "JUANCHO.O"

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(SSID, PASSWORD)

while not station.isconnected():
    pass

print("Conectado a WiFi")
print("Dirección IP:", station.ifconfig()[0])

def set_servo(angle):
    duty = int((angle / 180) * 102 + 26)  # Conversión de ángulo a ciclo de trabajo
    servo.duty(duty)
    print(f"Servo movido a {angle} grados")

def get_distance():
    trigger.off()
    time.sleep_us(2)
    trigger.on()
    time.sleep_us(10)
    trigger.off()
    
    start = time.ticks_us()
    timeout = start + 30000  # Timeout de 30ms para evitar bucles infinitos
    
    while echo.value() == 0:
        if time.ticks_us() > timeout:
            return None  # No se detectó señal de eco
    start = time.ticks_us()
    
    while echo.value() == 1:
        if time.ticks_us() > timeout:
            return None  # No se detectó señal de eco
    end = time.ticks_us()
    
    duration = end - start
    distance = (duration * 0.0343) / 2
    print(f"Distancia medida: {distance:.2f} cm")
    return distance if distance <= 30 else None  # Limitar la distancia máxima a 30 cm

def sensor_loop():
    while True:
        distance = get_distance()
        if distance is not None and distance <= 20:
            set_servo(90)  # Si detecta un objeto a 20 cm o menos, mueve el servo a 90°
        else:
            set_servo(0)  # Si no detecta o está más lejos, deja el servo en 0°
        time.sleep(5)  # Medir cada 5 segundoS

# Iniciar la medición en un segundo hilo
_thread.start_new_thread(sensor_loop, ())

def web_page():
    html = """
    <html>
    <head>
        <title>ESP32 Web Server</title>
    </head>
    <body>
        <h1>ESP32 Web Server</h1>
        <p>Control de Servomotor</p>
        <a href="/angle?value=0"><button>CERRAR</button></a>
        <a href="/angle?value=90"><button>ABRIR</button></a>
    </body>
    </html>
    """
    return html

# Configuración del socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

while True:
    conn, addr = s.accept()
    print("Conexión desde", addr)
    request = conn.recv(1024).decode()
    print(request)
    
    if '/angle?value=' in request:
        try:
            angle = int(request.split('/angle?value=')[1].split()[0])
            angle = max(0, min(90, angle))  # Limitar el ángulo entre 0 y 90 grados
            set_servo(angle)
        except:
            pass
    
    response = web_page()
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    conn.close()
