# Extra multivendor y rutas entre PC1 y PC2

Esta demo usa exclusivamente los routers **privados** del proyecto Lab01.
El Cisco compartido del profesor se mantiene de solo lectura y no se configura
con este script. La práctica Ansible de Semana 5 es independiente.

## Direccionamiento local

| Equipo | Interfaz | Dirección / función |
| --- | --- | --- |
| MikroTik | ether1 | 192.168.56.202/24, tránsito y SSH; secundaria 10.60.30.202/24 |
| MikroTik | ether2 | 172.16.20.1/24, gateway PC2 |
| MikroTik | ether3 | WAN por DHCP, red NAT existente 10.0.3.0/24 |
| Cisco 7200 | FastEthernet0/0 | 192.168.56.203/24, tránsito y SSH; secundaria 10.60.30.203/24 |
| Cisco 7200 | FastEthernet1/0 | 172.16.10.1/24, gateway PC1 |
| PC1 | Ethernet0 | 172.16.10.11/24, gateway 172.16.10.1 |
| PC2 | Ethernet0 | 172.16.20.100/24, gateway 172.16.20.1 |

Las dos PC usan DNS 8.8.8.8 y 1.1.1.1. Se configuraron IP estáticas y se guardaron
con `save` en VPCS. Los archivos de configuraciones/ permiten reproducir la base;
los usuarios SSH y sus claves se crean de forma privada por consola.
IOS usa RSA de 1024 bits para el SSH de esta imagen antigua de laboratorio.

El tránsito usa Host-only para acceder desde la laptop. A diferencia de la red
compartida de los apuntes, el Cisco local sale a Internet a través del MikroTik:
su gateway es 192.168.56.202. MikroTik sale por ether3 al NAT de VirtualBox.
No se configuraron servicios ni reglas de firewall en el host GNS3 VM.

## Rutas y NAT

extras/rutas_estaticas.py aplica y verifica:

- MikroTik: ruta 172.16.10.0/24 vía 192.168.56.203.
- Cisco: ruta 172.16.20.0/24 vía 192.168.56.202.
- MikroTik: excepción srcnat accept de PC2 hacia la LAN de PC1, antes del masquerade.
- Cisco: ACL extendida NAT-PC1-LAB01 que excluye el tráfico hacia PC2 y permite
  traducir el resto; reemplaza la ACL estándar 10 en la asociación NAT.

Las rutas y la excepción MikroTik llevan la etiqueta RUTAS-LAB-24. La repetición
consulta los objetos y no vuelve a crearlos. Un contenido distinto en la etiqueta,
la ACL o la asociación NAT provoca un error y no se adopta como propio.

`--limpiar` quita esas rutas y excepciones y restaura el NAT Cisco con ACL 10.
Conserva las IP, interfaces, gateway de Internet y loopback lo-ssh-24.
Al cambiar la asociación NAT se vacían traducciones del Cisco **privado** para que
IOS permita cambiarla; las conexiones de esta demo pueden interrumpirse.

## Ejecutar

Desde Linux, con las claves en las variables correspondientes o introduciéndolas
con getpass:

~~~bash
env-linux/bin/python extras/rutas_estaticas.py --estado
env-linux/bin/python extras/rutas_estaticas.py
env-linux/bin/python extras/rutas_estaticas.py
env-linux/bin/python extras/rutas_estaticas.py --limpiar
env-linux/bin/python extras/rutas_estaticas.py --limpiar
env-linux/bin/python extras/rutas_estaticas.py
env-linux/bin/python extras/verificar_pcs.py
~~~

El inventario de escritura separado es inventarios/extra_local.yaml. El inventario
principal conserva el rol de lectura para Cisco: lab1_inventario.py solamente
consulta Cisco y hace R6 en MikroTik.

En esta laptop, desde PowerShell, el auxiliar utiliza ambas claves DPAPI:

~~~powershell
python ejecutar_local_windows.py extras/rutas_estaticas.py --estado
python ejecutar_local_windows.py extras/rutas_estaticas.py
python ejecutar_local_windows.py extras/verificar_pcs.py
~~~

verificar_pcs.py usa las consolas reales de GNS3 VM 192.168.56.107, puertos 5004
y 5006. Si cambia la IP, usar `--host NUEVA_IP`. No modifica las PC. Guarda JSON
y la salida de consola en texto; exige tres respuestas en cada uno de ocho pings.

## Evidencia

evidencias/extra_rutas/ contiene los estados antes de aplicar, la aplicación,
repetición sin cambios, limpieza y estado final, junto con los pings reales.
Las pruebas incluyen gateway, la otra PC, 1.1.1.1 y google.com desde ambas PC.
Las ocho pruebas aplicadas obtuvieron **3/3 respuestas** cada una.
