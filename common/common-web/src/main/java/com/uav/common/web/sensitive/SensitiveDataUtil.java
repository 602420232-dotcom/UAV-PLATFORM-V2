package com.uav.common.web.sensitive;

import java.lang.reflect.Field;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 敏感数据脱敏工具类。
 * <p>
 * 提供基于正则表达式的日志脱敏能力，可在日志输出前对字符串中的
 * 手机号、邮箱、身份证号等敏感信息进行自动替换。
 */
public final class SensitiveDataUtil {

    private SensitiveDataUtil() {
    }

    // ---- 正则模式 ----

    /** 中国大陆手机号：1开头，11位 */
    private static final Pattern PHONE_PATTERN = Pattern.compile("(1[3-9]\\d)(\\d{4})(\\d{4})");

    /** 邮箱地址 */
    private static final Pattern EMAIL_PATTERN = Pattern.compile("(\\w)(\\w*)(\\w)(@\\w[\\w.-]+\\.[a-zA-Z]{2,})");

    /** 身份证号：15位或18位 */
    private static final Pattern ID_CARD_PATTERN = Pattern.compile("(\\d{3})(\\d{11})(\\d{4})");

    /** 银行卡号：连续13-19位数字 */
    private static final Pattern BANK_CARD_PATTERN = Pattern.compile("(\\d{4})(\\d{8,15})(\\d{4})");

    /**
     * 对字符串中的敏感数据进行脱敏。
     * <p>
     * 使用正则表达式匹配并替换手机号、邮箱、身份证号、银行卡号。
     *
     * @param text 原始文本
     * @return 脱敏后的文本
     */
    public static String desensitize(String text) {
        if (text == null || text.isEmpty()) {
            return text;
        }
        String result = text;
        result = PHONE_PATTERN.matcher(result).replaceAll("$1****$3");
        result = EMAIL_PATTERN.matcher(result).replaceAll("$1****$3$4");
        result = ID_CARD_PATTERN.matcher(result).replaceAll("$1***********$3");
        result = BANK_CARD_PATTERN.matcher(result).replaceAll("$1********$3");
        return result;
    }

    /**
     * 对对象进行反射脱敏。
     * <p>
     * 扫描对象所有字段，对标注了 {@link Sensitive} 注解的字段进行脱敏。
     * 注意：此方法会修改传入对象的字段值，请确保在日志输出后恢复或使用副本。
     *
     * @param obj 待脱敏的对象
     * @return 脱敏后的对象（同一个对象实例）
     */
    public static Object desensitizeObject(Object obj) {
        if (obj == null) {
            return null;
        }
        Class<?> clazz = obj.getClass();
        for (Field field : clazz.getDeclaredFields()) {
            Sensitive sensitive = field.getAnnotation(Sensitive.class);
            if (sensitive != null && field.getType() == String.class) {
                field.setAccessible(true);
                try {
                    String value = (String) field.get(obj);
                    if (value != null) {
                        field.set(obj, sensitive.strategy().desensitize(value));
                    }
                } catch (IllegalAccessException e) {
                    // 忽略无法访问的字段
                }
            }
        }
        return obj;
    }
}
