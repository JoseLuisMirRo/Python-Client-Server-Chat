"""
Prueba rápida para validar la comprobación SHA-256 en el servidor.
Genera un par RSA temporal, cifra un mensaje, y prueba dos payloads:
 - payload válido (hash correcto) -> debe ser aceptado
 - payload manipulado (hash cambiado) -> debe ser descartado

Esta prueba simula únicamente la lógica de verificación del servidor
sin abrir sockets.
"""
import json
import hashlib
import sys
import os

# Añadir directorio raíz del proyecto al path para importar el paquete 'crypto'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.rsa_crypto import RSACrypto


def simulate_server_processing(server_rsa: RSACrypto, payload_json: str) -> bool:
    """Simula el procesamiento del payload en el servidor.
    Devuelve True si el mensaje es aceptado (hash coincide), False si se descarta.
    """
    try:
        parsed = json.loads(payload_json)
    except Exception as e:
        print(f"[SIM] Payload no es JSON: {e}")
        return False

    if not (isinstance(parsed, dict) and 'cipher' in parsed and 'hash' in parsed):
        print("[SIM] Formato JSON inválido")
        return False

    cipher = parsed['cipher']
    recv_hash = parsed['hash']

    try:
        mensaje_desc = server_rsa.descifrar(cipher)
    except Exception as e:
        print(f"[SIM] No se pudo descifrar el cipher: {e}")
        return False

    calc_hash = hashlib.sha256(mensaje_desc.encode('utf-8')).hexdigest()
    if calc_hash != recv_hash:
        print("[SIM] Hash inválido: mensaje descartado")
        print(f"[SIM] hash recibido: {recv_hash}")
        print(f"[SIM] hash calculado: {calc_hash}")
        return False

    print("[SIM] Hash válido: mensaje aceptado")
    print(f"[SIM] Mensaje descifrado: {mensaje_desc}")
    return True


if __name__ == '__main__':
    # Generar par de claves del "servidor"
    server_rsa = RSACrypto()
    private_pem, public_pem = server_rsa.generar_par_claves()

    # Preparar el objeto 'cliente' que cifra con la clave pública del servidor
    client_rsa = RSACrypto()
    client_rsa.cargar_clave_publica(public_pem)

    mensaje = "Este es un mensaje de prueba para verificar hashes"

    # Cifrar mensaje como lo haría el cliente
    cipher = client_rsa.cifrar(mensaje)

    # Caso 1: hash correcto
    correct_hash = hashlib.sha256(mensaje.encode('utf-8')).hexdigest()
    payload_good = json.dumps({'cipher': cipher, 'hash': correct_hash})

    print('\n--- Prueba 1: payload con hash correcto ---')
    accepted = simulate_server_processing(server_rsa, payload_good)
    print(f"Resultado: {'ACEPTADO' if accepted else 'DESCARTADO'}\n")

    # Caso 2: hash manipulado (ataque)
    # Alterar un caracter del hash para simular manipulación
    bad_hash = correct_hash[:-1] + ( '0' if correct_hash[-1] != '0' else '1')
    payload_bad = json.dumps({'cipher': cipher, 'hash': bad_hash})

    print('--- Prueba 2: payload con hash MANIPULADO ---')
    accepted2 = simulate_server_processing(server_rsa, payload_bad)
    print(f"Resultado: {'ACEPTADO' if accepted2 else 'DESCARTADO'}\n")
