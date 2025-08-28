import serial
import time

def read_arduino_data():
    # Configuración del puerto serial
    port = '/dev/ttyACM0'
    baudrate = 500000
    
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            print(f"Conectado a {port} a {baudrate} bps")
            print("Esperando datos... (Presiona Ctrl+C para salir)")
            
            while True:
                # Esperar el carácter de inicio '@'
                start_byte = ser.read()
                if not start_byte:
                    continue
                    
                if start_byte == b'@':
                    # Leer los 4 bytes siguientes (PINA, PINK, PINF, PINE, PINH)
                    data = ser.read(5)
                    if len(data) == 5:
                        pina, pink, pinf, pine, pinh = data
                        
                        # Mostrar los valores en formato hexadecimal y decimal
                        print("\n--- Datos Recibidos ---")
                        print(f"Carácter de inicio: @ (0x40)")
                        print(f"PINA: 0x{pina:02X} | {pina} (decimal) | {bin(pina)[2:]:>08} (binario)")
                        print(f"PINK: 0x{pink:02X} | {pink} (decimal) | {bin(pink)[2:]:>08} (binario)")
                        print(f"PINF: 0x{pinf:02X} | {pinf} (decimal) | {bin(pinf)[2:]:>08} (binario)")
                        print(f"PINE: 0x{pine:02X} | {pine} (decimal) | {bin(pine)[2:]:>08} (binario)")
                        print(f"PINH: 0x{pinh:02X} | {pinh} (decimal) | {bin(pinh)[2:]:>08} (binario)")
                        print("-----------------------")
                        
    except serial.SerialException as e:
        print(f"Error de puerto serial: {e}")
    except KeyboardInterrupt:
        print("\nLectura terminada por el usuario")

if __name__ == "__main__":
    read_arduino_data()
