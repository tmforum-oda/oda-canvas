# get compreg-manager

```
CID=compreg-client
ATOK=$(curl -s --request POST   --url $KCURL/auth/realms/master/protocol/openid-connect/token   --header 'content-type: application/x-www-form-urlencoded'   --data client_id=admin-cli   --data grant_type=password   --data username=$USER   --data password=$PW | jq -r .access_token)
curl -sX GET -H "Authorization: Bearer $ATOK" $KCURL/auth/admin/realms/odari/clients  | jq -r ".[] | select(.clientId==\"$CID\").secret"
```

