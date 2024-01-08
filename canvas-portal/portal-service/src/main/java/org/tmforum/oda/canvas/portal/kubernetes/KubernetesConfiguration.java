package org.tmforum.oda.canvas.portal.kubernetes;

import java.io.IOException;

import org.slf4j.LoggerFactory;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.fabric8.kubernetes.client.Config;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.KubernetesClientBuilder;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.LoggerContext;

@Configuration
@EnableConfigurationProperties(KubernetesProperties.class)
public class KubernetesConfiguration {

    private static final String HTTP_LOGGING_INTERCEPTOR_LEVEL = "HTTP_LOGGING_INTERCEPTOR_LEVEL";

    @Bean
    KubernetesClient kubernetesClient(KubernetesProperties kubernetesProperties) throws IOException {
        Config config = Config.autoConfigure(null);
        LoggerContext loggerContext = (LoggerContext) LoggerFactory.getILoggerFactory();
        Logger logger = loggerContext.getLogger("okhttp3.logging.HttpLoggingInterceptor");
        String httpLoggingInterceptorLevel = System.getenv(HTTP_LOGGING_INTERCEPTOR_LEVEL) != null ? System.getenv(HTTP_LOGGING_INTERCEPTOR_LEVEL) : "TRACE";
        logger.setLevel(Level.valueOf(httpLoggingInterceptorLevel));
        return new KubernetesClientBuilder().withConfig(config).build();
    }
}
