# Solo el MikroTik PRIVADO del proyecto Lab01. ether1 gestion, ether2 PC2, ether3 WAN.
/system identity set name=mt-lab-local
:if ([:len [/ip address find where address="192.168.56.202/24" and interface="ether1"]] = 0) do={/ip address add address=192.168.56.202/24 interface=ether1 comment="LAB01-gestion-hostonly"}
:if ([:len [/ip address find where address="10.60.30.202/24" and interface="ether1"]] = 0) do={/ip address add address=10.60.30.202/24 interface=ether1 comment="LAB01-gestion"}
:if ([:len [/ip dhcp-client find where interface="ether3"]] = 0) do={/ip dhcp-client add interface=ether3 add-default-route=yes use-peer-dns=no disabled=no}
/ip dns set servers=8.8.8.8,1.1.1.1
/ip service enable ssh
:if ([:len [/ip address find where address="172.16.20.1/24" and interface="ether2"]] = 0) do={/ip address add address=172.16.20.1/24 interface=ether2 comment="LAB01-LAN-PC2"}
:if ([:len [/ip firewall nat find where comment="LAB01-local-internet"]] = 0) do={/ip firewall nat add chain=srcnat out-interface=ether3 action=masquerade comment="LAB01-local-internet"}
# Crear lab-ssh por consola con clave privada. Nunca guardar su password en este archivo.
