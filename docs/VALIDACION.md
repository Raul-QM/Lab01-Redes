# Verificación de entrega — 19 de octubre de 2026, Costa Rica

Estudiante: Raúl Quesada Morera, N=24, confirmado con la auditoría docente.
Cliente Netmiko: Debian/WSL, fuera de GNS3. Routers privados: MikroTik RouterOS
7.20.8 (192.168.56.202) y Cisco 7200 IOS 12.4(24)T5 (192.168.56.203).
Los JSON usan UTC: 20 de octubre de 2026.

| Requisito | Evidencia y resultado |
| --- | --- |
| R1 | YAML válido, N=24; MikroTik escritura y Cisco lectura |
| R2 | LAB_PASS_* o getpass; claves privadas excluidas de Git |
| R3 | with, errores por equipo y logs; fallo real de autenticación seguido de éxito en evidencias/error_y_continuidad.json |
| R4 | SSH real en ambos fabricantes: identidad, uptime, interfaces/IP y gateway; incluye NVI0 sin IP del Cisco |
| R5 | reporte_estado.json: dos equipos con estado ok, fecha UTC, datos estructurados y tablas reales |
| R6 | Crear/verificar, repetir sin cambios, limpiar/verificar, repetir limpieza sin cambios y recrear lo-ssh-24 / 10.253.0.24/32 |
| Logs | Sesiones reales de ambos fabricantes en logs/*.sanitizado.log; claves y avisos de terceros excluidos |
| Documentación | README, instalación, comandos, configuración base y declaración de IA |
| Colaborador | randthat verificado mediante API de GitHub con permiso write |
| Extra Cisco | Consulta SSH real con rol lectura en el inventario principal |
| Extra rutas/NAT | Aplicación, repetición, limpieza y recreación en ambos routers privados; ocho pings desde las PC con 3/3 respuestas |

## Evidencia principal actual

Carpeta: [20261020T051303131017Z](../evidencias/ejecucion_real/20261020T051303131017Z/).

1. 01_aplicar.json: objetos propios presentes y verificados, sin cambios.
2. 02_repetir.json: sin cambios.
3. 03_limpiar.json: dirección y bridge propios eliminados; Cisco solo lectura.
4. 04_limpiar_repetido.json: sin cambios, objetos propios ausentes.
5. 05_estado_final.json: bridge y dirección recreados y verificados; copia del
   reporte_estado.json de la raíz. Comentario: LAB01 N=24 - Raul Quesada Morera.

verificacion.json conserva el SHA-256 de 05_estado_final.json y la secuencia
realizada. Los .txt contienen la tabla real del script. La ejecución anterior,
solo con MikroTik, se conserva en 20261020T043406281096Z con su reporte final
archivado; no se mezcla con la evidencia multivendor actual.

La prueba R3 usa dos entradas del mismo MikroTik: una clave deliberadamente
incorrecta y otra válida. Su salida 1 es la esperada y el segundo equipo terminó
ok. No se publican las claves ni se reemplaza el reporte final correcto con ese error.

## Extras verificados

Ver [EXTRAS.md](EXTRAS.md), configuraciones/ y evidencias/extra_rutas/.
Se usaron las LAN de los apuntes: PC1 172.16.10.11/24 y PC2 172.16.20.100/24.
El tránsito privado es 192.168.56.0/24; Cisco sale a Internet por MikroTik y este
por la red NAT ya existente de VirtualBox en ether3. El script adicional solo
admite el inventario marcado como privado y permisos de escritura explícitos.
El Cisco compartido del profesor no se modifica.

La aplicación creó rutas y excepciones NAT. Repetir produjo cero cambios; limpiar
restauró la asociación NAT base y eliminó solamente los objetos de la demo;
repetir la limpieza produjo cero cambios. Se dejó la demo aplicada nuevamente.
Desde ambas PC se probó gateway, la otra PC, 1.1.1.1 y google.com: 3/3 respuestas
en cada prueba. Los archivos pings_aplicados.* y pings_finales.* contienen las
salidas reales. Cisco y MikroTik quedaron encendidos.

## Pruebas automáticas y compatibilidad

`python -m unittest discover -s tests -v`: **24 pruebas correctas en Windows y 24
en Debian/WSL**. Cubren R1-R6, parsers RouterOS/Cisco con formatos observados en los
routers, continuidad de errores, idempotencia y protección de objetos ajenos.
También comprueban el rechazo de ACL/NAT/rutas diferentes en el extra privado y
que repetir aplicación o limpieza no envíe escrituras.
Las pruebas con fixtures están separadas de la evidencia SSH/VPCS real.

Se usó el nombre ASCII en el comentario por compatibilidad con la consola RouterOS.
El parser reconoce comentarios sin comillas, rutas RouterOS sin índice e interfaces
Cisco NVI0 con OK?=NO. El gateway estático Cisco se interpreta aunque no contenga
la expresión `from`. Se ampliaron los tiempos de conexión por la carga de la VM.
El entorno virtual utiliza Paramiko 4 para el SSH legado de IOS 12.4; los paquetes
del sistema no se modificaron. La comprobación real se hizo después de estos ajustes.

## Reproducción

El .gns3 incluye nodos y enlaces, sin imágenes propietarias ni discos de VM.
En otra máquina se requieren las imágenes, aplicar la base de configuraciones/,
crear credenciales privadas y ajustar los inventarios. El auxiliar Windows usa
claves cifradas con DPAPI en .local/, excluidas de Git. La práctica Ansible de
Semana 5 es independiente de este laboratorio.
