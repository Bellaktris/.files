#!/usr/bin/env bash

if [[ "$(id -u)" != "0" ]]; then
	echo "Run with sudo."
	exit 1
fi

ufw disable &>/dev/null
service openvpn stop &>/dev/null

TIMEZONE=$(( $(date +"%z") / 100 ))

if $(( $TIMEZONE >= -7 && $TIMEZONE <= -4 ))
then
  serverip=$(dig +short ${1:-ca.torguardvpnaccess.com})
  [[ -z $serverip ]] && serverip=${1:-ca.torguardvpnaccess.com}
else
  serverip=$(dig +short ${1:-swiss.torguardvpnaccess.com})
  [[ -z $serverip ]] && serverip=${1:-swiss.torguardvpnaccess.com}
fi  # $(( $TIMEZONE >= -7 && $TIMEZONE <= -4 ))

read -d '' vpnconf <<- EOF
client
dev tun
proto udp
nobind
remote-random
remote $serverip 443
ca torguard.crt
auth-user-pass torguard-credentials
auth-nocache
remote-cert-tls server
tun-ipv6
cipher BF-CBC
resolv-retry infinite
tun-mtu 48000
fragment 0
mssfix 0
route-delay 5 30
ping-restart 0
keepalive 5 30
comp-lzo
fast-io
mute-replay-warnings
EOF

echo "$vpnconf" >/etc/openvpn/torguard.conf
echo "AUTOSTART='torguard'" >/etc/default/openvpn
service openvpn restart &>/dev/null

# Reset the ufw config
ufw --force reset &>/dev/null

# Block all traffic by default
ufw default deny incoming &>/dev/null
ufw default deny outgoing &>/dev/null

# Every communiction via VPN is safe
ufw allow in  on tun0 &>/dev/null
ufw allow out on tun0 &>/dev/null

# Don't block the creation of the VPN tunnels
ufw allow out to $serverip    port 443 &>/dev/null
ufw allow out to 188.44.41.76 port 443 &>/dev/null

# Allow Google DNS
ufw allow out to 8.8.8.8 port 53 &>/dev/null
ufw allow out to 8.8.4.4 port 53 &>/dev/null

# Allow private network and loopback
ipv4_1=("0.0.0.0/8" "127.0.0.0/8" "224.0.0.0/4")
ipv4_2=("192.168.0.0/16" "10.0.0.0/8" "172.16.0.0/12")

ipv6=("::1/128" "fe80::/10" "fc00::/7" "ff00::/8")

for address1 in ${ipv4_1[@]} ${ipv4_2[@]}; do
for address2 in ${ipv4_1[@]} ${ipv4_2[@]}; do
  ufw allow in  from ${address1} to ${address2} &>/dev/null
  ufw allow out from ${address1} to ${address2} &>/dev/null
done; done;

for address1 in ${ipv6[@]}; do
for address2 in ${ipv6[@]}; do
  ufw allow in  from ${address1} to ${address2} &>/dev/null
  ufw allow out from ${address1} to ${address2} &>/dev/null
done; done;

ufw enable &>/dev/null  # Enable the firewall
