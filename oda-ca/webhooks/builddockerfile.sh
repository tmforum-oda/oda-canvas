docker build -t lesterthomas/compcrdwebhook:0.4 -f webhook-dockerfile . 
#docker build -t tmforumodacanvas/compcrdwebhook:0.3 -t tmforumodacanvas/compcrdwebhook:latest -f webhook-dockerfile . 
docker push lesterthomas/compcrdwebhook --all-tags
