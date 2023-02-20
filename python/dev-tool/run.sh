#!/bin/bash
cd "$(dirname "$0")"
clear
echo $(pwd)

#app config
app=fastapi

#docker commands
if [ $(docker ps -a | grep -c $app) -gt 0 ] 
then
   echo " cleanup..."
   docker stop $app-container
   docker rm $app-container
   #docker rmi $app-image
   #echo " building image..."
   #docker build -t $-image $(pwd)
fi
echo " starting container..."
docker run --name $app-container -v .:/code -p 8080:8080 $app-image
echo " running"
docker ps | grep $app