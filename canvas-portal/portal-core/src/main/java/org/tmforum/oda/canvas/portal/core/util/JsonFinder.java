package org.tmforum.oda.canvas.portal.core.util;

import java.util.List;

import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.CoreExceptionErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.JsonPath;

public class JsonFinder {
    private DocumentContext context;

    JsonFinder(String json) {
        this.context = JsonPath.parse(json);
    }

    /**
     * Retrieves data from a JSON string at a specified path.
     *
     * @param jsonPath The path to search for.
     */
    @SuppressWarnings({"unchecked", "rawtypes"})
    public <T> T find(String jsonPath) throws BaseAppException {
        try {
            T data = context.read(jsonPath);
            return JsonPathUtil.convert(data);
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CoreExceptionErrorCode.FAILED_PARSE_JSON_PATH, jsonPath, context.jsonString());
        }
        return null;
    }

    /**
     * Finds the first piece of data that matches the condition.
     *
     * @param jsonPath The path to search for.
     */
    @SuppressWarnings({"rawtypes", "unchecked"})
    public <T> T findOne(String jsonPath) throws BaseAppException {
        T result = find(jsonPath);
        if (result instanceof List) {
            if (((List<?>) result).isEmpty()) {
                return null;
            }
            return (T) ((List) result).get(0);
        }
        return result;
    }

    /**
     * Converts the found data into a specified object.
     *
     * @param jsonPath The path to search for.
     * @param type     The type of object to convert to.
     */
    public <T> T find(String jsonPath, Class<T> type) throws BaseAppException {
        try {
            return context.read(jsonPath, type);
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CoreExceptionErrorCode.FAILED_PARSE_JSON_PATH_TO_TYPE, jsonPath, context.jsonString(), type);
        }
        return null;
    }

}
