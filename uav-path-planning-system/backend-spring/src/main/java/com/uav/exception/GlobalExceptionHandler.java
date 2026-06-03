package com.uav.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.ControllerAdvice;

@Slf4j
@ControllerAdvice
public class GlobalExceptionHandler extends com.uav.common.exception.GlobalExceptionHandler {

    // 父类已处理：NoHandlerFoundException、HttpRequestMethodNotSupportedException
    // 本模块特定异常处理器在此添加

}
