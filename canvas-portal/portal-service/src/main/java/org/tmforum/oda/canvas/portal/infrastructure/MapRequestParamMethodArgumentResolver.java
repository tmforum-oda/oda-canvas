package org.tmforum.oda.canvas.portal.infrastructure;

import java.util.Arrays;
import java.util.stream.Collectors;

import org.springframework.core.MethodParameter;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

/**
 * Map type, request query parameter parsing, such as labelSelector=a=b,c=d
 */
public class MapRequestParamMethodArgumentResolver implements HandlerMethodArgumentResolver {

    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        return parameter.hasParameterAnnotation(MapRequestParam.class);
    }

    @Override
    public Object resolveArgument(MethodParameter parameter, ModelAndViewContainer mavContainer, NativeWebRequest webRequest, WebDataBinderFactory binderFactory) {
        String[] paramValues = webRequest.getParameterValues(parameter.getParameterAnnotation(MapRequestParam.class).name());
        if (paramValues != null) {
            return Arrays.stream(paramValues[0].split(",")).collect(Collectors.toMap(x -> x.split("=")[0], x -> x.split("=")[1]));
        }
        return null;
    }

}
