package org.tmforum.oda.canvas.portal.core.util;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JavaType;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.Module;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.module.SimpleModule;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Collections;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.apache.commons.lang3.math.NumberUtils;

public abstract class JsonUtil {
    private static final String DEFAULT_OBJECT_MAPPER = "default";
    private static final int CACHE_SIZE = 10;
    private static final Module CUSTOM_MODULE = new CustomModule();
    private static Map<String, ObjectMapper> cachedObjectMapper = Collections.synchronizedMap(new LinkedHashMap<String, ObjectMapper>() {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, ObjectMapper> eldest) {
            return this.size() > 10;
        }
    });

    public JsonUtil() {
    }

    private static ObjectMapper instance() {
        if (cachedObjectMapper.get("default") != null) {
            return (ObjectMapper) cachedObjectMapper.get("default");
        } else {
            ObjectMapper ret = new ObjectMapper();
            ret.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
            ret.registerModule(CUSTOM_MODULE);
            cachedObjectMapper.put("default", ret);
            return ret;
        }
    }

    private static ObjectMapper instance(String datePattern) {
        if (datePattern.isEmpty()) {
            return instance();
        } else if (cachedObjectMapper.get(datePattern) != null) {
            return (ObjectMapper)cachedObjectMapper.get(datePattern);
        } else {
            ObjectMapper ret = new ObjectMapper();
            ret.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
            ret.setDateFormat(new SimpleDateFormat(datePattern));
            cachedObjectMapper.put(datePattern, ret);
            return ret;
        }
    }

    public static String object2Json(Object object) throws BaseAppException {
        try {
            return instance().writeValueAsString(object);
        } catch (JsonProcessingException var2) {
            //ExceptionHandler.publish("7071005", var2);
            return null;
        }
    }

    public static String object2Json(Object object, String datePattern) throws BaseAppException {
        try {
            return instance(datePattern).writeValueAsString(object);
        } catch (JsonProcessingException var3) {
            // FIXME
           /* ExceptionHandler.publish("7071005", var3);
            return null;*/
        }
        return datePattern;
    }

    public static <T> T json2Object(String json, Class<T> valueType) throws BaseAppException {
        try {
            return instance().readValue(json, valueType);
        } catch (IOException var3) {
            // FIXME
           /* ExceptionHandler.publish("7071004", var3);
            return null;*/
        }
        return null;
    }

    public static <T> T json2Object(String json, Class<T> valueType, String datePattern) throws BaseAppException {
        try {
            return instance(datePattern).readValue(json, valueType);
        } catch (IOException var4) {
            /*ExceptionHandler.publish("7071004", var4);
            return null;*/
        }
        return null;
    }

    public static <K, V> String map2Json(Map<K, V> map) throws BaseAppException {
        try {
            return instance().writeValueAsString(map);
        } catch (JsonProcessingException var2) {
            /*ExceptionHandler.publish("7071005", var2);
            return null;*/
        }
        return null;
    }

    public static <K, V> String map2Json(Map<K, V> map, String datePattern) throws BaseAppException {
        try {
            return instance(datePattern).writeValueAsString(map);
        } catch (JsonProcessingException var3) {
            // FIXME
            /*ExceptionHandler.publish("7071005", var3);
            return null;*/
        }
        return datePattern;
    }

    public static <K, V> Map<K, V> json2Map(String json) throws BaseAppException {
        try {
            return (Map) instance().readValue(json, Map.class);
        } catch (IOException var2) {
            // FIXME
           /* ExceptionHandler.publish("7071004", var2);
            return null;*/
        }
        return null;
    }

    public static <K, V> Map<K, V> json2Map(String json, String datePattern) throws BaseAppException {
        try {
            return (Map) instance(datePattern).readValue(json, Map.class);
        } catch (IOException var3) {
            //FIXME
           /* ExceptionHandler.publish("7071004", var3);
            return null;*/
        }
        return null;
    }

    public static <T> String list2Json(List<T> list) throws BaseAppException {
        try {
            return instance().writeValueAsString(list);
        } catch (JsonProcessingException var2) {
            //FIXME
            /*ExceptionHandler.publish("7071005", var2);
            return null;*/
        }
        return null;
    }

    public static <T> String list2Json(List<T> list, String datePattern) throws BaseAppException {
        try {
            return instance(datePattern).writeValueAsString(list);
        } catch (JsonProcessingException var3) {
            // FIXME
           /* ExceptionHandler.publish("7071005", var3);
            return null;*/
        }
        return datePattern;
    }

    public static <T> List<T> json2List(String json) throws BaseAppException {
        try {
            return (List)instance().readValue(json, List.class);
        } catch (IOException var2) {
            // FIXME
            /*ExceptionHandler.publish("7071004", var2);
            return null;*/
        }
        return null;
    }

    public static <T> List<T> json2List(String json, String datePattern) throws BaseAppException {
        try {
            return (List)instance(datePattern).readValue(json, List.class);
        } catch (IOException var3) {
            // FIXME
           /* ExceptionHandler.publish("7071004", var3);
            return null;*/
        }
        return null;
    }

    public static <T> List<T> json2List(String json, Class<T> valueType) throws BaseAppException {
        ObjectMapper mapper = instance();
        JavaType javaType = mapper.getTypeFactory().constructParametricType(List.class, new Class[]{valueType});

        try {
            return (List)mapper.readValue(json, javaType);
        } catch (IOException var5) {
            /*ExceptionHandler.publish("7071004", var5);
            return null;*/
        }
        return null;
    }

    public static <T> List<T> json2List(String json, Class<T> valueType, String datePattern) throws BaseAppException {
        ObjectMapper mapper = instance(datePattern);
        JavaType javaType = mapper.getTypeFactory().constructParametricType(List.class, new Class[]{valueType});

        try {
            return (List)mapper.readValue(json, javaType);
        } catch (IOException var6) {
           /* ExceptionHandler.publish("7071004", var6);
            return null;*/
        }
        return null;
    }

    private static class CustomModule extends SimpleModule {
        private static final long serialVersionUID = 1L;

        CustomModule() {
            this.addDeserializer(Date.class, new CustomDateJsonDeserializer());
        }
    }

    private static class CustomDateJsonDeserializer extends JsonDeserializer<Date> {
        private CustomDateJsonDeserializer() {
        }

        @Override
        public Date deserialize(JsonParser jsonParser, DeserializationContext deserializationContext) throws IOException {
            String dateString = jsonParser.getText();
            return NumberUtils.isCreatable(dateString) ? new Date(NumberUtils.toLong(dateString)) : DateUtil.formatDateWithAuto(dateString);
        }
    }
}
