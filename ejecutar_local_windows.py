"""Ejecutar el laboratorio en WSL usando la clave local cifrada con Windows DPAPI.

La clave no se muestra ni se pasa por argumentos. Solo funciona en la cuenta
Windows que la guardo. En otra computadora usar getpass del script principal.
"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent


class Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def main():
    if sys.platform != "win32":
        raise SystemExit("Este auxiliar es para Windows. En Linux ejecutar lab1_inventario.py.")
    ruta = BASE / ".local" / "clave_lab.dpapi"
    if not ruta.exists():
        raise SystemExit("No hay clave local cifrada. Usar lab1_inventario.py con getpass desde Linux.")
    credenciales = {}
    for variable, archivo in (("LAB_PASS_MT_LAB", "clave_lab.dpapi"),
                              ("LAB_PASS_CISCO_GNS3", "clave_cisco.dpapi")):
        ruta = BASE / ".local" / archivo
        if not ruta.exists():
            continue
        datos = ruta.read_bytes()
        buffer = ctypes.create_string_buffer(datos)
        entrada = Blob(len(datos), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
        salida = Blob()
        if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(entrada), None, None, None,
                                                      None, 0, ctypes.byref(salida)):
            raise ctypes.WinError()
        try:
            credenciales[variable] = ctypes.string_at(salida.pbData, salida.cbData).decode()
        finally:
            ctypes.windll.kernel32.LocalFree(salida.pbData)
    argumentos = sys.argv[1:] or ["lab1_inventario.py"]
    programa = (
        "import json,os,runpy,sys; "
        "os.environ.update(json.loads(sys.stdin.readline())); "
        "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
    )
    resultado = subprocess.run(
        ["wsl", "-d", "Debian", "--", "env-linux/bin/python", "-c", programa, *argumentos],
        cwd=BASE, input=json.dumps(credenciales) + "\n", text=True,
    )
    return resultado.returncode


if __name__ == "__main__":
    raise SystemExit(main())
