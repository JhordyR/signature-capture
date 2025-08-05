import serial
from PIL import Image, ImageFilter
import datetime
import os

class SerialConnection:
    """Clase para manejar la conexión serial con el Arduino."""
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None

    def connect(self):
        """Establece la conexión serial."""
        try:
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Conexión establecida en {self.port} a {self.baud_rate} baudios.")
            return True
        except serial.SerialException as e:
            print(f"Error: No se pudo conectar a {self.port}. Verifica que el Microcontrolador esté conectado y el puerto sea correcto.")
            print(e)
            self.serial = None  # Asegurar que self.serial sea None en caso de fallo
            return False

    def send_command(self, command):
        """Envía un comando al Arduino."""
        if self.serial and self.serial.is_open:
            self.serial.write(command.encode())
            print("Enviando orden de captura...")

    def read_line(self):
        """Lee una línea desde el puerto serial."""
        if self.serial and self.serial.is_open:
            return self.serial.readline().decode().strip()
        return ""

    def close(self):
        """Cierra la conexión serial."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("Puerto serial cerrado.")
            self.serial = None

class SignatureProcessor:
    """Clase para procesar y guardar la firma como imagen."""
    def __init__(self, save_folder="firmas"):
        self.save_folder = save_folder
        self._ensure_folder_exists()

    def _ensure_folder_exists(self):
        """Crea la carpeta de guardado si no existe."""
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

    def process_pixel_data(self, width, height, pixel_data, serial_number):
        """Procesa los datos de píxeles y guarda la imagen."""
        if not pixel_data or width <= 0 or height <= 0:
            print("Datos de píxeles inválidos.")
            return
        img = Image.new('RGB', (width, height), "black")
        pixels = img.load()

        for x, y, color in pixel_data:
            if 0 <= x < width and 0 <= y < height:
                r = ((color >> 11) & 0x1F) * 255 // 31
                g = ((color >> 5) & 0x3F) * 255 // 63
                b = (color & 0x1F) * 255 // 31
                pixels[x, y] = (r, g, b)

        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        scaled_img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        self._save_image(scaled_img, serial_number)

    def _save_image(self, image, serial_number):
        """Guarda la imagen con un nombre basado en el número de serie y la fecha."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_folder, f"firma_{serial_number}_{timestamp}.png")
        image.save(filename)
        print(f"Firma guardada en: {filename}")

class SignatureCapture:
    """Clase principal para coordinar la captura de firmas."""
    def __init__(self, port='COM8', baud_rate=115200, save_folder="firmas"):
        self.serial_conn = SerialConnection(port, baud_rate)
        self.signature_processor = SignatureProcessor(save_folder)

    def capture_signature(self, interactive=True):
        """Captura una firma desde el Arduino y la procesa."""
        if not self.serial_conn.connect():
            return

        try:
            while True:
                if interactive:
                    user_input = input("Presiona Enter para capturar una firma (o 'salir' para terminar): ")
                    if user_input.lower() == "salir":
                        break
                else:
                    self.serial_conn.send_command("CAPTURE_SIGNATURE\n")
                    self._capture_once()
                    break

                self.serial_conn.send_command("CAPTURE_SIGNATURE\n")
                self._capture_once()

        except KeyboardInterrupt:
            print("Programa detenido por el usuario.")
        finally:
            self.serial_conn.close()

    def _capture_once(self):
        """Captura una única firma."""
        capturing = False
        pixel_data = []
        width = 0
        height = 0
        serial_number = ""

        while True:
            line = self.serial_conn.read_line()
            if line:
                if line.startswith("START_SAVING:"):
                    capturing = True
                    pixel_data = []
                    serial_number = line.replace("START_SAVING:", "")
                    print(f"Capturando firma con serial: {serial_number}")
                elif line == "END_SAVING" and capturing:
                    capturing = False
                    if width > 0 and height > 0 and pixel_data:
                        self.signature_processor.process_pixel_data(width, height, pixel_data, serial_number)
                    pixel_data = []
                    break
                elif capturing:
                    if line.startswith("DIM:"):
                        dims = line[4:].split(",")
                        width = int(dims[0])
                        height = int(dims[1])
                    else:
                        parts = line.split(",")
                        if len(parts) == 3:
                            x = int(parts[0])
                            y = int(parts[1])
                            color = int(parts[2], 16)
                            pixel_data.append((x, y, color))