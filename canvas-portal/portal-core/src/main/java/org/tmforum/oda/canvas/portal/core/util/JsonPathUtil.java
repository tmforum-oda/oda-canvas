package org.tmforum.oda.canvas.portal.core.util;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Set;

import com.alibaba.fastjson.JSON;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.CoreExceptionErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import com.jayway.jsonpath.spi.json.JacksonJsonProvider;
import com.jayway.jsonpath.spi.json.JsonProvider;
import com.jayway.jsonpath.spi.mapper.JacksonMappingProvider;
import com.jayway.jsonpath.spi.mapper.MappingProvider;

public abstract class JsonPathUtil {
    static {
        Configuration.setDefaults(new Configuration.Defaults() {

            private final JsonProvider jacksonJsonProvider = new JacksonJsonProvider();
            private final MappingProvider jacksonMappingProvider = new JacksonMappingProvider();

            @Override
            public JsonProvider jsonProvider() {
                return jacksonJsonProvider;
            }

            @Override
            public MappingProvider mappingProvider() {
                return jacksonMappingProvider;
            }

            @Override
            public Set<Option> options() {
                EnumSet<Option> options = EnumSet.noneOf(Option.class);
                options.add(Option.DEFAULT_PATH_LEAF_TO_NULL);
                return options;
            }
        });
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    public static <T> T find(String json, String jsonPath) throws BaseAppException {
        try {
            T data = JsonPath.read(json, jsonPath);
            return convert(data);
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CoreExceptionErrorCode.FAILED_PARSE_JSON_PATH, jsonPath, json);
        }
        return null;
    }

    static <T> T convert(T data) {
        if (data instanceof List) {
            List result = new ArrayList();
            for (Object obj : (List) data) {
                if (obj != null) {
                    result.add(obj);
                }
            }
            return (T) result;
        }
        return data;
    }

    public static <T> T find(Object json, String jsonPath) throws BaseAppException {
        if (json == null) {
            return null;
        }
        return find(JSON.toJSONString(json), jsonPath);
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    public static <T> T findOne(String json, String jsonPath) throws BaseAppException {
        T result = find(json, jsonPath);
        if (result instanceof List) {
            if (!((List) result).isEmpty()) {
                return (T) ((List) result).get(0);
            }
            else {
                return null;
            }
        }
        return result;
    }

    public static <T> T findOne(Object json, String jsonPath) throws BaseAppException {
        if (json == null) {
            return null;
        }
        return findOne(JSON.toJSONString(json), jsonPath);
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    public static <T> T findOne(String json, String jsonPath, T defaultVal) throws BaseAppException {
        T result = find(json, jsonPath);
        if (result instanceof List) {
            if (!((List) result).isEmpty()) {
                return (T) ((List) result).get(0);
            }
            else {
                return defaultVal;
            }
        }
        if (result == null) {
            return defaultVal;
        }
        return result;
    }

    public static Integer findInteger(String json, String jsonPath) throws BaseAppException {
        Object result = findOne(json, jsonPath);
        if (result == null) {
            return null;
        }
        return Integer.parseInt(result.toString());
    }

    public static Integer findInteger(String json, String jsonPath, int defaultValue) throws BaseAppException {
        Object result = findOne(json, jsonPath);
        if (result == null) {
            return defaultValue;
        }
        return Integer.parseInt(result.toString());
    }

    public static <T> T find(String json, String jsonPath, Class<T> type) throws BaseAppException {
        try {
            DocumentContext jsonContext = JsonPath.parse(json);
            return jsonContext.read(jsonPath, type);
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CoreExceptionErrorCode.FAILED_PARSE_JSON_PATH_TO_TYPE, jsonPath, json, type);
        }
        return null;
    }

    public static <T extends Enum<T>> T findEnum(String json, String jsonPath, Class<T> type) throws BaseAppException {
        try {
            String data = findOne(json, jsonPath);
            return Enum.valueOf(type, data);
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CoreExceptionErrorCode.FAILED_PARSE_JSON_PATH_TO_TYPE, jsonPath, json, type);
        }
        return null;
    }

    public static <T> T find(Object json, String jsonPath, Class<T> type) throws BaseAppException {
        if (json == null) {
            return null;
        }
        return find(JSON.toJSONString(json), jsonPath, type);
    }

    public static JsonFinder complie(String json) {
        return new JsonFinder(json);
    }

    public static <T> List<T> findList(String data, String jsonPath, Class<T> clazz) throws BaseAppException {
        List list = JsonPathUtil.find(data, jsonPath);
        return JsonUtil.json2List(JsonUtil.list2Json(list), clazz);
    }

}
