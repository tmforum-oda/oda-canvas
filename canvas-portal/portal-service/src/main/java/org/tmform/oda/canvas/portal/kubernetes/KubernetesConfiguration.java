package org.tmform.oda.canvas.portal.kubernetes;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.fabric8.kubernetes.client.Config;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.KubernetesClientBuilder;

@Configuration
@EnableConfigurationProperties(KubernetesProperties.class)
public class KubernetesConfiguration {

    @Bean
    KubernetesClient kubernetesClient(KubernetesProperties kubernetesProperties) throws IOException {
        Config config = Config.fromKubeconfig(Files.readString(Paths.get(kubernetesProperties.getKubeconfig())));
        config.setMasterUrl(kubernetesProperties.getMasterUrl());
        return new KubernetesClientBuilder().withConfig(config).build();
    }
}
