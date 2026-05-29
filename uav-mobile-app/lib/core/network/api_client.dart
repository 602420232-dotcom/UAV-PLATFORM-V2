import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

import 'api_interceptor.dart';
import 'api_exception.dart';
import '../../config/app_config.dart';

class ApiClient {
  ApiClient._() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        validateStatus: (status) => status != null && status < 600,
      ),
    );

    _dio.interceptors.addAll([
      ApiInterceptor(),
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        error: true,
      ),
    ]);

    if (!kIsWeb) {
      (_dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
        final client = HttpClient();
        client.badCertificateCallback =
            (X509Certificate cert, String host, int port) => true;
        return client;
      };
    }
  }

  factory ApiClient() {
    _instance ??= ApiClient._();
    return _instance!;
  }
  late final Dio _dio;
  static ApiClient? _instance;

  Dio get dio => _dio;

  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      final response = await _dio.get(path, queryParameters: queryParameters);
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> post(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      final response = await _dio.post(
        path,
        data: data,
        queryParameters: queryParameters,
      );
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> put(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      final response = await _dio.put(
        path,
        data: data,
        queryParameters: queryParameters,
      );
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> delete(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      final response =
          await _dio.delete(path, queryParameters: queryParameters);
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> uploadFile(
    String path, {
    required File file,
    String fileField = 'file',
    Map<String, dynamic>? extraData,
    void Function(int, int)? onProgress,
  }) async {
    try {
      final formData = FormData.fromMap({
        fileField: await MultipartFile.fromFile(file.path),
        if (extraData != null) ...extraData,
      });
      final response = await _dio.post(
        path,
        data: formData,
        onSendProgress: onProgress,
      );
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Map<String, dynamic> _handleResponse(Response response) {
    final code = response.statusCode ?? -1;

    if (response.data == null) {
      throw ApiException(code: code, message: '服务器返回空数据');
    }

    if (code >= 400) {
      throw ApiException(
        code: code,
        message: '请求失败 ($code): ${response.statusMessage ?? "请检查API地址"}',
      );
    }

    try {
      final data = response.data is String
          ? json.decode(response.data) as Map<String, dynamic>
          : response.data as Map<String, dynamic>;
      return data;
    } on FormatException {
      throw ApiException(
        code: code,
        message: '服务器返回了HTML页面而非JSON（API地址可能不正确，或后端未启动）',
      );
    } on TypeError {
      throw ApiException(
        code: code,
        message: '服务器返回了非预期的数据格式',
      );
    }
  }

  ApiException _handleError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const ApiException(code: -1, message: '网络连接超时');
      case DioExceptionType.connectionError:
        return const ApiException(code: -1, message: '无法连接到服务器');
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode ?? -1;
        if (statusCode == 401) {
          return const ApiException(code: 401, message: '认证已过期，请重新登录');
        }
        if (statusCode == 403) {
          return const ApiException(code: 403, message: '没有访问权限');
        }
        if (statusCode == 404) {
          return const ApiException(code: 404, message: '请求的资源不存在');
        }
        if (statusCode >= 500) {
          return ApiException(code: statusCode, message: '服务器内部错误');
        }
        return ApiException(
          code: statusCode,
          message: e.response?.statusMessage ?? '请求失败',
        );
      case DioExceptionType.cancel:
        return const ApiException(code: -1, message: '请求已取消');
      default:
        return const ApiException(code: -1, message: '网络异常，请检查网络连接');
    }
  }
}
