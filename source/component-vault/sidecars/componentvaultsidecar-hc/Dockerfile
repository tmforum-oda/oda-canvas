FROM golang:1.19 AS build
WORKDIR /go/src
COPY *.go .
COPY go.mod .
COPY go.sum .

ENV GO111MODULE=on
ENV CGO_ENABLED=0
ENV GOOS=linux
RUN go get -d -v ./...

RUN go build -a -installsuffix cgo -o component-vault-service .

FROM scratch AS runtime
# https://stackoverflow.com/questions/52969195/docker-container-running-golang-http-client-getting-error-certificate-signed-by
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build /go/src/component-vault-service ./
EXPOSE 5000/tcp
ENTRYPOINT ["./component-vault-service"]
