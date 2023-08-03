#!/bin/sh
kubectl get pods -n demo-comp
echo "expected: 3 PODs have two containers, POD democ-comp-three has only 1 container (no sidecar)" 
echo ""

echo "setting 'mysecret' in POD demoa-comp-one-sender to 'SET_BY_ONE-SENDER'"
kubectl exec -it -n demo-comp deployment/demoa-comp-one-sender -c component-implementation -- curl -s -X "POST" -d "{\"key\":\"my-secret\",\"value\":\"SET_BY_ONE-SENDER\"}" "http://localhost:5000/api/v3/secret" -H "accept: application/json" -H "Content-Type: application/json"
sleep 1
echo ""

echo "getting 'mysecret' in POD demoa-comp-one-sender"
echo "--------------------------"
kubectl exec -it -n demo-comp deployment/demoa-comp-one-sender -c component-implementation --  curl -s -X GET http://localhost:5000/api/v3/secret/my-secret -H "accept: application/json"
sleep 1
echo ""
echo "--------------------------"
echo "expected: 'SET_BY_ONE-SENDER'"
echo ""

echo "getting 'mysecret' in POD demoa-comp-one-receiver"
echo "--------------------------"
kubectl exec -it -n demo-comp deployment/demoa-comp-one-receiver -c component-implementation --  curl -s -X GET http://localhost:5000/api/v3/secret/my-secret -H "accept: application/json"
sleep 1
echo ""
echo "--------------------------"
echo "expected: 'SET_BY_ONE-SENDER'"
echo ""

echo "getting 'mysecret' in POD demob-comp-two"
echo "--------------------------"
kubectl exec -it -n demo-comp deployment/demob-comp-two -c component-implementation --  curl -s -X GET http://localhost:5000/api/v3/secret/my-secret -H "accept: application/json"
sleep 1
echo ""
echo "--------------------------"
echo "expected: empty in first run"
echo ""

echo "setting 'mysecret' in POD demob-comp-two to 'secret of B-TWO'"
kubectl exec -it -n demo-comp deployment/demob-comp-two -c component-implementation -- curl -s -X "POST" -d "{\"key\":\"my-secret\",\"value\":\"secret of B-TWO\"}" "http://localhost:5000/api/v3/secret" -H "accept: application/json" -H "Content-Type: application/json"
sleep 1
echo ""

echo "getting 'mysecret' in POD demob-comp-two"
echo "--------------------------"
kubectl exec -it -n demo-comp deployment/demob-comp-two -c component-implementation --  curl -s -X GET http://localhost:5000/api/v3/secret/my-secret -H "accept: application/json"
sleep 1
echo ""
echo "--------------------------"
echo "expected: 'secret of B-TWO'"
echo ""

echo "getting 'mysecret' in POD demoa-comp-one-sender"
echo "--------------------------"
kubectl exec -it -n demo-comp deployment/demoa-comp-one-sender -c component-implementation --  curl -s -X GET http://localhost:5000/api/v3/secret/my-secret -H "accept: application/json"
sleep 1
echo ""
echo "--------------------------"
echo "expected: 'SET_BY_ONE-SENDER'"
echo ""
