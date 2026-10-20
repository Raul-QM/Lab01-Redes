"""Demo adicional en routers PRIVADOS: rutas y exclusion NAT entre PC1 y PC2.

Aplicar; --estado solo consulta; --limpiar restaura el NAT base y quita lo propio.
Requiere la base de configuraciones/ y las claves LAB_PASS_* o getpass.
No cambia direcciones, usuarios, WAN ni la loopback obligatoria lo-ssh-24.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab1_inventario as lab

ETIQUETA = "RUTAS-LAB-24"
ACL = "NAT-PC1-LAB01"
RUTA = "ip route 172.16.20.0 255.255.255.0 {gateway} name " + ETIQUETA
NAT_BASE = "ip nat inside source list 10 interface FastEthernet0/0 overload"
NAT_EXTRA = f"ip nat inside source list {ACL} interface FastEthernet0/0 overload"
REGLAS = ["deny ip 172.16.10.0 0.0.0.255 172.16.20.0 0.0.0.255",
          "permit ip 172.16.10.0 0.0.0.255 any"]


def estado(mt, cs):
    rutas = lab.registros_terse(lab.enviar(mt, f'/ip route print terse where comment="{ETIQUETA}"'))
    nat = lab.registros_terse(lab.enviar(mt, f'/ip firewall nat print terse where comment="{ETIQUETA}"'))
    texto = lab.enviar(cs, 'show running-config | include ^ip route|^ip nat inside source')
    lineas = [x.strip() for x in texto.splitlines() if x.strip()]
    acl = lab.enviar(cs, f'show access-lists {ACL}')
    reglas = [re.sub(r'\s+\(.*?matches\).*$', '', re.sub(r'^\s*\d+\s+', '', x)).strip()
              for x in acl.splitlines() if re.match(r'^\s*\d+\s+', x)]
    return {"rutas_mt": rutas, "nat_mt": nat, "lineas_cisco": lineas, "acl_cisco": reglas}


def comprobar(s, host_mt, host_cs):
    if len(s['rutas_mt']) > 1 or len(s['nat_mt']) > 1:
        raise lab.ErrorEquipo('Objetos duplicados con la etiqueta propia; no se modifican.')
    if any(x.get('dst-address') != '172.16.10.0/24' or x.get('gateway') != host_cs
           for x in s['rutas_mt']):
        raise lab.ErrorEquipo('La ruta etiquetada no coincide con la demo.')
    if any(x.get('chain') != 'srcnat' or x.get('action') != 'accept' or
           x.get('src-address') != '172.16.20.0/24' or x.get('dst-address') != '172.16.10.0/24'
           for x in s['nat_mt']):
        raise lab.ErrorEquipo('La excepcion NAT etiquetada no coincide con la demo.')
    if s['acl_cisco'] and s['acl_cisco'] != REGLAS:
        raise lab.ErrorEquipo('La ACL tiene contenido distinto; no se sobrescribe.')
    esperada = RUTA.format(gateway=host_mt)
    if any(ETIQUETA in x and x != esperada for x in s['lineas_cisco']):
        raise lab.ErrorEquipo('La ruta Cisco etiquetada tiene valores distintos.')
    if any(x.startswith('ip nat inside source') and x not in (NAT_BASE, NAT_EXTRA)
           for x in s['lineas_cisco']):
        raise lab.ErrorEquipo('El NAT Cisco no corresponde a la base de esta demo privada.')


def configurar(mt, cs, antes, host_mt, host_cs, limpiar):
    cambios = []
    for tipo, presentes, comando in (
        ('ruta', antes['rutas_mt'], f'/ip route add dst-address=172.16.10.0/24 gateway={host_cs} comment="{ETIQUETA}"'),
        ('excepcion NAT', antes['nat_mt'], f'/ip firewall nat add chain=srcnat src-address=172.16.20.0/24 dst-address=172.16.10.0/24 action=accept comment="{ETIQUETA}" place-before=0'),
    ):
        if limpiar and presentes:
            menu = '/ip route' if tipo == 'ruta' else '/ip firewall nat'
            lab.enviar(mt, f'{menu} remove [find where comment="{ETIQUETA}"]')
            cambios.append('MikroTik: ' + tipo + ' eliminada')
        elif not limpiar and not presentes:
            lab.enviar(mt, comando)
            cambios.append('MikroTik: ' + tipo + ' creada')
    comandos = []
    ruta = RUTA.format(gateway=host_mt)
    if limpiar and ruta in antes['lineas_cisco']:
        comandos.append('no ' + ruta)
    elif not limpiar and ruta not in antes['lineas_cisco']:
        comandos.append(ruta)
    objetivo, anterior = (NAT_BASE, NAT_EXTRA) if limpiar else (NAT_EXTRA, NAT_BASE)
    if objetivo not in antes['lineas_cisco']:
        if anterior in antes['lineas_cisco']:
            lab.enviar(cs, 'clear ip nat translation *')
            comandos.append('no ' + anterior)
        if not limpiar and not antes['acl_cisco']:
            comandos.extend([f'ip access-list extended {ACL}', *REGLAS, 'exit'])
        comandos.append(objetivo)
    if limpiar and antes['acl_cisco']:
        comandos.append(f'no ip access-list extended {ACL}')
    if comandos:
        salida = cs.send_config_set(comandos, error_pattern=r'% (?:Invalid|Incomplete|Ambiguous|Error)|Dynamic mapping in use')
        cs.save_config()
        cambios.extend('Cisco: ' + x for x in comandos)
    return cambios


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventario', type=Path, default=lab.BASE/'inventarios/extra_local.yaml')
    p.add_argument('--reporte', type=Path, default=lab.BASE/'evidencias/extra_rutas.json')
    grupo = p.add_mutually_exclusive_group()
    grupo.add_argument('--estado', action='store_true')
    grupo.add_argument('--limpiar', action='store_true')
    args = p.parse_args()
    inv = lab.leer_inventario(args.inventario)
    if inv.get('laboratorio_privado') is not True or inv.get('estudiante') != 24:
        p.error('Esta demo solo admite el laboratorio PRIVADO del estudiante 24.')
    equipos = {e['device_type']: e for e in inv['equipos']}
    mt_eq, cs_eq = equipos['mikrotik_routeros'], equipos['cisco_ios']
    if not args.estado and any(e['rol'] != 'escritura' for e in (mt_eq, cs_eq)):
        p.error('La demo necesita permiso de escritura explicito en ambos equipos privados.')
    def conectar(e):
        return lab.ConnectHandler(host=e['host'], device_type=e['device_type'], username=e['usuario'],
            password=lab.clave(e), conn_timeout=30, auth_timeout=60, banner_timeout=60,
            session_log=str(lab.BASE/'logs'/('extra_'+e['nombre']+'.log')))
    with conectar(mt_eq) as mt, conectar(cs_eq) as cs:
        cs.enable()
        antes = estado(mt, cs)
        comprobar(antes, mt_eq['host'], cs_eq['host'])
        cambios = [] if args.estado else configurar(mt, cs, antes, mt_eq['host'], cs_eq['host'], args.limpiar)
        despues = estado(mt, cs)
        comprobar(despues, mt_eq['host'], cs_eq['host'])
        aplicada = bool(despues['rutas_mt'] and despues['nat_mt'] and
                        RUTA.format(gateway=mt_eq['host']) in despues['lineas_cisco'] and
                        NAT_EXTRA in despues['lineas_cisco'] and despues['acl_cisco'] == REGLAS)
        limpia = not despues['rutas_mt'] and not despues['nat_mt'] and not despues['acl_cisco'] and NAT_EXTRA not in despues['lineas_cisco'] and RUTA.format(gateway=mt_eq['host']) not in despues['lineas_cisco'] and NAT_BASE in despues['lineas_cisco']
        if not args.estado and not (limpia if args.limpiar else aplicada):
            raise lab.ErrorEquipo('La verificacion posterior de rutas/NAT no coincide.')
        resultado = {'fecha_hora': datetime.now(timezone.utc).isoformat(), 'fuente': 'SSH real',
                     'modo': 'estado' if args.estado else 'limpiar' if args.limpiar else 'aplicar',
                     'cambios': cambios, 'aplicada': aplicada, 'limpia': limpia, 'estado': despues}
        args.reporte.parent.mkdir(parents=True, exist_ok=True)
        args.reporte.write_text(json.dumps(resultado, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
        print('Demo aplicada:', aplicada, '| Demo limpia:', limpia)
        print('\n'.join(cambios) if cambios else 'sin cambios')
        print('Reporte:', args.reporte)


if __name__ == '__main__':
    main()
