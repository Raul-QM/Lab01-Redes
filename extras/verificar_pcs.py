"""Probar los VPCS locales por sus consolas GNS3; no cambia configuracion.

Cada PC debe responder tres veces desde su gateway, la otra PC, 1.1.1.1 y google.com.
Guarda salida real y resumen JSON. Ajustar --host si cambia la IP de GNS3 VM.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
try:
    import telnetlib
except ModuleNotFoundError:
    from netmiko._telnetlib import telnetlib


def probar(host, pc, puerto, destinos):
    resultados = []
    prompt = (pc + '> ').encode()
    with telnetlib.Telnet(host, puerto, 10) as conexion:
        time.sleep(.5)
        conexion.read_very_eager()
        conexion.write(b'\r')
        if prompt not in conexion.read_until(prompt, 5):
            raise RuntimeError('No se recibio el prompt de ' + pc)
        conexion.write(b'show ip\r')
        configuracion = conexion.read_until(prompt, 10).decode(errors='replace').replace('\r', '')
        for destino in destinos:
            comando = f'ping {destino} -c 3'
            conexion.write((comando + '\r').encode())
            salida = conexion.read_until(prompt, 25).decode(errors='replace').replace('\r', '')
            respuestas = len(re.findall(r'bytes from .*?icmp_seq=', salida))
            resultados.append({'destino': destino, 'comando': comando, 'respuestas': respuestas,
                               'correcto': respuestas == 3, 'salida_real': salida})
    return {'pc': pc, 'configuracion_real': configuracion, 'pruebas': resultados,
            'correcto': all(x['correcto'] for x in resultados)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', default='192.168.56.107')
    p.add_argument('--reporte', type=Path, default=Path(__file__).resolve().parents[1]/'evidencias/extra_rutas/pings_finales.json')
    args = p.parse_args()
    casos = [('PC1', 5004, ['172.16.10.1', '172.16.20.100', '1.1.1.1', 'google.com']),
             ('PC2', 5006, ['172.16.20.1', '172.16.10.11', '1.1.1.1', 'google.com'])]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(probar, args.host, *caso) for caso in casos]
        pcs = [f.result() for f in futuros]
    correcto = all(pc['correcto'] for pc in pcs)
    reporte = {'fecha_hora': datetime.now(timezone.utc).isoformat(),
               'fuente': 'Consolas VPCS reales de GNS3', 'correcto': correcto, 'equipos': pcs}
    args.reporte.parent.mkdir(parents=True, exist_ok=True)
    args.reporte.write_text(json.dumps(reporte, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
    texto = '\n'.join(pc['pc']+'\n'+pc['configuracion_real']+'\n'+
                       '\n'.join(x['salida_real'] for x in pc['pruebas']) for pc in pcs)
    args.reporte.with_suffix('.txt').write_text(texto, encoding='utf8')
    for pc in pcs:
        for prueba in pc['pruebas']:
            print(pc['pc'], '->', prueba['destino'], ':', str(prueba['respuestas'])+'/3',
                  'OK' if prueba['correcto'] else 'FALLO')
    print('Reporte:', args.reporte)
    return 0 if correcto else 1


if __name__ == '__main__':
    raise SystemExit(main())
