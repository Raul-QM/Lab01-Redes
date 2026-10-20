"""Limites de la demo privada: conflictos y ausencia de cambios al repetir."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extras import rutas_estaticas as rutas

MT, CS = '192.168.56.202', '192.168.56.203'
BASE = {'rutas_mt': [], 'nat_mt': [], 'lineas_cisco': [rutas.NAT_BASE], 'acl_cisco': []}
APLICADA = {'rutas_mt': [{'dst-address': '172.16.10.0/24', 'gateway': CS}],
            'nat_mt': [{'chain': 'srcnat', 'action': 'accept', 'src-address': '172.16.20.0/24',
                        'dst-address': '172.16.10.0/24'}],
            'lineas_cisco': [rutas.RUTA.format(gateway=MT), rutas.NAT_EXTRA],
            'acl_cisco': rutas.REGLAS.copy()}


class RutasExtra(unittest.TestCase):
    def test_base_y_estado_aplicado_son_validos(self):
        for estado in (BASE, APLICADA):
            rutas.comprobar(estado, MT, CS)

    def test_no_adopta_ruta_con_otro_gateway(self):
        estado = deepcopy(APLICADA)
        estado['rutas_mt'][0]['gateway'] = '192.0.2.1'
        with self.assertRaises(rutas.lab.ErrorEquipo):
            rutas.comprobar(estado, MT, CS)

    def test_no_sobrescribe_acl_diferente(self):
        estado = deepcopy(APLICADA)
        estado['acl_cisco'] = ['permit ip any any']
        with self.assertRaises(rutas.lab.ErrorEquipo):
            rutas.comprobar(estado, MT, CS)

    def test_no_toca_nat_o_rutas_duplicadas(self):
        for campo, valor in [('lineas_cisco', 'ip nat inside source list AJENA interface FastEthernet0/0 overload'),
                             ('rutas_mt', APLICADA['rutas_mt'][0])]:
            estado = deepcopy(APLICADA)
            estado[campo].append(valor)
            with self.assertRaises(rutas.lab.ErrorEquipo):
                rutas.comprobar(estado, MT, CS)

    def test_repetir_aplicacion_o_limpieza_no_envia_escrituras(self):
        for estado, limpiar in ((APLICADA, False), (BASE, True)):
            mt, cs = Mock(), Mock()
            self.assertEqual(rutas.configurar(mt, cs, estado, MT, CS, limpiar), [])
            self.assertEqual(mt.mock_calls, [])
            self.assertEqual(cs.mock_calls, [])


if __name__ == '__main__':
    unittest.main()
