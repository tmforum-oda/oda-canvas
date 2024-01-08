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


/**
 * 对JSON-Path做一层简单封装：</br>
 * 1. 使用Jackson作为JSON引擎,以便支持从JSON转换成对象</br>
 * 2. 限制可用的API，简化使用</br>
 * 3. 做一些增强</br>
 * 参考：
 * http://www.baeldung.com/guide-to-jayway-jsonpath
 * https://github.com/jayway/JsonPath
 *
 * @author li.peilong
 */
public abstract class JsonPathUtil {
    // 使用Jackson
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
                // 路径不存在不抛异常，返回null
                options.add(Option.DEFAULT_PATH_LEAF_TO_NULL);
                return options;
            }
        });
    }

    /**
     * 查找指定路径的数据
     *
     * @param json     JSON数据
     * @param jsonPath 要查找的路径
     */
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

    /**
     * 查找满足条件的第一条数据
     *
     * @param json     JSON数据
     * @param jsonPath 要查找的路径
     */
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

    /**
     * 查找满足条件的第一条数据,支持设置默认值
     *
     * @param json
     * @param jsonPath
     * @param defaultVal
     */
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

    /**
     * 查询指定路径整数
     *
     * @param json
     * @param jsonPath
     * @return
     * @throws BaseAppException
     */
    public static Integer findInteger(String json, String jsonPath) throws BaseAppException {
        Object result = findOne(json, jsonPath);
        if (result == null) {
            return null;
        }
        return Integer.parseInt(result.toString());
    }

    /**
     * 查询指定路径整数，支持默认值
     *
     * @param json
     * @param jsonPath
     * @param defaultValue
     * @return
     * @throws BaseAppException
     */
    public static Integer findInteger(String json, String jsonPath, int defaultValue) throws BaseAppException {
        Object result = findOne(json, jsonPath);
        if (result == null) {
            return defaultValue;
        }
        return Integer.parseInt(result.toString());
    }

    /**
     * 将搜索到的数据转换成指定的对象
     *
     * @param json
     * @param jsonPath
     * @param type
     */
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

    /**
     * 查找枚举值
     *
     * @param json
     * @param jsonPath
     * @param type
     * @param <T>
     * @return
     * @throws BaseAppException
     */
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
        // 先提取出所需要的的数据
        List list = JsonPathUtil.find(data, jsonPath);
        // 转换成需要的对象
        return JsonUtil.json2List(JsonUtil.list2Json(list), clazz);
    }

}
