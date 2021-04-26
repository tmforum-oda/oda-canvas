docker build -t lesterthomas/compcrdwebhook:0.2 -t lesterthomas/compcrdwebhook:latest -f webhook-dockerfile . 
docker push lesterthomas/compcrdwebhook --all-tags
