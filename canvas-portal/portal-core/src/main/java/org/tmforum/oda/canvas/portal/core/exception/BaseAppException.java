package org.tmforum.oda.canvas.portal.core.exception;

import java.io.Serializable;

public class BaseAppException extends Exception implements Serializable {

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    @Override
    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    private String code;

    private String message;


}
