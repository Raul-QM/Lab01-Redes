"""Demo REAL de R4-R6: aplicar, repetir, limpiar, repetir y dejar aplicado.

Pide las claves una sola vez. Nunca guarda credenciales en archivos.
Se detiene ante errores; no inventa reportes ni resultados de verificacion.
"""
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import hashlib
import json
import os
from pathlib import Path

import lab1_inventario as lab


def ejecutar(args, ruta, descripcion, sin_cambios=False, limpio=False):
    print(f"\n--- {descripcion} ---", flush=True)
    salida = io.StringIO()
    with redirect_stdout(salida):
        rc = lab.main(["--inventario", str(args.inventario), "--reporte", str(ruta)]
                      + (["--limpiar"] if limpio else []))
    texto = salida.getvalue()
    print(texto, end="", flush=True)
    ruta.with_suffix(".txt").write_text(texto, encoding="utf-8")
    if rc:
        raise RuntimeError(f"Fallo en {descripcion}; revise {ruta.name}. No se continua.")
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for equipo in datos:
        conf = equipo.get("configuracion") or {}
        if conf.get("modo"):
            if sin_cambios and conf["cambios"]:
                raise RuntimeError("La repeticion produjo cambios: no se confirma idempotencia.")
            if not conf.get("verificado"):
                raise RuntimeError("Falta verificacion posterior de R6.")
    return datos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventario", type=Path, default=lab.BASE / "inventario.yaml")
    args = parser.parse_args()
    inventario = lab.leer_inventario(args.inventario)
    lab.validar_propietario(inventario)
    identificador = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    carpeta = lab.BASE / "evidencias" / "ejecucion_real" / identificador
    carpeta.mkdir(parents=True, exist_ok=True)
    originales = {}
    try:
        for equipo in inventario["equipos"]:
            variable = lab.nombre_variable(equipo["nombre"])
            originales[variable] = os.environ.get(variable)
            os.environ[variable] = lab.clave(equipo)
        ejecutar(args, carpeta / "01_aplicar.json", "Aplicar y verificar R6")
        ejecutar(args, carpeta / "02_repetir.json", "Repetir: sin cambios", sin_cambios=True)
        ejecutar(args, carpeta / "03_limpiar.json", "Limpiar solo objetos propios", limpio=True)
        ejecutar(args, carpeta / "04_limpiar_repetido.json", "Repetir limpieza: sin cambios",
                 sin_cambios=True, limpio=True)
        ejecutar(args, lab.BASE / "reporte_estado.json", "Estado final: R6 aplicado")
        (carpeta / "05_estado_final.json").write_bytes((lab.BASE / "reporte_estado.json").read_bytes())
        (carpeta / "05_estado_final.txt").write_bytes((lab.BASE / "reporte_estado.txt").read_bytes())
        resumen = {"fecha_hora": datetime.now(timezone.utc).isoformat(),
                   "fuente": "SSH Netmiko real; no simulada", "resultado": "ok",
                   "archivo_reporte_final": "05_estado_final.json",
                   "sha256_reporte_final": hashlib.sha256((lab.BASE / "reporte_estado.json").read_bytes()).hexdigest(),
                   "pasos": ["aplicar y verificar", "repetir sin cambios", "limpiar y verificar",
                             "repetir limpieza sin cambios", "aplicar y verificar estado final"]}
        (carpeta / "verificacion.json").write_text(json.dumps(resumen, indent=2) + "\n", encoding="utf-8")
        print("Verificacion real completa. Los objetos propios quedan aplicados.")
    finally:
        for variable, anterior in originales.items():
            if anterior is None:
                os.environ.pop(variable, None)
            else:
                os.environ[variable] = anterior


if __name__ == "__main__":
    main()
