import argparse
import json
from signature_capture import SignatureCapture

def main():
    parser = argparse.ArgumentParser(description="Captura firmas desde Arduino")
    parser.add_argument('--port', type=str, default='COM8', help='Puerto serial')
    parser.add_argument('--baud_rate', type=int, default=115200, help='Baud rate')
    parser.add_argument('--save_folder', type=str, default='firmas', help='Carpeta de guardado')
    parser.add_argument('--interactive', type=str, default='true', help='Modo interactivo (true/false)')
    parser.add_argument('--default_width', type=int, default=100, help='Ancho predeterminado')
    parser.add_argument('--default_height', type=int, default=100, help='Alto predeterminado')
    args = parser.parse_args()

    interactive = args.interactive.lower() == 'true'

    try:
        capture = SignatureCapture(
            port=args.port,
            baud_rate=args.baud_rate,
            save_folder=args.save_folder,
            default_width=args.default_width,
            default_height=args.default_height
        )
        capture.capture_signature(interactive=interactive)
        print(json.dumps({"status": "success", "message": "Captura completada"}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        raise

if __name__ == "__main__":
    main()