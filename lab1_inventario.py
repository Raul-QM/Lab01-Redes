"""Lab 1: inventario YAML, SSH Netmiko, estado JSON y loopback propia.

--estado: solo lectura. Sin opciones: asegurar R6. --limpiar: quitar R6 propio.
Las credenciales se leen de LAB_PASS_<NOMBRE> o mediante getpass.
"""
import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import shlex

import yaml
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

BASE = Path(__file__).resolve().parent


class ErrorEquipo(ValueError):
    """Mensaje conocido, apto para reporte; no contiene salida cruda ni claves."""


def nombre_variable(nombre):
    return "LAB_PASS_" + nombre.upper().replace("-", "_")


def leer_inventario(ruta):
    with Path(ruta).open(encoding="utf-8") as archivo:
        inventario = yaml.safe_load(archivo)
    if not isinstance(inventario, dict):
        raise ValueError("El YAML debe contener un diccionario.")
    equipos = inventario.get("equipos")
    if not isinstance(equipos, list) or not equipos:
        raise ValueError("equipos debe ser una lista no vacia.")
    usados = set()
    for equipo in equipos:
        if not isinstance(equipo, dict):
            raise ValueError("Cada equipo debe ser un diccionario.")
        for campo in ("nombre", "host", "device_type", "usuario", "rol"):
            if not isinstance(equipo.get(campo), str) or not equipo[campo].strip():
                raise ValueError(f"Campo requerido invalido: {campo}")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", equipo["nombre"]):
            raise ValueError("nombre solo admite letras, numeros, guiones y guion bajo.")
        variable = nombre_variable(equipo["nombre"])
        if variable in usados:
            raise ValueError("Nombre o variable de credenciales duplicado.")
        usados.add(variable)
        if equipo["rol"] not in ("lectura", "escritura"):
            raise ValueError("rol debe ser lectura o escritura.")
        if equipo["device_type"] not in DRIVERS:
            raise ValueError("device_type no soportado; consulte DRIVERS.")
        if any(str(c).lower() in {"password", "contrasena", "contraseña", "secret", "clave"} for c in equipo):
            raise ValueError("No se admiten contrasenas en el inventario.")
        if "puerto" in equipo and (type(equipo["puerto"]) is not int or not 1 <= equipo["puerto"] <= 65535):
            raise ValueError("puerto debe ser un entero entre 1 y 65535.")
        if "conexion_host" in equipo and (not isinstance(equipo["conexion_host"], str) or not equipo["conexion_host"].strip()):
            raise ValueError("conexion_host debe ser una direccion de conexion no vacia.")
    return inventario


def validar_propietario(inventario):
    n = inventario.get("estudiante")
    nombre = inventario.get("nombre_estudiante", "")
    if type(n) is not int or not 1 <= n <= 254:
        raise ValueError("Confirme estudiante: N (numero de lista entre 1 y 254).")
    if not isinstance(nombre, str) or not nombre.strip() or len(nombre) > 100:
        raise ValueError("Complete nombre_estudiante con su nombre (maximo 100 caracteres).")
    if any(ord(c) < 32 or ord(c) == 127 for c in nombre):
        raise ValueError("El nombre no puede contener caracteres de control.")
    return f"lo-ssh-{n}", f"10.253.0.{n}/32", f"LAB01 N={n} - {nombre.strip()}"


def clave(equipo):
    return os.getenv(nombre_variable(equipo["nombre"])) or getpass.getpass(
        f"Clave SSH para {equipo['nombre']} ({nombre_variable(equipo['nombre'])}): "
    )


def registros_terse(texto):
    """Interpretar filas RouterOS, incluidas propiedades entre comillas."""
    registros = []
    for linea in texto.splitlines():
        if "=" not in linea or not re.match(r"^\s*(?:\d+\s|[A-Za-z+*]+\s+\w[\w-]*=|[\w.-]+=)", linea):
            continue
        try:
            # shlex no debe eliminar los escapes hexadecimales de RouterOS.
            linea = re.sub(r"\\([0-9A-Fa-f]{2})", r"\\\\\1", linea)
            tokens = shlex.split(linea, posix=True)
        except ValueError as error:
            raise ErrorEquipo("No se pudo interpretar una fila RouterOS terse.") from error
        indice = tokens.pop(0) if tokens[0].isdigit() else None
        fila = {"indice": indice, "flags": ""}
        ultima = None
        for token in tokens:
            if re.match(r"^[a-z][a-z0-9-]*=", token):
                k, valor = token.split("=", 1)
                fila[k] = re.sub(r"(?:\\[0-9A-Fa-f]{2})+",
                    lambda m: bytes.fromhex(m[0].replace("\\", "")).decode("utf-8", errors="replace"), valor)
                ultima = k
            elif ultima is not None:
                # RouterOS real imprime comentarios con espacios SIN comillas.
                fila[ultima] += " " + token
            elif re.fullmatch(r"[A-Za-z+*]+", token):
                fila["flags"] += token
        registros.append(fila)
    if "=" in texto and not registros:
        raise ErrorEquipo("RouterOS no devolvio filas terse reconocibles.")
    return registros


def pares_colon(texto):
    return {m[1]: m[2].strip() for linea in texto.splitlines()
            if (m := re.match(r"^\s*([\w-]+):\s*(.*?)\s*$", linea))}


def parsear_routeros(salidas):
    identidad = pares_colon(salidas["identidad"]).get("name")
    uptime = pares_colon(salidas["recursos"]).get("uptime")
    if not identidad or not uptime:
        raise ErrorEquipo("Faltan nombre o uptime en la respuesta RouterOS.")
    direcciones = registros_terse(salidas["direcciones"])
    interfaces = []
    for fila in registros_terse(salidas["interfaces"]):
        nombre = fila.get("name")
        if not nombre:
            raise ErrorEquipo("Interfaz RouterOS sin nombre.")
        interfaces.append({"nombre": nombre, "tipo": fila.get("type"),
            "activa": "R" in fila["flags"] or fila.get("running") == "true",
            "direcciones": [{"direccion": d["address"], "red": d.get("network"),
                "dinamica": "D" in d["flags"], "deshabilitada": "X" in d["flags"]}
                for d in direcciones if d.get("interface") == nombre and "address" in d]})
    rutas = [{"destino": f.get("dst-address"), "gateway": f.get("gateway"),
        "gateway_inmediato": f.get("immediate-gw"),
        "distancia": int(f["distance"]) if f.get("distance", "").isdigit() else None,
        "activa": "A" in f["flags"] or f.get("active") == "true"}
        for f in registros_terse(salidas["ruta_defecto"]) if f.get("dst-address") == "0.0.0.0/0"]
    return {"nombre_equipo": identidad, "tiempo_encendido": uptime,
            "interfaces": interfaces, "rutas_por_defecto": rutas}


def parsear_cisco(salidas):
    nombre = re.search(r"^\s*hostname\s+(\S+)", salidas["identidad"], re.M)
    uptime = re.search(r"\buptime is\s+(.+)", salidas["recursos"])
    if not nombre or not uptime:
        raise ErrorEquipo("Faltan hostname o uptime en la respuesta Cisco IOS.")
    interfaces = []
    for linea in salidas["interfaces"].splitlines():
        m = re.match(r"^(\S+)\s+(unassigned|\d+\.\d+\.\d+\.\d+)\s+(?:YES|NO)\s+\S+\s+(.+?)\s+(up|down)\s*$", linea)
        if m:
            interfaces.append({"nombre": m[1], "estado": m[3], "protocolo": m[4],
                "direcciones": [] if m[2] == "unassigned" else [{"direccion": m[2]}]})
    gateways = re.findall(r"^\s*(?:\*\s*)?(\d+\.\d+\.\d+\.\d+)(?:,\s+from\s+|\s*$)",
                          salidas["ruta_defecto"], re.M)
    rutas = [{"destino": "0.0.0.0/0", "gateway": g, "activa": True} for g in dict.fromkeys(gateways)]
    return {"nombre_equipo": nombre[1], "tiempo_encendido": uptime[1].strip(),
            "interfaces": interfaces, "rutas_por_defecto": rutas}


def enviar(conexion, comando):
    salida = conexion.send_command(comando, read_timeout=30)
    if re.search(r"^\s*(failure:|syntax error|expected |bad command name|no such item|% (?:Invalid|Error))", salida, re.I | re.M):
        raise ErrorEquipo("El equipo rechazo un comando; revise el session_log local.")
    return salida


def citar_routeros(texto):
    escapado = texto.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    return '"' + ''.join(c if ord(c) < 128 else ''.join(f"\\{b:02X}" for b in c.encode("utf-8"))
                         for c in escapado) + '"'


def inspeccionar_loopback(conexion, propietario):
    nombre, direccion, comentario = propietario
    qnombre = citar_routeros(nombre)
    puentes = registros_terse(enviar(conexion, f"/interface bridge print terse where name={qnombre}"))
    interfaces = registros_terse(enviar(conexion, f"/interface print terse where name={qnombre}"))
    puertos = registros_terse(enviar(conexion, f"/interface bridge port print terse where bridge={qnombre}"))
    ips = registros_terse(enviar(conexion, f"/ip address print terse where interface={qnombre}"))
    coincidencias = registros_terse(enviar(conexion, f"/ip address print terse where address={citar_routeros(direccion)}"))
    if len(puentes) > 1 or len(ips) > 1:
        raise ErrorEquipo("Conflicto: hay duplicados o IP adicionales; no se modificaron.")
    if interfaces and not puentes:
        raise ErrorEquipo("Conflicto: el nombre lo-ssh-N pertenece a otra clase de interfaz.")
    if puentes and (puentes[0].get("comment") != comentario or "X" in puentes[0]["flags"]):
        raise ErrorEquipo("Conflicto: bridge ajeno, comentario diferente o bridge deshabilitado.")
    if puertos:
        raise ErrorEquipo("Conflicto: el bridge tiene puertos; no es una loopback aislada.")
    if ips and (ips[0].get("address") != direccion or ips[0].get("comment") != comentario or "X" in ips[0]["flags"]):
        raise ErrorEquipo("Conflicto: direccion ajena, distinta o deshabilitada en la interfaz.")
    if any(f.get("interface") != nombre or f.get("comment") != comentario for f in coincidencias):
        raise ErrorEquipo("Conflicto: la IP de estudiante ya esta utilizada por otro objeto.")
    return {"bridge": bool(puentes), "direccion": bool(ips)}


def gestionar_loopback(conexion, propietario, limpiar=False):
    nombre, direccion, comentario = propietario
    antes = inspeccionar_loopback(conexion, propietario)
    cambios = []
    qnombre, qdireccion, qcomentario = map(citar_routeros, propietario)
    if limpiar:
        if antes["direccion"]:
            enviar(conexion, f"/ip address remove [find where interface={qnombre} and address={qdireccion} and comment={qcomentario}]")
            cambios.append("direccion eliminada")
        if antes["bridge"]:
            enviar(conexion, f"/interface bridge remove [find where name={qnombre} and comment={qcomentario}]")
            cambios.append("bridge eliminado")
    else:
        if not antes["bridge"]:
            enviar(conexion, f"/interface bridge add name={qnombre} protocol-mode=none comment={qcomentario}")
            cambios.append("bridge creado")
        if not antes["direccion"]:
            enviar(conexion, f"/ip address add address={qdireccion} interface={qnombre} comment={qcomentario}")
            cambios.append("direccion creada")
    despues = inspeccionar_loopback(conexion, propietario)
    if despues != {"bridge": not limpiar, "direccion": not limpiar}:
        raise ErrorEquipo("La verificacion posterior no coincide con el estado solicitado.")
    return {"modo": "limpiar" if limpiar else "aplicar", "interfaz": nombre,
            "direccion": direccion, "comentario": comentario, "cambios": cambios,
            "resultado": ", ".join(cambios) if cambios else "sin cambios",
            "verificado": True, "antes": antes, "despues": despues}


# Comandos, parsers y configurador declarados una vez por fabricante (R4).
DRIVERS = {
    "mikrotik_routeros": {
        "comandos": {"identidad": "/system identity print", "recursos": "/system resource print",
            "interfaces": "/interface print terse", "direcciones": "/ip address print terse",
            "ruta_defecto": "/ip route print terse where dst-address=0.0.0.0/0"},
        "parser": parsear_routeros, "configurar": gestionar_loopback,
    },
    "cisco_ios": {
        "comandos": {"identidad": "show running-config | include hostname",
            "recursos": "show version | include uptime", "interfaces": "show ip interface brief",
            "ruta_defecto": "show ip route 0.0.0.0"},
        "parser": parsear_cisco, "configurar": None,
    },
}


def procesar_equipo(equipo, inventario, modo, carpeta_logs):
    resultado = {"equipo": equipo["nombre"], "host": equipo["host"],
        "device_type": equipo["device_type"], "rol": equipo["rol"],
        "fecha_hora": datetime.now(timezone.utc).isoformat(),
        "estado": "ok", "datos": None, "configuracion": None}
    try:
        driver = DRIVERS[equipo["device_type"]]
        with ConnectHandler(host=equipo.get("conexion_host", equipo["host"]), port=equipo.get("puerto", 22),
            device_type=equipo["device_type"], username=equipo["usuario"], password=clave(equipo),
            conn_timeout=30, auth_timeout=60, banner_timeout=60,
            session_log=str(carpeta_logs / f"{equipo['nombre']}.log"),
            session_log_record_writes=False, session_log_file_mode="append") as conexion:
            salidas = {dato: enviar(conexion, comando) for dato, comando in driver["comandos"].items()}
            resultado["datos"] = driver["parser"](salidas)
            if modo == "estado" or equipo["rol"] == "lectura" or not driver["configurar"]:
                resultado["configuracion"] = {"resultado": "solo lectura", "cambios": []}
            else:
                resultado["configuracion"] = driver["configurar"](
                    conexion, validar_propietario(inventario), limpiar=modo == "limpiar")
                if resultado["configuracion"]["cambios"]:
                    salidas = {dato: enviar(conexion, comando) for dato, comando in driver["comandos"].items()}
                    resultado["datos"] = driver["parser"](salidas)
    except NetmikoAuthenticationException:
        resultado["estado"] = "error: autenticacion SSH"
    except NetmikoTimeoutException:
        resultado["estado"] = "error: tiempo de espera SSH"
    except ErrorEquipo as error:
        resultado["estado"] = f"error: {error}"
    except Exception as error:
        resultado["estado"] = f"error: {type(error).__name__} (revise el log local)"
    return resultado


def guardar_reporte(resultados, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text(json.dumps(resultados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporal.replace(ruta)


def imprimir_tabla(resultados):
    filas = [("EQUIPO", "IP", "ESTADO", "INTERFACES", "GATEWAY POR DEFECTO")]
    for r in resultados:
        datos = r["datos"] or {}
        gateways = ", ".join(str(f.get("gateway")) for f in datos.get("rutas_por_defecto", [])
                             if f.get("activa") and f.get("gateway")) or "-"
        filas.append((r["equipo"], r["host"], r["estado"],
            str(len(datos["interfaces"])) if r["datos"] else "-", gateways))
    anchos = [max(len(f[i]) for f in filas) for i in range(5)]
    for n, fila in enumerate(filas):
        print(" | ".join(valor.ljust(anchos[i]) for i, valor in enumerate(fila)).rstrip())
        if n == 0:
            print("-+-".join("-" * ancho for ancho in anchos))
    for r in resultados:
        if r["configuracion"]:
            print(f"{r['equipo']}: {r['configuracion']['resultado']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--inventario", type=Path, default=BASE / "inventario.yaml")
    parser.add_argument("--reporte", type=Path, default=BASE / "reporte_estado.json")
    parser.add_argument("--logs", type=Path, default=BASE / "logs")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--estado", action="store_true", help="Solo lectura")
    grupo.add_argument("--limpiar", action="store_true", help="Eliminar exclusivamente los objetos propios")
    grupo.add_argument("--validar", action="store_true", help="Validar inventario sin conectar")
    args = parser.parse_args(argv)
    modo = "estado" if args.estado else "limpiar" if args.limpiar else "aplicar"
    try:
        inventario = leer_inventario(args.inventario)
        if args.validar:
            print(f"Inventario valido: {len(inventario['equipos'])} equipo(s). No se establecieron sesiones.")
            if inventario.get("estudiante") is None:
                print("R6 pendiente: confirme estudiante y nombre_estudiante antes de aplicar o limpiar.")
            return 0
        if modo != "estado" and any(e["rol"] == "escritura" and DRIVERS[e["device_type"]]["configurar"] for e in inventario["equipos"]):
            validar_propietario(inventario)
        args.logs.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.exit(2, f"Inventario o rutas invalidas: {error}\n")
    resultados = [procesar_equipo(e, inventario, modo, args.logs) for e in inventario["equipos"]]
    guardar_reporte(resultados, args.reporte)
    imprimir_tabla(resultados)
    print(f"Reporte: {args.reporte}")
    return int(any(r["estado"] != "ok" for r in resultados))


if __name__ == "__main__":
    raise SystemExit(main())
