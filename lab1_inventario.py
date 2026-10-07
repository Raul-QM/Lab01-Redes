"""Avance de clase R1-R3: inventario YAML, SSH, errores y logs.

Esta primera etapa solo abre y cierra sesiones. R4-R6 quedan pendientes.
No aplica configuraciones ni genera un reporte de estado ficticio.
"""

import argparse
import getpass
import os
from pathlib import Path
import re

import yaml
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

BASE = Path(__file__).resolve().parent


def leer_inventario(ruta):
    """Validar todo el inventario antes de establecer conexiones."""
    with ruta.open(encoding="utf-8") as archivo:
        inventario = yaml.safe_load(archivo)
    if not isinstance(inventario, dict):
        raise ValueError("El YAML debe contener un diccionario.")
    equipos = inventario.get("equipos")
    if not isinstance(equipos, list) or not equipos:
        raise ValueError("equipos debe ser una lista no vacia.")
    nombres = set()
    variables = set()
    campos = ("nombre", "host", "device_type", "usuario", "rol")
    for equipo in equipos:
        if not isinstance(equipo, dict):
            raise ValueError("Cada equipo debe ser un diccionario.")
        for campo in campos:
            if not isinstance(equipo.get(campo), str) or not equipo[campo].strip():
                raise ValueError(f"Campo requerido invalido: {campo}")
        nombre = equipo["nombre"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", nombre):
            raise ValueError("nombre solo admite letras, numeros, guiones y guion bajo.")
        variable = nombre_variable(nombre)
        if nombre in nombres or variable in variables:
            raise ValueError(f"Nombre o variable de credenciales duplicado: {nombre}")
        nombres.add(nombre)
        variables.add(variable)
        if equipo["rol"] not in ("lectura", "escritura"):
            raise ValueError(f"Rol invalido en {nombre}")
        if any(campo.lower() in {"password", "contrasena", "contraseña", "secret", "clave"}
               for campo in equipo):
            raise ValueError("El inventario no debe incluir contrasenas.")
    return equipos


def nombre_variable(nombre):
    return "LAB_PASS_" + nombre.upper().replace("-", "_")


def obtener_clave(equipo):
    variable = nombre_variable(equipo["nombre"])
    return os.getenv(variable) or getpass.getpass(
        f"Clave SSH para {equipo['nombre']} ({variable}): "
    )


def conectar_equipo(equipo, carpeta_logs):
    """Un fallo de un equipo no interrumpe las conexiones siguientes."""
    resultado = {"equipo": equipo["nombre"], "host": equipo["host"]}
    try:
        clave = obtener_clave(equipo)
        with ConnectHandler(
            host=equipo["host"],
            device_type=equipo["device_type"],
            username=equipo["usuario"],
            password=clave,
            conn_timeout=10,
            auth_timeout=15,
            banner_timeout=15,
            session_log=str(carpeta_logs / f"{equipo['nombre']}.log"),
            session_log_record_writes=False,
        ):
            resultado["estado"] = "ok"
    except NetmikoAuthenticationException:
        resultado["estado"] = "error: autenticacion SSH"
    except NetmikoTimeoutException:
        resultado["estado"] = "error: tiempo de espera SSH"
    except Exception as error:
        # No imprimir el mensaje completo: podria contener datos sensibles.
        resultado["estado"] = f"error: {type(error).__name__}"
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventario", type=Path, default=BASE / "inventario.yaml")
    parser.add_argument("--validar", action="store_true", help="Validar YAML sin conectar")
    args = parser.parse_args()
    try:
        equipos = leer_inventario(args.inventario)
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.exit(2, f"Inventario invalido: {error}\n")
    if args.validar:
        print(f"Inventario valido: {len(equipos)} equipo(s). No se establecieron sesiones.")
        return 0
    carpeta_logs = BASE / "logs"
    carpeta_logs.mkdir(exist_ok=True)
    hubo_errores = False
    for equipo in equipos:
        resultado = conectar_equipo(equipo, carpeta_logs)
        print(f"{resultado['equipo']} | {resultado['host']} | {resultado['estado']}")
        hubo_errores |= resultado["estado"] != "ok"
    return 1 if hubo_errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
