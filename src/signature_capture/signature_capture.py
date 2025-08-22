import serial
from PIL import Image, ImageFilter
import datetime
import os
import time

class SignatureCaptureError(Exception):
    """Excepción base para errores en la captura de firmas."""
    pass

class SerialConnectionError(SignatureCaptureError):
    """Error en la conexión serial."""
    pass

class InvalidDataError(SignatureCaptureError):
    """Error en los datos recibidos."""
    pass

class EmptySignatureError(SignatureCaptureError):
    """Firma vacía detectada."""
    pass

class SaveImageError(SignatureCaptureError):
    """Error al guardar la imagen."""
    pass

class TimeoutError(SignatureCaptureError):
    """Timeout en la lectura de datos."""
    pass

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
            raise SerialConnectionError(f"Error: No se pudo conectar a {self.port}. Verifica que el Microcontrolador esté conectado, el puerto sea correcto y no esté en uso por otra aplicación. Detalles: {str(e)}")

    def send_command(self, command):
        """Envía un comando al Arduino."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(command.encode())
                print("Enviando orden de captura...")
            except serial.SerialException as e:
                raise SerialConnectionError(f"Error al enviar comando: {str(e)}")
        else:
            raise SerialConnectionError("No hay conexión serial establecida.")

    def read_line(self, timeout=5):
        """Lee una línea desde el puerto serial con timeout."""
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout al leer datos del serial.")
            if self.serial and self.serial.is_open:
                try:
                    line = self.serial.readline().decode().strip()
                    if line:
                        return line
                except serial.SerialException as e:
                    raise SerialConnectionError(f"Error al leer línea: {str(e)}")
            else:
                raise SerialConnectionError("No hay conexión serial establecida.")

    def close(self):
        """Cierra la conexión serial."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
                print("Puerto serial cerrado.")
            except serial.SerialException as e:
                raise SerialConnectionError(f"Error al cerrar el puerto: {str(e)}")
            finally:
                self.serial = None

class SignatureProcessor:
    """Clase para procesar y guardar la firma como imagen."""
    def __init__(self, save_folder="firmas"):
        self.save_folder = save_folder
        self._ensure_folder_exists()

    def _ensure_folder_exists(self):
        """Crea la carpeta de guardado si no existe."""
        try:
            if not os.path.exists(self.save_folder):
                os.makedirs(self.save_folder)
        except OSError as e:
            raise SaveImageError(f"Error al crear la carpeta de guardado '{self.save_folder}': {str(e)}")

    def process_pixel_data(self, width, height, pixel_data, serial_number):
        """Procesa los datos de píxeles y guarda la imagen."""
        if not pixel_data or width <= 0 or height <= 0:
            raise InvalidDataError("Datos de píxeles inválidos: ancho, alto o datos vacíos.")
        
        img = Image.new('RGB', (width, height), "black")
        pixels = img.load()

        non_black_pixels = 0
        for x, y, color in pixel_data:
            if 0 <= x < width and 0 <= y < height:
                r = ((color >> 11) & 0x1F) * 255 // 31
                g = ((color >> 5) & 0x3F) * 255 // 63
                b = (color & 0x1F) * 255 // 31
                pixels[x, y] = (r, g, b)
                if (r, g, b) != (0, 0, 0):
                    non_black_pixels += 1
            else:
                raise InvalidDataError(f"Píxel fuera de rango: x={x}, y={y} con ancho={width}, alto={height}")

        if non_black_pixels == 0:
            raise EmptySignatureError("Firma vacía detectada: todos los píxeles son negros.")

        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        scaled_img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        try:
            self._save_image(scaled_img, serial_number)
        except SaveImageError as e:
            raise SaveImageError(f"Error al guardar la imagen: {str(e)}")

    def _save_image(self, image, serial_number):
        """Guarda la imagen con un nombre basado en el número de serie y la fecha."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_folder, f"firma_{serial_number}_{timestamp}.png")
        try:
            image.save(filename)
            print(f"Firma guardada en: {filename}")
        except OSError as e:
            raise SaveImageError(f"Error al guardar la imagen en '{filename}': {str(e)}. Verifica permisos de escritura en la carpeta.")

class SignatureCapture:
    """Clase principal para coordinar la captura de firmas."""
    def __init__(self, port='COM8', baud_rate=115200, save_folder="firmas", default_width=100, default_height=100):
        self.serial_conn = SerialConnection(port, baud_rate)
        self.signature_processor = SignatureProcessor(save_folder)
        self.default_width = default_width
        self.default_height = default_height

    def capture_signature(self, interactive=True):
        """Captura una firma desde el Arduino y la procesa."""
        try:
            if not self.serial_conn.connect():
                raise SerialConnectionError("No se pudo establecer la conexión serial.")
        except SerialConnectionError as e:
            print(str(e))
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

        except TimeoutError as e:
            print(f"Timeout durante la captura: {str(e)}")
        except InvalidDataError as e:
            print(f"Datos inválidos recibidos: {str(e)}")
        except EmptySignatureError as e:
            print(f"Firma vacía: {str(e)}")
        except KeyboardInterrupt:
            print("Programa detenido por el usuario.")
        except Exception as e:
            print(f"Error inesperado durante la captura: {str(e)}")
        finally:
            try:
                self.serial_conn.close()
            except SerialConnectionError as e:
                print(f"Error al cerrar la conexión: {str(e)}")

    def _capture_once(self):
        """Captura una única firma."""
        capturing = False
        pixel_data = []
        width = self.default_width
        height = self.default_height
        serial_number = ""

        try:
            while True:
                line = self.serial_conn.read_line(timeout=10)  # Timeout de 10 segundos por línea
                if line:
                    if line.startswith("START_SAVING:"):
                        capturing = True
                        pixel_data = []
                        serial_number = line.replace("START_SAVING:", "")
                        if not serial_number:
                            raise InvalidDataError("Número de serie vacío recibido.")
                        print(f"Capturando firma con serial: {serial_number}")
                    elif line == "END_SAVING" and capturing:
                        capturing = False
                        if width <= 0 or height <= 0:
                            raise InvalidDataError("Dimensiones inválidas: ancho o alto <= 0.")
                        if not pixel_data:
                            raise EmptySignatureError("No se recibieron datos de píxeles.")
                        self.signature_processor.process_pixel_data(width, height, pixel_data, serial_number)
                        pixel_data = []
                        break
                    elif capturing:
                        if line.startswith("DIM:"):
                            dims = line[4:].split(",")
                            if len(dims) != 2:
                                raise InvalidDataError("Formato de dimensiones inválido.")
                            try:
                                width = int(dims[0])
                                height = int(dims[1])
                                if width <= 0 or height <= 0:
                                    raise InvalidDataError("Dimensiones negativas o cero.")
                            except ValueError:
                                raise InvalidDataError("Valores de dimensiones no numéricos.")
                        else:
                            parts = line.split(",")
                            if len(parts) != 3:
                                raise InvalidDataError("Formato de píxel inválido.")
                            try:
                                x = int(parts[0])
                                y = int(parts[1])
                                color = int(parts[2], 16)
                            except ValueError:
                                raise InvalidDataError("Valores de píxel no válidos (no numéricos o hexadecimal inválido).")
                            pixel_data.append((x, y, color))
                else:
                    raise TimeoutError("No se recibió respuesta del microcontrolador después de enviar el comando.")
        except TimeoutError as e:
            raise TimeoutError(f"Timeout durante la captura individual: {str(e)}")
        except InvalidDataError as e:
            raise InvalidDataError(f"Error en datos durante la captura individual: {str(e)}")