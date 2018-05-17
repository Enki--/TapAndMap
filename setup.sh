#!/bin/bash

current_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ "$EUID" != "0" ]]; then
  echo "[!] This script must be run as root." 1>&2
  exit 1
fi

# -y flag will be passed to this variable for a non-interactive setup.
SKIP=""

while getopts "y" OPTION; do
  case $OPTION in
    y)
      SKIP=" -y"
      ;;
  esac
done


if [[ $OSTYPE == "linux-gnu" ]]; then
  echo -e "\t#########################"
  echo -e "\t   linux Configuration"
  echo -e "\t#########################"

  echo "[*] Installing redis"
  apt-get -qq -y update
  apt-get -qq -y full-upgrade
  apt-get -qq -y install redis-server

  echo "[*] Installing python3..."
  apt-get -qq -y install python3

  echo "[*] Installing pip3..."
  apt-get -qq -y install python3-pip

  echo "[*] Installing python libs..."
  pip install flask-googlemaps --upgrade
  pip install redis --upgrade
  pip instal flask --upgrade
  pip install scapy --upgrade
  pip install configparser --upgrade

  echo ""
  echo "[*] Setup Completed."

else
   echo -e "Some day I will build this for non-linux systems"

fi
