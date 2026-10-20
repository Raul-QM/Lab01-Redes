"""Pruebas sin red: fixtures explicitos, no generan evidencia de ejecucion real."""
import contextlib
import io
import json
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab1_inventario as lab

ROS = {
    "identidad": "  name: mt-lab1\n",
    "recursos": "uptime: 2w3d4h5m6s\nversion: 7.20.8 (stable)",
    "interfaces": 'Flags: R - RUNNING\n0 R name=ether1 type=ether\n1 name=ether2 type=ether\n2 R name="bridge prueba" type=bridge',
    "direcciones": '0 D address=10.60.30.202/24 network=10.60.30.0 interface=ether1\n1 address=172.16.20.1/24 network=172.16.20.0 interface="bridge prueba"\n2 X address=192.0.2.1/24 interface=ether2',
    "ruta_defecto": '0 DAd dst-address=0.0.0.0/0 gateway=10.60.30.1 immediate-gw=10.60.30.1%ether1 distance=1\n1 Is dst-address=0.0.0.0/0 gateway=10.60.30.254 distance=2',
}
EQUIPO = {"nombre": "mt-lab", "host": "192.0.2.1", "device_type": "mikrotik_routeros", "usuario": "prueba", "rol": "escritura"}
INVENTARIO = {"estudiante": 7, "nombre_estudiante": "Prueba Unitaria", "equipos": [EQUIPO]}
PROPIETARIO = lab.validar_propietario(INVENTARIO)


class RouterSimulado:
    """Modelo de objetos propios y ajenos para probar limites de limpieza."""
    def __init__(self):
        self.bridge = None
        self.direccion = None
        self.puertos = False
        self.ajeno = {"nombre": "lo-ssh-99", "direccion": "10.253.0.99/32"}
        self.mutaciones = []
        self.comandos = []
        self.cerrado = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cerrado = True

    def send_command(self, comando, **kwargs):
        self.comandos.append(comando)
        for campo, consulta in lab.DRIVERS['mikrotik_routeros']['comandos'].items():
            if consulta == comando:
                return ROS[campo]
        if ' print terse where ' in comando:
            if comando.startswith('/interface bridge port '):
                return '0 bridge=lo-ssh-7 interface=ether2' if self.puertos else ''
            if comando.startswith('/interface bridge ') or comando.startswith('/interface print '):
                return self.bridge or ''
            if comando.startswith('/ip address '):
                return self.direccion or ''
        tokens = shlex.split(comando)
        valores = dict(t.split('=', 1) for t in tokens if '=' in t and not t.startswith('['))
        if ' add ' in comando:
            self.mutaciones.append(comando)
            if comando.startswith('/interface bridge add'):
                self.bridge = '0 R name=' + valores['name'] + ' comment=' + json.dumps(valores['comment'])
            elif comando.startswith('/ip address add'):
                self.direccion = '0 address=' + valores['address'] + ' interface=' + valores['interface'] + ' comment=' + json.dumps(valores['comment'])
            return ''
        if ' remove ' in comando:
            self.mutaciones.append(comando)
            if comando.startswith('/ip address '):
                self.direccion = None
            else:
                self.bridge = None
            return ''
        raise AssertionError('Comando inesperado: ' + comando)


class Parsers(unittest.TestCase):
    def test_comentario_real_sin_comillas_no_se_confunde_con_flags(self):
        fila = lab.registros_terse('0 R comment=LAB01 N=24 - Ral Quesada Morera name=lo-ssh-24 protocol-mode=none')[0]
        self.assertEqual(fila['comment'], 'LAB01 N=24 - Ral Quesada Morera')
        self.assertEqual(fila['flags'], 'R')
        self.assertEqual(fila['name'], 'lo-ssh-24')

    def test_routeros_estructurado_y_flags(self):
        datos = lab.parsear_routeros(ROS)
        self.assertEqual(datos['nombre_equipo'], 'mt-lab1')
        self.assertEqual(datos['tiempo_encendido'], '2w3d4h5m6s')
        self.assertEqual(len(datos['interfaces']), 3)
        self.assertEqual(datos['interfaces'][2]['nombre'], 'bridge prueba')
        self.assertTrue(datos['interfaces'][0]['direcciones'][0]['dinamica'])
        self.assertTrue(datos['interfaces'][1]['direcciones'][0]['deshabilitada'])
        self.assertTrue(datos['rutas_por_defecto'][0]['activa'])
        self.assertFalse(datos['rutas_por_defecto'][1]['activa'])
        self.assertEqual(datos['rutas_por_defecto'][0]['distancia'], 1)

    def test_sin_ips_ni_ruta(self):
        datos = lab.parsear_routeros({**ROS, 'direcciones': '', 'ruta_defecto': ''})
        self.assertEqual(datos['rutas_por_defecto'], [])
        self.assertTrue(all(i['direcciones'] == [] for i in datos['interfaces']))

    def test_ruta_dinamica_routeros_sin_numero_de_fila(self):
        datos = lab.parsear_routeros({**ROS, 'ruta_defecto': '  DAd+ dst-address=0.0.0.0/0 gateway=10.0.3.2 immediate-gw=10.0.3.2%ether3 distance=1'})
        self.assertTrue(datos['rutas_por_defecto'][0]['activa'])
        self.assertEqual(datos['rutas_por_defecto'][0]['gateway'], '10.0.3.2')

    def test_nombre_unicode_y_escape_hex_routeros(self):
        filas = lab.registros_terse('0 name=lo-ssh-24 comment="LAB01 N=24 - Ra\\C3\\BAl Quesada Morera"')
        self.assertEqual(filas[0]['comment'], 'LAB01 N=24 - Raúl Quesada Morera')
        self.assertEqual(lab.citar_routeros('Raúl'), '"Ra\\C3\\BAl"')

    def test_rechazar_respuesta_incompleta(self):
        with self.assertRaises(lab.ErrorEquipo):
            lab.parsear_routeros({**ROS, 'identidad': ''})
        with self.assertRaises(lab.ErrorEquipo):
            lab.registros_terse('0 name="sin terminar')

    def test_cisco_lectura(self):
        datos = lab.parsear_cisco({'identidad': 'hostname R1', 'recursos': 'R1 uptime is 2 days, 5 hours',
            'interfaces': 'Interface IP-Address OK? Method Status Protocol\nFastEthernet0/0 10.60.30.203 YES manual up up\nFastEthernet1/0 unassigned YES unset administratively down down\nNVI0 unassigned NO unset up up',
            'ruta_defecto': 'Routing entry for 0.0.0.0/0\n  * 10.60.30.1, from 0.0.0.0, 00:10:00'})
        self.assertEqual(datos['nombre_equipo'], 'R1')
        self.assertEqual(len(datos['interfaces']), 3)
        self.assertEqual(datos['interfaces'][2]['direcciones'], [])
        self.assertEqual(datos['rutas_por_defecto'][0]['gateway'], '10.60.30.1')

    def test_gateway_estatico_real_ios_sin_from(self):
        datos = lab.parsear_cisco({'identidad': 'hostname cisco-lab-local',
            'recursos': 'cisco-lab-local uptime is 16 minutes',
            'interfaces': 'FastEthernet0/0 192.168.56.203 YES manual up up',
            'ruta_defecto': 'Routing entry for 0.0.0.0/0, supernet\n  Known via "static", distance 1, metric 0, candidate default path\n  Routing Descriptor Blocks:\n  * 192.168.56.202\n      Route metric is 0, traffic share count is 1'})
        self.assertEqual(datos['rutas_por_defecto'][0]['gateway'], '192.168.56.202')


class Configuracion(unittest.TestCase):
    def test_crear_repetir_limpiar_repetir_sin_tocar_ajeno(self):
        router = RouterSimulado()
        ajeno = dict(router.ajeno)
        primero = lab.gestionar_loopback(router, PROPIETARIO)
        self.assertEqual(len(primero['cambios']), 2)
        n = len(router.mutaciones)
        segundo = lab.gestionar_loopback(router, PROPIETARIO)
        self.assertEqual(segundo['resultado'], 'sin cambios')
        self.assertEqual(len(router.mutaciones), n)
        limpieza = lab.gestionar_loopback(router, PROPIETARIO, limpiar=True)
        self.assertEqual(len(limpieza['cambios']), 2)
        self.assertEqual(lab.gestionar_loopback(router, PROPIETARIO, limpiar=True)['resultado'], 'sin cambios')
        self.assertEqual(router.ajeno, ajeno)
        self.assertIn('comment=', router.mutaciones[-1])
        self.assertIn('name=', router.mutaciones[-1])

    def test_objeto_ajeno_no_se_adopta_ni_borra(self):
        for limpiar in (False, True):
            router = RouterSimulado()
            router.bridge = '0 R name=lo-ssh-7 comment="Otro estudiante"'
            with self.assertRaises(lab.ErrorEquipo):
                lab.gestionar_loopback(router, PROPIETARIO, limpiar=limpiar)
            self.assertEqual(router.mutaciones, [])

    def test_bridge_con_puertos_no_se_toca(self):
        router = RouterSimulado()
        lab.gestionar_loopback(router, PROPIETARIO)
        router.puertos = True
        n = len(router.mutaciones)
        with self.assertRaises(lab.ErrorEquipo):
            lab.gestionar_loopback(router, PROPIETARIO, limpiar=True)
        self.assertEqual(len(router.mutaciones), n)

    def test_direccion_ajena_bloquea_cambios(self):
        router = RouterSimulado()
        router.direccion = '0 address=10.253.0.7/32 interface=ether2 comment="ajeno"'
        with self.assertRaises(lab.ErrorEquipo):
            lab.gestionar_loopback(router, PROPIETARIO)
        self.assertEqual(router.mutaciones, [])

    def test_recuperar_creacion_parcial(self):
        router = RouterSimulado()
        lab.gestionar_loopback(router, PROPIETARIO)
        router.direccion = None
        self.assertEqual(lab.gestionar_loopback(router, PROPIETARIO)['cambios'], ['direccion creada'])

    def test_error_de_router_no_es_exito(self):
        with patch.object(RouterSimulado, 'send_command', return_value='failure: not enough permissions'):
            with self.assertRaises(lab.ErrorEquipo):
                lab.enviar(RouterSimulado(), 'comando')

    def test_nombre_se_escapa_sin_inyeccion(self):
        self.assertEqual(lab.citar_routeros('Raul "$x"'), '"Raul \\"\\$x\\""')


class Flujo(unittest.TestCase):
    def test_lectura_no_modifica_y_cierra_sesion(self):
        for modo, equipo in [('estado', EQUIPO), ('aplicar', {**EQUIPO, 'rol': 'lectura'})]:
            router = RouterSimulado()
            with patch.object(lab, 'clave', return_value='no-publicar'), patch.object(lab, 'ConnectHandler', return_value=router):
                r = lab.procesar_equipo(equipo, INVENTARIO, modo, Path('logs'))
            self.assertEqual(r['estado'], 'ok')
            self.assertEqual(router.mutaciones, [])
            self.assertTrue(router.cerrado)
            self.assertNotIn('no-publicar', json.dumps(r))

    def test_continuar_tras_cada_error(self):
        errores = [lab.NetmikoTimeoutException(), lab.NetmikoAuthenticationException(), RuntimeError('clave sensible')]
        for error in errores:
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as carpeta:
                ruta = Path(carpeta)
                inventario = {**INVENTARIO, 'equipos': [EQUIPO, {**EQUIPO, 'nombre': 'segundo'}]}
                (ruta/'inventario.yaml').write_text(lab.yaml.safe_dump(inventario), encoding='utf8')
                with patch.object(lab, 'clave', return_value='no-publicar'), patch.object(lab, 'ConnectHandler', side_effect=[error, RouterSimulado()]), contextlib.redirect_stdout(io.StringIO()):
                    rc = lab.main(['--estado','--inventario',str(ruta/'inventario.yaml'),'--reporte',str(ruta/'reporte.json'),'--logs',str(ruta/'logs')])
                datos = json.loads((ruta/'reporte.json').read_text(encoding='utf8'))
                self.assertEqual(rc, 1)
                self.assertTrue(datos[0]['estado'].startswith('error:'))
                self.assertEqual(datos[1]['estado'], 'ok')
                self.assertEqual(len(datos), 2)
                self.assertNotIn('clave sensible', json.dumps(datos))
                self.assertNotIn('no-publicar', json.dumps(datos))

    def test_propietario_obligatorio_antes_de_conectar(self):
        for n in (None, 0, 255, True, '7'):
            with self.assertRaises(ValueError):
                lab.validar_propietario({**INVENTARIO, 'estudiante': n})

    def test_validacion_inventario(self):
        invalidos = [[], {'equipos': []}, {'equipos': [{**EQUIPO, 'password': 'prohibida'}]},
            {'equipos': [EQUIPO, EQUIPO]}, {'equipos': [{**EQUIPO, 'rol': 'administrador'}]}]
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta)/'inventario.yaml'
            for invalido in invalidos:
                ruta.write_text(lab.yaml.safe_dump(invalido), encoding='utf8')
                with self.assertRaises(ValueError):
                    lab.leer_inventario(ruta)


if __name__ == '__main__':
    unittest.main()
