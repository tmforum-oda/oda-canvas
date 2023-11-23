package org.tmform.oda.canvas.portal.configuration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.LocaleResolver;

@Configuration
public class WebConfiguration {

    @Bean
    public LocaleResolver localeResolver(){
        return new org.tmform.oda.canvas.portal.configuration.LocaleResolver();
    }
}
