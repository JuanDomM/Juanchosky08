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

# Función para mover el servomotor
def set_servo(angle):
    duty = int((angle / 180) * (102 - 26) + 26)  # Ajuste de conversión
    servo.duty(duty)
    print(f"Servo movido a {angle} grados")

# Función para medir la distancia con el sensor ultrasónico
def get_distance():
    trigger.off()
    time.sleep_us(2)
    trigger.on()
    time.sleep_us(10)
    trigger.off()

    start = time.ticks_us()
    timeout = start + 30000  # Timeout de 30ms para evitar bloqueos

    while echo.value() == 0:
        if time.ticks_us() > timeout:
            print("Timeout esperando eco")
            return float('inf')
    start = time.ticks_us()

    while echo.value() == 1:
        if time.ticks_us() > timeout:
            print("Timeout esperando final del eco")
            return float('inf')
    end = time.ticks_us()

    duration = end - start
    distance = (duration * 0.0343) / 2
    print(f"Distancia medida: {distance:.2f} cm")
    return distance if distance <= 30 else float('inf')

# Variable para habilitar/deshabilitar el monitoreo del sensor
active_monitoring = True  

# Bucle de monitoreo del sensor ultrasónico
def sensor_loop():
    global active_monitoring
    while True:
        if active_monitoring:
            distance = get_distance()
            if distance <= 20:
                set_servo(140)
            else:
                set_servo(0)
        time.sleep(5)  # Medición cada 5 segundos

# Iniciar la medición en un segundo hilo
_thread.start_new_thread(sensor_loop, ())

# Página web para control del servo y el sensor
def web_page():
    html = """<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ESP32 Web Server</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }
            .container { width: 80%%; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px #ccc; }
            h1 { color: #333; }
            img { width: 300px; height: auto; }
            .section { margin-bottom: 20px; padding: 15px; background: #e8e8e8; border-radius: 5px; }
            .button { padding: 10px 20px; margin: 5px; font-size: 16px; border: none; cursor: pointer; border-radius: 5px; }
            .open { background: green; color: white; }
            .close { background: red; color: white; }
            .on { background: blue; color: white; }
            .off { background: gray; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Caneca de basura inteligente</h1>

            <div class="section">
                <h2>Introducción</h2>
                <img src="https://github.com/JuanDomM/Juanchosky08/blob/main/fotomontaje.jpeg?raw=true" alt="Imagen del Proyecto">
                <p>En la actualidad hay un problema mundial con los desechos para ello una buena opción para tener en nuestra casa son las canecas inteligentes, diseñadas para optimizar la gestión de residuos mediante tecnologías como sensores, conectividad IoT y automatización.
En concreto esta caneca tiene la funcionalidad de detectar los objetos cercanos a ella mediante un sensor ultrasónico, y así poder abrir y cerrar la tapa cuando se detecte el objeto. Además, desde la interfaz web se puede manipular la tapa de esta caneca, con la funcionalidad de desactivar el monitoreo del sensor o abrir y cerrar la tapa mediante botones. 
</p>
            </div>

            <div class="section">
                <h2>Descripción</h2>
                <p>Todavía no se ha generado la cultura de el reciclaje, las personas desechan los objetos en cualquier parte sin saber a que tipo de residuo pertenece. 
Para esto una buena opción seria que las propias canecas de basura se encargaran de ello, o que pueda de alguna manera detectar el objeto y indicarle al sujeto en que parte debe ir, esto sería una solución a futuro para poder reducir la mala separación de desechos. 
</p>
            </div>

            <div class="section">
                <h2>Objetivos</h2>
                <p> El objetivo de este proyecto es diseñar una caneca inteligente que mediante un sensor detecte que tan cerca esta el residuo y pueda abrir y cerrar la tapa para su desecho, además de poder controlar remotamente en que momento se desea detectar el residuo o directamente abrir la tapa.  En un futuro se rediseñará esta caneca para que pueda detectar el tipo de residuo y así que se pueda poner en el lugar indicado.</p>
                <ul>
                    <li>Medir distancias con el sensor ultrasónico.</li>
                    <li>Activar el servomotor cuando un objeto esté cerca.</li>
                    <li>Permitir control manual desde una interfaz web.</li>
                </ul>
            </div>

            <div class="section">
                <h2>Control de la tapa</h2>
                <a href="/angle?value=0"><button class="button close">Cerrar </button></a>
                <a href="/angle?value=140"><button class="button open">Abrir </button></a>
            </div>

            <div class="section">
                <h2>Control de detección automática  </h2>
                <a href="/monitor?state=on"><button class="button on">Activar Sensor</button></a>
                <a href="/monitor?state=off"><button class="button off">Desactivar Sensor</button></a>
            </div>
        </div>
    </body>
    </html>
    """
    return html
# Configuración del servidor web
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print("Servidor Web Iniciado")

while True:
    try:
        conn, addr = s.accept()
        print("Conexión desde", addr)
        request = conn.recv(1024).decode()
        print(request)

        if '/angle?value=' in request:
            try:
                angle = int(request.split('/angle?value=')[1].split()[0])
                angle = max(0, min(180, angle))  # Limitar el ángulo entre 0 y 180 grados
                set_servo(angle)
            except ValueError:
                print("Valor inválido recibido")

        if '/monitor?state=' in request:
            state = request.split('/monitor?state=')[1].split()[0]
            active_monitoring = (state == 'on')
            print(f"Monitoreo del sensor: {'Activado' if active_monitoring else 'Desactivado'}")

        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()

    except Exception as e:
        print(f"Error en el servidor: {e}")
