package org.tmforum.oda.canvas.portal.configuration;

import java.util.List;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.LocaleResolver;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.tmforum.oda.canvas.portal.infrastructure.MapRequestParamMethodArgumentResolver;

@Configuration
public class WebConfiguration {

    @Bean
    public LocaleResolver localeResolver() {
        return new org.tmforum.oda.canvas.portal.infrastructure.LocaleResolver();
    }

    @Configuration
    static class CanvasPortalWebMvcConfigurer implements WebMvcConfigurer {

        @Override
        public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
            resolvers.add(new MapRequestParamMethodArgumentResolver());
        }
    }
}
