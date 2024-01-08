FROM bellsoft/liberica-openjre-alpine:17.0.9

ARG USERNAME=zpaas
ARG HOMEDIR=/app

RUN addgroup -g 1810 -S $USERNAME \
    && mkdir $HOMEDIR  \
    && adduser $USERNAME -u 1810  -h /app -D -s /bin/sh $USERNAME -G $USERNAME

USER $USERNAME
COPY --chown=$USERNAME:$USERNAME ./portal-service*.jar $HOMEDIR/lib/
COPY --chown=$USERNAME:$USERNAME ./lib/*.jar $HOMEDIR/lib/thirdlib/
COPY --chown=$USERNAME:$USERNAME ./classes/config/application.properties $HOMEDIR/conf/

WORKDIR $HOMEDIR

ENV HELM_CACHE_HOME=$HOMEDIR/helm-client/.cache/helm
ENV HELM_CONFIG_HOME=$HOMEDIR/helm-client/.config/helm
ENV HELM_DATA_HOME=$HOMEDIR/helm-client/.local/share/helm

ENTRYPOINT ["java", "--add-opens", "java.base/java.lang=ALL-UNNAMED", \
            "-DAPP_NAME=oda-dashboard", "-Dspring.config.location=/app/conf/application.properties", \
            "-cp", "/app/lib/*:/app/lib/thirdlib/*", "org.tmforum.oda.canvas.portal.CanvasPortalApplication"]