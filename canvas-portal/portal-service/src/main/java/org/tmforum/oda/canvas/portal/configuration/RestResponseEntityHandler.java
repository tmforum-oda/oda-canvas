package org.tmforum.oda.canvas.portal.configuration;

import java.util.HashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpResponse;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.CoreExceptionErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.ErrorMessage;

@RestControllerAdvice
public class RestResponseEntityHandler extends ResponseEntityExceptionHandler implements ResponseBodyAdvice {
    public static final HttpStatus DEFAULT_HTTP_STATUS;
    protected final Logger logger;
    protected Map<String, Integer> httpStatusMap;

    public RestResponseEntityHandler() {
        this(new HashMap(0));
    }

    public RestResponseEntityHandler(Map<String, Integer> httpStatusMap) {
        this.logger = LoggerFactory.getLogger(this.getClass());
        this.httpStatusMap = httpStatusMap;
    }

    @ExceptionHandler({BaseAppException.class})
    public ResponseEntity<BaseAppException> handleMyException(BaseAppException ex) {
        logger.error(ex.getMessage(), ex);
        return new ResponseEntity(new ErrorMessage(ex.getCode(), ex.getMessage()), DEFAULT_HTTP_STATUS);
    }

    @ExceptionHandler({Exception.class})
    public ResponseEntity<Exception> handleException(Exception ex) {
        logger.error(ex.getMessage(), ex);
        return new ResponseEntity(new ErrorMessage(CoreExceptionErrorCode.UNKNOWN.toString(), ""), DEFAULT_HTTP_STATUS);
    }

    static {
        DEFAULT_HTTP_STATUS = HttpStatus.INTERNAL_SERVER_ERROR;
    }

    @Override
    public boolean supports(MethodParameter returnType, Class converterType) {
        return true;
    }

    @Override
    public Object beforeBodyWrite(Object body, MethodParameter returnType, MediaType selectedContentType, Class selectedConverterType, ServerHttpRequest request, ServerHttpResponse response) {
        if (body == null && response instanceof ServletServerHttpResponse) {
            int status = ((ServletServerHttpResponse) response).getServletResponse().getStatus();
            if (status == HttpStatus.OK.value()) {
                response.setStatusCode(HttpStatus.NO_CONTENT);
                this.logger.debug("Response body is null and status is 200, set status to no_content.");
            }
        }

        return body;
    }
}
