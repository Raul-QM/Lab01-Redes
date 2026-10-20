# Verificación de entrega — 19 de octubre de 2026, Costa Rica

Estudiante: Raúl Quesada Morera, N=24, confirmado con la lista de la auditoría
docente. Se ejecutó desde Debian/WSL, fuera de GNS3, contra el MikroTik privado
192.168.56.202, identidad mt-lab-local, RouterOS 7.20.8.
Los JSON usan UTC: 20 de octubre de 2026.

| Requisito | Evidencia y resultado |
| --- | --- |
| R1 | inventario.yaml válido: campos requeridos, N=24 y roles |
| R2 | Credencial de entorno; getpass como alternativa; no hay claves versionadas |
| R3 | ConnectHandler con with, logs; prueba real de autenticación fallida seguida de equipo exitoso en evidencias/error_y_continuidad.json |
| R4 | SSH real: identidad, uptime, cinco interfaces con sus IP y gateway 10.0.3.2, sin texto crudo en datos |
| R5 | reporte_estado.json final: lista de diccionarios, fecha UTC y estado ok; tablas en cada etapa |
| R6 | Aplicación, repetición sin cambios, limpieza, limpieza repetida sin cambios y recreación verificadas por SSH |
| Logs | logs/mt-lab.sanitizado.log conserva cinco sesiones reales propias; se quitan líneas vacías/prompts repetidos y se excluyen avisos de terceros |
| Documentación | README con instalación, ejecución, inventario, seguridad, alcance y declaración de IA |
| Colaborador | API de GitHub: randthat tiene permission=write y role_name=write; sin invitación pendiente |

## Ejecución real

Carpeta: [20261020T043406281096Z](../evidencias/ejecucion_real/20261020T043406281096Z/).

1. 01_aplicar.json: objetos ya presentes, verificados, sin cambios.
2. 02_repetir.json: sin cambios.
3. 03_limpiar.json: dirección y bridge propios eliminados; cuatro interfaces restantes.
4. 04_limpiar_repetido.json: sin cambios, objetos propios ausentes.
5. reporte_estado.json en la raíz: bridge y dirección creados nuevamente;
   lo-ssh-24, 10.253.0.24/32 y comentario LAB01 N=24 - Raul Quesada Morera.

Todas las etapas terminaron con estado ok. verificacion.json conserva el SHA-256
del reporte final y la secuencia realizada. Los .txt son la salida real de la tabla
del script, no una captura reconstruida. La prueba R3 usa dos entradas del mismo
router: la primera con clave deliberadamente incorrecta y la segunda con clave válida;
el código de salida 1 de esa prueba es el esperado. No se publican sus claves.

Durante el diagnóstico hubo un timeout por carga de la VM y una incompatibilidad
de comentarios con tildes en la consola. Se usó el nombre ASCII en el comentario,
se corrigió el parser para comentarios sin comillas y rutas dinámicas sin índice,
y se ampliaron los tiempos de conexión. La secuencia de entrega indicada arriba
se completó después de esos ajustes. No hay reintentos que oculten errores.
El Cisco opcional quedó detenido para liberar CPU durante las pruebas.

## Pruebas automáticas

`python -m unittest discover -s tests -v`: **18 pruebas correctas en Windows y 18
en Debian/WSL**. Cubren parsers, flags, interfaces sin IP, rutas dinámicas sin índice,
comentarios reales sin comillas, validación, cierre de sesión, continuidad tras errores,
idempotencia, recuperación parcial y rechazo de objetos ajenos o bridges con puertos.
Estas pruebas usan fixtures; la evidencia SSH real está separada.

## Alcance y reproducción

El proyecto GNS3 incluye Cisco 7200, MikroTik, switch, Cloud, PC1 y PC2. El cliente
Netmiko utiliza la administración Host-only; la WAN MikroTik usa el NAT existente.
El Cisco multivendor y la demo de rutas/NAT entre PC1 y PC2 de los apuntes son extras:
no se presentan como verificados. No forman parte de R1-R6 del enunciado.
La práctica Ansible de Semana 5 es independiente.

El .gns3 describe nodos y enlaces; no incluye imágenes propietarias ni los discos
de las VM. La configuración y credenciales del router privado residen en el GNS3
local. Para reproducir en otra máquina se requieren las imágenes, configurar SSH y
ajustar el inventario a un equipo autorizado. En esta laptop puede usarse el auxiliar
ejecutar_local_windows.py con la clave DPAPI excluida de Git.
