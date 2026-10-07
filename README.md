# Laboratorio 1 - Redes Programables

Avance de clase del 6 de octubre de 2026. Alcance de hoy: R1-R3.
R4 (estado estructurado), R5 (JSON y tabla) y R6 (bridge lo-ssh-N,
idempotencia y limpieza) quedan para la siguiente sesion.

## Avance implementado

- R1: inventario externo con nombre, host, device_type, usuario y rol; validacion antes de conectar.
- R2: clave desde LAB_PASS_<NOMBRE> o getpass; ninguna clave en los archivos.
- R3: ConnectHandler dentro de with, timeout, errores de autenticacion y otros errores por equipo; logs por nombre.
- El script solo abre y cierra sesiones SSH. No aplica configuraciones.

Implementacion revisada con Netmiko 4.8.0 y PyYAML 6.0.3 en el entorno de Semana 3.
Inventario validado y sintaxis Python comprobada. La conexion SSH real aun no esta verificada.
No se incluye reporte_estado.json porque corresponde a R4-R5 y debe salir de una ejecucion real.

## Instalacion en Linux (equipo externo a GNS3)

El enunciado pide Linux, VM o WSL2 para ejecutar el script.

~~~bash
python3 -m venv env
source env/bin/activate
python -m pip install -r requirements.txt
python lab1_inventario.py --validar
python lab1_inventario.py
~~~

Si no define la variable de entorno, getpass pide la clave sin mostrarla.
El equipo mt-lab usa LAB_PASS_MT_LAB. Obtenga la clave del profesor;
no la guarde en archivos ni la escriba en Git. Confirme primero la IP y usuario:
10.60.30.202 y lab-ssh son los datos del ejemplo. estudiante permanece null hasta
confirmar el numero de lista; no se usa para esta primera etapa.

## Prueba de errores en clase

Ejecutar con una clave incorrecta debe mostrar error: autenticacion SSH.
Con un host inaccesible debe mostrar error: tiempo de espera SSH.
Para demostrar continuidad, usar un inventario temporal con dos equipos autorizados,
el primero inaccesible y el segundo real; pasar --inventario ruta.yaml.
El script debe intentar ambos y devolver codigo 1 si hubo algun error.
Las sesiones generan logs/<nombre>.log. Se ignoran en Git por contener informacion
sensible; revisar y sanitizar antes de compartir evidencia.

## Topologia GNS3

El proyecto Lab01.gns3 contiene:

~~~text
Internet (eth1) -- SW1 (Ethernet0)
SW1 (Ethernet1) -- MikroTik (ether1)
MikroTik (ether2) -- PC2
SW1 (Ethernet2) -- Cisco (FastEthernet0/0)
Cisco (FastEthernet1/0) -- PC1
~~~

Cisco: 7200 NPE-400, 512 MB, C7200-IO-FE + PA-FE-TX, ejecutado en GNS3 VM.
Imagen importada desde el archivo proporcionado por el estudiante:
c7200-adventerprisek9-mz.124-24.T5.image.
MD5 verificado: 6b89d0d804e1f2bb5b8bda66b5692047.
GNS3 confirmo el arranque del Cisco y del MikroTik; los enlaces estan guardados.
La consola TCP no pudo verificarse desde este entorno por restriccion de acceso.
Las IP, SSH y conectividad entre PCs quedan sin confirmar.
El enunciado usa Cisco 3725, pero se agrego 7200 por solicitud del estudiante.
El extra multivendor no esta habilitado. La LAN del MikroTik usa ether2 en este
proyecto; ether8 en los apuntes pertenece a otra cantidad de adaptadores.
No se configuraron rutas estaticas ni excepciones NAT de los apuntes: son una
referencia adicional y no sustituyen R6 del laboratorio.

Las imagenes IOS y discos de maquinas no se suben al repositorio.
El archivo .gns3 describe la topologia; requiere GNS3 VM y las imagenes instaladas.

## Pendiente para continuar otro dia

1. Confirmar numero de lista, nombre y datos de acceso; probar SSH y errores reales.
2. Completar R4 y R5: parsers de los cuatro datos, comandos por fabricante, JSON y tabla.
3. Completar R6: consultar, crear solo lo propio, verificar, segunda ejecucion sin cambios y --limpiar.

El avance de clase solicitado por el enunciado es R1-R3 funcionando con push.
La implementacion local por si sola no demuestra una conexion real ni reemplaza el push.
El repositorio indicado es https://github.com/Raul-QM/Lab01-Redes.
El conector disponible tiene solo lectura y Git local no alcanzo github.com;
la publicacion quedo pendiente. No se envio invitacion al profesor.

## Uso de IA

Se uso Codex para revisar el enunciado y los apuntes, preparar R1-R3,
validar el inventario, conectar la topologia mediante la API local de GNS3 e
importar la imagen Cisco proporcionada. El estudiante debe revisar y poder
explicar el codigo en la defensa. No se genero evidencia de conexiones inexistentes.
