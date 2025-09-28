FROM ubuntu:latest
LABEL authors="kirillkiselev"

ENTRYPOINT ["top", "-b"]