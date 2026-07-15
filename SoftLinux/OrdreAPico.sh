#!/bin/bash
# Guy 19/06/2026 CarbetBox
# recois des ordres en parametres et les envoie a PicoBox
# utile pour cron qui utilise dash
# seul bash connait /dev/tcp/localhost/12345
# passer l'ordre en parameter

if [ $# -eq 0 ]
  then
    echo "No arguments supplied! EXIT!"
    exit
fi

printf "$1" > /dev/tcp/localhost/12345
