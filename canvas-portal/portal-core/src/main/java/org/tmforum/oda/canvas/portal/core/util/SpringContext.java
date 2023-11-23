package org.tmforum.oda.canvas.portal.core.util;

import org.springframework.context.ApplicationContext;

public class SpringContext {

    private static ApplicationContext applicationContext;

    public static void setApplicationContext(ApplicationContext applictionContext){
        SpringContext.applicationContext = applictionContext;
    }

    public static <T> T getBean(Class<T> beanClass) {
        return applicationContext.getBean(beanClass);
    }
}
