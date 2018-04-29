#!/bin/bash

current_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ "$EUID" != "0" ]]; then
  echo "[!] This script must be run as root." 1>&2
  exit 1
fi

if [[ $OSTYPE == "linux-gnu" ]]; then
  echo -e "\t#########################"
  echo -e "\t   linux Configuration"
  echo -e "\t#########################"

  echo "[*] Installing python..."
  apt-get install python3 python-pip -y

  echo "[*] Installing packages..."
  apt-get install geoip-bin geoip-database apache2 tcpdump screen python-pcapy bridge-utils -y

  echo "[*] Installing python libs..."
  sh "$current_path/python3-depends.sh"

  echo ""
  echo "[*] Setup Completed."
  
fi
