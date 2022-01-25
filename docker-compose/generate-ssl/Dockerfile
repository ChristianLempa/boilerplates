FROM golang

RUN git clone https://github.com/FiloSottile/mkcert
WORKDIR mkcert
RUN go build -ldflags "-X main.Version=$(git describe --tags)"

ENTRYPOINT [ "./mkcert"]