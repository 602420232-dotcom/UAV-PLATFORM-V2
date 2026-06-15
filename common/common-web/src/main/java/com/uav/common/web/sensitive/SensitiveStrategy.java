package com.uav.common.web.sensitive;

/**
 * 脱敏策略枚举。
 * <p>
 * 定义不同类型敏感数据的脱敏规则。
 */
public enum SensitiveStrategy {

    /** 手机号：中间4位替换为 ****，如 138****1234 */
    PHONE {
        @Override
        public String desensitize(String value) {
            if (value == null || value.length() < 7) {
                return value;
            }
            return value.substring(0, 3) + "****" + value.substring(value.length() - 4);
        }
    },

    /** 邮箱：@前部分保留首尾字符，中间用 **** 替换，如 t***e@example.com */
    EMAIL {
        @Override
        public String desensitize(String value) {
            if (value == null || !value.contains("@")) {
                return value;
            }
            int atIndex = value.indexOf("@");
            String prefix = value.substring(0, atIndex);
            String suffix = value.substring(atIndex);
            if (prefix.length() <= 1) {
                return prefix + "****" + suffix;
            }
            return prefix.charAt(0) + "****" + prefix.charAt(prefix.length() - 1) + suffix;
        }
    },

    /** 身份证号：保留前3位和后4位，中间用 **** 替换，如 110***********1234 */
    ID_CARD {
        @Override
        public String desensitize(String value) {
            if (value == null || value.length() < 8) {
                return value;
            }
            return value.substring(0, 3) + "***********" + value.substring(value.length() - 4);
        }
    },

    /** 银行卡号：保留前4位和后4位，中间用 **** 替换，如 6222********1234 */
    BANK_CARD {
        @Override
        public String desensitize(String value) {
            if (value == null || value.length() < 8) {
                return value;
            }
            return value.substring(0, 4) + "********" + value.substring(value.length() - 4);
        }
    },

    /** 姓名：保留姓氏，名用 * 替换，如 张* */
    NAME {
        @Override
        public String desensitize(String value) {
            if (value == null || value.isEmpty()) {
                return value;
            }
            if (value.length() == 1) {
                return "*";
            }
            return value.charAt(0) + "*".repeat(value.length() - 1);
        }
    },

    /** 地址：保留前3个字符，其余用 **** 替换 */
    ADDRESS {
        @Override
        public String desensitize(String value) {
            if (value == null || value.length() <= 3) {
                return value;
            }
            return value.substring(0, 3) + "****";
        }
    },

    /** 密码：全部替换为 ****** */
    PASSWORD {
        @Override
        public String desensitize(String value) {
            if (value == null) {
                return value;
            }
            return "******";
        }
    };

    /**
     * 对敏感数据进行脱敏处理
     *
     * @param value 原始值
     * @return 脱敏后的值
     */
    public abstract String desensitize(String value);
}
