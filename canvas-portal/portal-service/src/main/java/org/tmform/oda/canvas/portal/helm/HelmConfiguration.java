package org.tmform.oda.canvas.portal.helm;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.tmform.oda.canvas.portal.helm.HelmProperties;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.HelmClientConfig;

import com.google.common.base.Joiner;

@Configuration
@EnableConfigurationProperties(HelmProperties.class)
public class HelmConfiguration {

    @Bean
    public HelmClient helmClient(HelmProperties helmProperties) throws BaseAppException {
        HelmClient.HelmClientBuilder builder = HelmClient.builder();
        builder.helmClientConfig(HelmClientConfig.builder()
                .kubeConfig(helmProperties.getKubeconfig())
                .kubeInsecureSkipTlsVerify(helmProperties.isKubeInsecureSkipTlsVerify()).build());
        HelmClient helmClient = builder.build();
        // do helm repo add
        helmClient.repos().add(Joiner.on("-").join("tmfoda", helmProperties.getReponame()),
                helmProperties.getUrl(), helmProperties.getUsername(),
                helmProperties.getPassword(), true);
        return helmClient;
    }

}
