package org.tmforum.oda.canvas.portal.core.exception;


public final class ExceptionPublisher {

    private ExceptionPublisher() {

    }

    public static void publish(Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(null, null, errorCode, params);
    }

    public static void publish(BaseAppException e) throws BaseAppException {
        throw e;
    }

    public static void publish(String msg, Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(msg, null, errorCode, params);
    }

    public static void publish(Throwable t, Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(null, t, errorCode, params);
    }

    public static void publish(String msg, Throwable t, Object errorCode, Object... params) throws BaseAppException {
        BaseAppException baseAppException = new BaseAppException();
        baseAppException.setCode((errorCode.toString()));
        String errorMessage = I18nUtils.getMessage(errorCode.toString(), params);
        baseAppException.setMessage(errorMessage == null ? msg : errorMessage);
        throw baseAppException;
    }

    public static BaseAppException build(String msg, Throwable t, Object errorCode, Object... params) {
        try {
            ExceptionPublisher.publish(msg, t, errorCode, params);
        }
        catch (BaseAppException e) {
            return e;
        }
        return null;
    }

    public static BaseAppException build(Object errorCode, Object... params) {
        return build(null, null, errorCode, params);
    }

    private static String convert(Object errorCode) {
        if (errorCode instanceof String) {
            return (String) errorCode;
        }
        return errorCode == null ? null : errorCode.toString();
    }
}
