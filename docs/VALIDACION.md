# Verificación de entrega - 19 de octubre de 2026

Este registro distingue implementación, pruebas sin red y evidencia real.
No acredita pruebas que todavía no se hayan ejecutado.

| Requisito | Implementación y verificación | Estado real |
| --- | --- | --- |
| R1 | YAML validado, campos mínimos, rol y driver | Inventario válido; falta N confirmado |
| R2 | Variables LAB_PASS_* o getpass | Comprobado en el avance del 6 de octubre |
| R3 | with, errores por equipo, session_log | SSH exitoso y fallo de autenticación del avance; pruebas de continuidad simuladas |
| R4 | Parsers y comandos por fabricante | Pruebas sin red correctas; falta nueva ejecución SSH |
| R5 | Lista JSON y tabla | Pruebas sin red correctas; falta reporte final real |
| R6 | Consulta/creación/verificación/limpieza con propietario | Pruebas sin red correctas; falta N y demo real |
| Documentación | Instalación, entorno, CLI, seguridad, declaración de IA | README actualizado |
| Colaborador | randthat invitado/aceptado | No confirmado |
| Extra Cisco | Comandos y parser preparados | Extra opcional no acreditado por pruebas sin red |

Prueba automática ejecutada: python -m unittest discover -s tests -v.
Resultado: 15 pruebas correctas en Windows y 15 en Debian/WSL; inventario validado
también desde Linux. No conecta ni escribe a routers.

Para cerrar los pendientes de ejecución real:

1. Confirmar N con el profesor y completar estudiante en inventario.yaml.
2. Confirmar acceso SSH y clave local al MikroTik autorizado.
3. Ejecutar verificar_entrega.py desde Linux/VM/WSL.
4. Revisar evidencias/ejecucion_real/ y reporte_estado.json: todos con estado ok.
5. Revisar/sanitizar logs antes de publicarlos; omitir avisos de accesos de terceros.
6. Verificar la invitación a randthat y publicar los resultados reales con otro commit.

La topología local y el laboratorio compartido son entornos distintos.
La demo de rutas estáticas de los apuntes no equivale al bridge de R6.
