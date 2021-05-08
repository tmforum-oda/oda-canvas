docker build -t lesterthomas/compcrdwebhook:0.3 -t lesterthomas/compcrdwebhook:latest -f webhook-dockerfile . 
docker push lesterthomas/compcrdwebhook --all-tags
