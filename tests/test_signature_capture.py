import unittest
import os
from unittest.mock import Mock, patch
from src.signature_capture.signature_capture import SerialConnection, SignatureProcessor, SignatureCapture
from PIL import Image

class TestSerialConnection(unittest.TestCase):
    def setUp(self):
        """Configura un objeto SerialConnection para cada prueba."""
        self.serial_conn = SerialConnection(port="COM8", baud_rate=115200)

    @patch("serial.Serial")
    def test_connect_success(self, mock_serial):
        """Prueba que connect() devuelve True cuando la conexión serial es exitosa."""
        mock_serial.return_value = Mock()
        result = self.serial_conn.connect()
        self.assertTrue(result)
        mock_serial.assert_called_once_with("COM8", 115200, timeout=1)

    @patch("serial.Serial")
    def test_connect_failure(self, mock_serial):
        """Prueba que connect() maneja correctamente un fallo de conexión."""
        mock_serial.side_effect = Exception("Error de conexión")
        result = self.serial_conn.connect()
        self.assertFalse(result)

    def test_close_without_connection(self):
        """Prueba que close() no falla si no hay conexión."""
        self.serial_conn.close()  # No debería lanzar excepción

class TestSignatureProcessor(unittest.TestCase):
    def setUp(self):
        """Configura un objeto SignatureProcessor para cada prueba."""
        self.processor = SignatureProcessor(save_folder="test_firmas")

    def tearDown(self):
        """Elimina la carpeta de prueba después de cada prueba."""
        if os.path.exists("test_firmas"):
            for file in os.listdir("test_firmas"):
                os.remove(os.path.join("test_firmas", file))
            os.rmdir("test_firmas")

    def test_ensure_folder_exists(self):
        """Prueba que la carpeta de guardado se crea si no existe."""
        self.assertTrue(os.path.exists("test_firmas"))

    @patch("PIL.Image.new")
    @patch("PIL.Image.Image.save")
    def test_process_pixel_data(self, mock_save, mock_image):
        """Prueba que process_pixel_data procesa y guarda la imagen correctamente."""
        mock_image.return_value = Mock(spec=Image.Image)
        pixel_data = [(0, 0, 0xF800)]  # Ejemplo de datos de píxeles (color rojo)
        self.processor.process_pixel_data(width=1, height=1, pixel_data=pixel_data, serial_number="TEST123")
        mock_save.assert_called_once()
        self.assertTrue(os.path.exists(os.path.join("test_firmas", "firma_TEST123_*.png")))

class TestSignatureCapture(unittest.TestCase):
    def setUp(self):
        """Configura un objeto SignatureCapture para cada prueba."""
        self.capture = SignatureCapture(port="COM8", baud_rate=115200, save_folder="test_firmas")

    def tearDown(self):
        """Elimina la carpeta de prueba después de cada prueba."""
        if os.path.exists("test_firmas"):
            for file in os.listdir("test_firmas"):
                os.remove(os.path.join("test_firmas", file))
            os.rmdir("test_firmas")

    @patch.object(SerialConnection, "connect")
    @patch.object(SerialConnection, "send_command")
    @patch.object(SerialConnection, "read_line")
    def test_capture_signature_interactive(self, mock_read_line, mock_send_command, mock_connect):
        """Prueba la captura interactiva con entrada simulada."""
        mock_connect.return_value = True
        mock_read_line.side_effect = [
            "START_SAVING:TEST123",
            "DIM:1,1",
            "0,0,F800",
            "END_SAVING"
        ]
        mock_send_command.return_value = None
        # Simular entrada de usuario (esto requiere un patch de input)
        with patch("builtins.input", side_effect=["", "salir"]):
            self.capture.capture_signature(interactive=True)
        mock_connect.assert_called_once()
        mock_send_command.assert_called()

    @patch.object(SerialConnection, "connect")
    @patch.object(SerialConnection, "send_command")
    @patch.object(SerialConnection, "read_line")
    def test_capture_signature_non_interactive(self, mock_read_line, mock_send_command, mock_connect):
        """Prueba la captura no interactiva."""
        mock_connect.return_value = True
        mock_read_line.side_effect = [
            "START_SAVING:TEST123",
            "DIM:1,1",
            "0,0,F800",
            "END_SAVING"
        ]
        mock_send_command.return_value = None
        self.capture.capture_signature(interactive=False)
        mock_connect.assert_called_once()
        mock_send_command.assert_called()

if __name__ == "__main__":
    unittest.main()