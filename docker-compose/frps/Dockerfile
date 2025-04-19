FROM alpine:latest

RUN apk add --no-cache wget tar

ENV FRP_VERSION 0.59.0

RUN wget https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_amd64.tar.gz \
    && tar -xzf frp_${FRP_VERSION}_linux_amd64.tar.gz \
    && mv frp_${FRP_VERSION}_linux_amd64 /frp \
    && rm frp_${FRP_VERSION}_linux_amd64.tar.gz

EXPOSE 7000 7500

ENTRYPOINT ["/frp/frps", "-c", "/frp/frps.toml"]
