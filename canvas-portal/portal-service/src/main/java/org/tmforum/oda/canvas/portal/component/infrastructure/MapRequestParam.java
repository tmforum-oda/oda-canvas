package org.tmforum.oda.canvas.portal.component.infrastructure;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import org.springframework.core.annotation.AliasFor;

@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
public @interface MapRequestParam {
    boolean required() default true;

    @AliasFor("name")
    String value() default "";

    @AliasFor("value")
    String name() default "";

    String defaultValue() default "";
}
