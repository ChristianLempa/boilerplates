#!/bin/bash
# Bash File for use local docker 

clear
cd $(pwd)
#app config
app=fastapi

#docker commands
if [ $(docker ps -a | grep -c $app) -gt 0 ] 
then
   echo " cleanup..."
   docker stop $app-container
   docker rm $app-container
   docker image prune -f
   echo $(pwd)
   docker build -t $-image .
fi
echo " starting container..."
docker run --name $app-container -v .:/code -p 8080:8080 $app-image
echo " running"
docker ps | grep $app