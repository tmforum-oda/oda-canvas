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
     * 从JSON字符串获取指定路径的数据
     *
     * @param jsonPath 查找的路径
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
     * 查找满足条件的第一条数据
     *
     * @param jsonPath 查找的路径
     */
    @SuppressWarnings({"rawtypes", "unchecked"})
    public <T> T findOne(String jsonPath) throws BaseAppException {
        T result = find(jsonPath);
        if (result instanceof List) {
            if (result == null || ((List<?>) result).isEmpty()) {
                return null;
            }
            return (T) ((List) result).get(0);
        }
        return result;
    }

    /**
     * 将搜索到的数据转换成指定的对象
     *
     * @param jsonPath 查找的路径
     * @param type     要转换成的对象
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
