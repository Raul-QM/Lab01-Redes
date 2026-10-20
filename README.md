# Laboratorio 1 - Netmiko

ITIEL-13, Redes Programables, UTN. Estudiante: **Raúl Quesada Morera, N=24**.
Repositorio: https://github.com/Raul-QM/Lab01-Redes

## Objetivo y alcance

Un solo script, lab1_inventario.py, lee el YAML, conecta por SSH con Netmiko,
consulta el estado de cada equipo, genera JSON y asegura una loopback propia
sin duplicados. --limpiar elimina exclusivamente los objetos de R6 del estudiante.

El avance R1-R3 del 6 de octubre se conserva en los commits anteriores.
R4-R6 están implementados. El número 24 corresponde a la lista de la auditoría
del profesor. La ejecución usa un MikroTik privado en GNS3 y Debian/WSL como
cliente externo; véanse los resultados y limitaciones en docs/VALIDACION.md.
La verificación SSH completa de R4-R6 terminó correctamente el 19 de octubre de
2026 (Costa Rica; los JSON registran 20 de octubre en UTC). El reporte final y las
cinco etapas reales están versionados. Pasan 18 pruebas automáticas en Windows y WSL.

## Requisitos

- Linux, VM o WSL2 fuera de GNS3, Python 3.10 o posterior, SSH y acceso al laboratorio.
- Netmiko y PyYAML, declarados en requirements.txt.
- MikroTik RouterOS v7, usuario del laboratorio y permisos sobre los objetos propios.
- El Cisco es extra opcional. El driver y parser Cisco están implementados, pero el
  extra solo puede darse por comprobado después de conectar realmente con el equipo.

## Instalación

Desde Linux, dentro de la carpeta del repositorio:

~~~bash
python3 -m venv env-linux
source env-linux/bin/activate
python -m pip install -r requirements.txt
python lab1_inventario.py --validar
~~~

En Windows con la instalación WSL Debian ya preparada para este laboratorio:

~~~powershell
cd "C:\Users\EliteBook\Desktop\Redes Programables\Semana 4\Lab01"
wsl -d Debian -- env-linux/bin/python lab1_inventario.py --validar
~~~

En esta laptop se puede usar la credencial local protegida con Windows DPAPI:

~~~powershell
python ejecutar_local_windows.py lab1_inventario.py --estado
python ejecutar_local_windows.py verificar_entrega.py
~~~

Este auxiliar ejecuta Python en Debian/WSL. La clave cifrada está únicamente en
.local/clave_lab.dpapi, excluida de Git, vinculada a la cuenta Windows que la creó.
No se muestra ni se pasa como argumento. En otro equipo se usa getpass o una variable
de entorno con una credencial autorizada; el repo no distribuye contraseñas.

El código también funciona en Windows con env/Scripts/python.exe, pero la ejecución
solicitada por el enunciado es desde Linux/VM/WSL. La VM Debian de la práctica de
Semana 5 es otra máquina; sus carpetas no se comparten automáticamente con WSL.
Si se usa esa VM, clonar el repo y preparar su propio entorno.

## Inventario y credenciales (R1-R2)

inventario.yaml define nombre, host, device_type, usuario y rol por equipo.
No hay IP de administración ni usuario de equipos incrustados en el script.
puerto es opcional (22 por defecto).

- estudiante: número de lista N CONFIRMADO por el profesor, entero entre 1 y 254.
  El 7 del ejemplo docente no es una asignación para este estudiante.
- nombre_estudiante: nombre usado en el comentario de R6.
- rol: lectura nunca modifica; escritura permite únicamente el configurador R6.
- device_type: mikrotik_routeros o cisco_ios.

Con estudiante: null se permite --estado y --validar. Aplicar o limpiar R6 se
rechaza ANTES de conectar para evitar crear objetos con un número inventado.
El inventario entregado usa 24 y el comentario ASCII `LAB01 N=24 - Raul Quesada Morera`,
compatible con la consola del router. La loopback es lo-ssh-24 y su IP 10.253.0.24/32.

La variable de clave se deriva del nombre: mt-lab -> LAB_PASS_MT_LAB;
cisco-gns3 -> LAB_PASS_CISCO_GNS3. Si falta, getpass pide la clave sin mostrarla.
Para una sesión de shell, se puede introducir sin escribirla en el historial:

~~~bash
read -r -s -p 'Clave MikroTik: ' LAB_PASS_MT_LAB; echo
export LAB_PASS_MT_LAB
~~~

No escribir claves en YAML, código, archivos .env versionados ni mensajes de commit.
Al terminar: unset LAB_PASS_MT_LAB. Para el uso habitual basta con getpass.

## Conexiones y errores (R3)

ConnectHandler se utiliza dentro de with. Se captura por equipo el timeout,
el error de autenticación y cualquier otro Exception; el ciclo sigue con los demás.
Los errores arbitrarios no se copian completos al JSON para evitar exponer secretos.
Cada sesión se agrega a logs/<nombre>.log, sin grabar las escrituras de contraseña.
Los originales quedan excluidos de Git: pueden contener avisos de accesos de terceros.

El código de salida es 0 si todos los equipos terminan ok, 1 si un equipo falla y 2
para errores de argumentos/inventario. El reporte incluye también los equipos fallidos.

## Estado estructurado y reporte (R4-R5)

~~~bash
python lab1_inventario.py --estado
~~~

Consulta únicamente: no crea, borra ni cambia objetos del router.
Los comandos están en DRIVERS, una sola entrada por device_type, junto con su parser.
RouterOS utiliza identity, resource, interface, ip address e ip route print terse.
La tabla muestra equipo, IP, estado, cantidad de interfaces y gateways activos.
Una interfaz sin IP se incluye con direcciones: []. Si no hay ruta por defecto,
rutas_por_defecto es una lista vacía y la tabla muestra '-'.

reporte_estado.json es una lista, un diccionario por equipo:

| Campo | Contenido |
| --- | --- |
| equipo, host, device_type, rol | Identificación desde el YAML |
| fecha_hora | Fecha y hora UTC con zona horaria |
| estado | ok o mensaje de error |
| datos.nombre_equipo | Identidad del router |
| datos.tiempo_encendido | Uptime interpretado, sin texto crudo completo |
| datos.interfaces | Nombres, tipo/estado y direcciones por interfaz |
| datos.rutas_por_defecto | Destino, gateway y estado activo |
| configuracion | Cambios propios, estado anterior/posterior y verificación |

--reporte ruta.json, --logs carpeta y --inventario ruta.yaml permiten elegir rutas.
El archivo JSON se reemplaza de forma atómica para no dejarlo parcialmente escrito.
No se incluye un reporte final simulado ni se debe copiar un ejemplo como evidencia.

## Cambio idempotente y limpieza (R6)

Después de confirmar N y el nombre en el inventario:

~~~bash
python lab1_inventario.py
python lab1_inventario.py
python lab1_inventario.py --limpiar
python lab1_inventario.py --limpiar
~~~

La primera ejecución asegura el bridge sin puertos lo-ssh-N con 10.253.0.N/32.
Bridge e IP llevan el mismo comentario: LAB01 N=N - Nombre.
La segunda ejecución informa 'sin cambios' y no envía comandos add/set/remove.
--limpiar elimina primero la IP propia y luego el bridge propio. Repetir la limpieza
informa 'sin cambios'. --estado y --limpiar son mutuamente excluyentes.

Antes de cualquier escritura se comprueban nombre, IP y comentario exactos.
Si el nombre ya es de otro tipo de interfaz, hay puertos en el bridge, una IP ajena,
otra dirección o un comentario distinto, se registra un conflicto sin adoptar ni
borrar esos objetos. Si una ejecución se interrumpió tras crear solo el bridge,
la siguiente completa únicamente la dirección que falta.

Toda aplicación y limpieza verifica el resultado con comandos de lectura.
Tras cambios se vuelve a recolectar R4 para que el JSON refleje el estado final.
RouterOS guarda automáticamente estos objetos; no se requiere un 'save'.
No se modifican rutas, NAT, DHCP, interfaces físicas ni configuración Cisco en R6.

## Verificación real de entrega

El auxiliar verificar_entrega.py utiliza el MISMO script principal, solicita las
claves una sola vez y las mantiene solo durante el proceso. Ejecuta:

1. Aplicar y verificar.
2. Repetir y exigir cero cambios.
3. Limpiar y verificar la ausencia de lo propio.
4. Repetir limpieza y exigir cero cambios.
5. Aplicar nuevamente y dejar reporte_estado.json con el estado final.

~~~bash
python verificar_entrega.py
~~~

Se detiene ante errores. Guarda los reportes y tablas reales en
 evidencias/ejecucion_real/ y el reporte final en la raíz. No ejecutarlo con un
N inventado ni cambiar el nombre de propietario entre creación y limpieza.
Esta secuencia comprueba R6; no simula un fallo de credenciales automáticamente.
Para una prueba real de error, usar una clave incorrecta solo en una sesión de prueba
con --estado y --reporte evidencias/error_autenticacion.json. No sobrescribir el
reporte final correcto con la prueba de error.

## Pruebas automáticas sin red

~~~bash
python -m unittest discover -s tests -v
~~~

Fixtures explícitos comprueban parsers RouterOS/Cisco, rutas ausentes, cadenas con
espacios, flags, validación de inventario, cierre de sesiones, continuación después
de errores, idempotencia y rechazo de objetos ajenos/puertos ajenos. Son pruebas
simuladas y NO acreditan conectividad ni permisos reales.

## Topología GNS3 y guía de rutas

Lab01.gns3 contiene la topología guardada:

~~~text
Internet/Cloud (eth0, Host-only) -- SW1 (Ethernet0)
SW1 (Ethernet1) -- MikroTik (ether1)
MikroTik (ether2) -- PC2
SW1 (Ethernet2) -- Cisco (FastEthernet0/0)
Cisco (FastEthernet1/0) -- PC1
Internet/Cloud (eth1, NAT existente) -- MikroTik (ether3, WAN DHCP)
~~~

El Cisco local es un 7200 (solicitado por el estudiante), en vez del 3725 de la
imagen docente. Tiene NPE-400, 512 MB, C7200-IO-FE y PA-FE-TX, en GNS3 VM.
Imagen c7200-adventerprisek9-mz.124-24.T5.image;
MD5 6b89d0d804e1f2bb5b8bda66b5692047. Las imágenes y discos no se publican.
El 19 de octubre se calculó y aplicó Idle-PC 0x63d6d8d8 al Cisco local;
GNS3 confirmó el equipo encendido con ese valor.
El proyecto requiere esas imágenes y GNS3 VM instalada; el .gns3 no es una VM portable.
La administración local es 192.168.56.202/24 por ether1 y usuario lab-ssh.
El adaptador Host-only de Windows debe estar en 192.168.56.0/24 y GNS3 VM encendida.
La WAN recibe dirección de la red NAT existente 10.0.3.0/24 por DHCP en ether3.
No se modificaron el firewall ni servicios de red del host GNS3 VM.
10.60.30.202 es la dirección del entorno compartido del profesor; su inventario
alternativo está en inventarios/compartido.ejemplo.yaml y requiere su acceso de clase.

Apuntes rutas_estaticas.py es una demo adicional de rutas/NAT entre las LAN de PC1 y
PC2. No sustituye R6. El Cisco compartido es de solo lectura según el enunciado;
no ejecutar comandos de escritura de esa demo contra él. La conexión entre ambas
PC no se da por comprobada a partir de un SSH exitoso al laboratorio compartido.
La práctica Ansible PracticaClase5 es independiente de este Lab01.

## Uso de IA

Se utilizó Codex como apoyo en el desarrollo y la depuración del código,
la configuración del entorno GNS3 y la verificación de resultados.
