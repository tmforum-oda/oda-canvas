#buildx is required for this to work
#docker build -t tmforumodacanvas/compcrdwebhook.3 -t tmforumodacanvas/compcrdwebhook:latest -f webhook-dockerfile .
#docker push tmforumodacanvas/compcrdwebhook --all-tags

# The following uses buildx to build for multiple platforms (*nix/amd64 and arm64)
# please read this as well https://github.com/docker/buildx/issues/59 , doesn't change much but it's good to know
docker buildx build -t "tmforumodacanvas/compcrdwebhook:0.5.1" --platform "linux/amd64,linux/arm64" -f webhook-dockerfile . --push
