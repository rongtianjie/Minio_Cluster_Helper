@echo off
docker run -it --name cluster_helper --restart always -v %cd%:/app -p 12030:12030 cluster_helper:latest
pause