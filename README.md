# Laboratorio 1 - Redes Programables

Avance de clase del 6 de octubre de 2026. Alcance de hoy: R1-R3.
R4 (estado estructurado), R5 (JSON y tabla) y R6 (bridge lo-ssh-N,
idempotencia y limpieza) quedan para la siguiente sesion.

## Avance implementado

- R1: inventario externo con nombre, host, device_type, usuario y rol; validacion antes de conectar.
- R2: clave desde LAB_PASS_<NOMBRE> o getpass; ninguna clave en los archivos.
- R3: ConnectHandler dentro de with, timeout, errores de autenticacion y otros errores por equipo; logs por nombre.
- El script solo abre y cierra sesiones SSH. No aplica configuraciones.

Entorno propio env/ preparado con Netmiko 4.8.0 y PyYAML 6.0.3.
Inventario validado y sintaxis Python comprobada. El host 10.60.30.202:22 responde.
Prueba real con una clave intencionalmente incorrecta: error de autenticacion SSH,
controlado por el script (codigo de salida 1). Falta probar autenticacion exitosa
con la clave del laboratorio ingresada localmente por el estudiante.
Pruebas simuladas adicionales verificaron cierre de sesiones y continuidad tras errores.
No se incluye reporte_estado.json porque corresponde a R4-R5 y debe salir de una ejecucion real.

## Instalacion en Linux (equipo externo a GNS3)

El enunciado pide Linux, VM o WSL2 para ejecutar el script.
Debian en WSL esta disponible en este equipo. El entorno env-linux/ se creo
y sus dependencias se instalaron; --validar paso desde Linux.
Ubuntu no dispone de ensurepip.

~~~bash
python3 -m venv env-linux
source env-linux/bin/activate
python -m pip install -r requirements.txt
python lab1_inventario.py --validar
python lab1_inventario.py
~~~

Si no define la variable de entorno, getpass pide la clave sin mostrarla.
El equipo mt-lab usa LAB_PASS_MT_LAB. Obtenga la clave del profesor;
no la guarde en archivos ni la escriba en Git. Confirme primero la IP y usuario:
10.60.30.202 y lab-ssh son los datos del ejemplo. estudiante permanece null hasta
confirmar el numero de lista; no se usa para esta primera etapa.

## Ejecutar la prueba exitosa en Linux/WSL

Desde PowerShell en la carpeta del laboratorio:

~~~powershell
wsl -d Debian -- env-linux/bin/python lab1_inventario.py
~~~

La clave se ingresa localmente cuando getpass la solicita.

## Ejecutar la prueba exitosa en Windows

Desde la carpeta del laboratorio, en PowerShell:

~~~powershell
.\env\Scripts\python.exe .\lab1_inventario.py
~~~

Ingrese la clave cuando getpass la solicite; no se muestra ni se guarda en Git.
El resultado esperado es mt-lab | 10.60.30.202 | ok.
Esta comprobacion permanece pendiente hasta ejecutarla con la clave correcta.

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
Consola MikroTik accesible en 192.168.56.107:5002; RouterOS 7.20.8 solicita login.
El host del inventario responde por SSH; falta autenticacion exitosa.
No se ha confirmado que ese host corresponda al router local ni la conectividad entre PCs.
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
El avance R1-R3 y la topologia se publicaron en la rama main mediante Git local.
No se envio invitacion al profesor.

## Uso de IA

Se uso Codex para revisar el enunciado y los apuntes, preparar R1-R3,
validar el inventario, conectar la topologia mediante la API local de GNS3 e
importar la imagen Cisco proporcionada. El estudiante debe revisar y poder
explicar el codigo en la defensa. No se genero evidencia de conexiones inexistentes.
