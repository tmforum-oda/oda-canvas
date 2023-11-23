package org.tmforum.oda.canvas.portal.core.listener;

import org.springframework.boot.SpringApplicationRunListener;
import org.springframework.context.ConfigurableApplicationContext;

import org.tmforum.oda.canvas.portal.core.util.SpringContext;

public class SpringContextListener implements SpringApplicationRunListener {

    @Override
    public void contextPrepared(ConfigurableApplicationContext context) {
        SpringContext.setApplicationContext(context);
    }
}
