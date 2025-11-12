#!/bin/sh


echo "delete API: self:r-cat-productcatalogmanagement:metrics"
curl -X 'DELETE' \
  'http://localhost:8080/resource/self%3Ar-cat-productcatalogmanagement%3Ametrics' \
  -H 'accept: */*'
  
  
echo "delete API: self:r-cat-productcatalogmanagement:partyrole"
curl -X 'DELETE' \
  'http://localhost:8080/resource/self%3Ar-cat-productcatalogmanagement%3Apartyrole' \
  -H 'accept: */*'
  
  
echo "delete API: self:r-cat-productcatalogmanagement:productcatalogmanagement"
curl -X 'DELETE' \
  'http://localhost:8080/resource/self%3Ar-cat-productcatalogmanagement%3Aproductcatalogmanagement' \
  -H 'accept: */*'
  

echo "delete ODAComponent: self:r-cat-productcatalogmanagement"
curl -X 'DELETE' \
  'http://localhost:8080/resource/self%3Ar-cat-productcatalogmanagement' \
  -H 'accept: */*'
  

echo "delete hub localdev80"
curl -X 'DELETE' \
  'http://localhost:8080/hub/localdev80' \
  -H 'accept: */*'
  
