set GO111MODULE=on
set CGO_ENABLED=0
go get -d -v ./...
go build -a -installsuffix cgo -o private-vault-service.exe .