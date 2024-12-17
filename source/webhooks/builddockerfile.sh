#buildx is required for this to work
#docker build -t tmforumodacanvas/conversion-webhook.3 -t tmforumodacanvas/conversion-webhook:latest -f webhook-dockerfile .
#docker push tmforumodacanvas/conversion-webhook --all-tags

# The following uses buildx to build for multiple platforms (*nix/amd64 and arm64)
# please read this as well https://github.com/docker/buildx/issues/59 , doesn't change much but it's good to know
docker buildx build -t "tmforumodacanvas/conversion-webhook:1.0.0" --platform "linux/amd64,linux/arm64" -f webhook-dockerfile . --push
