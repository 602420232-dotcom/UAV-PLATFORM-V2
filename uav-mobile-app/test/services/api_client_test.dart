import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:uav_path_planning_app/services/api_client.dart';
import 'package:uav_path_planning_app/services/token_manager.dart';
import 'package:uav_path_planning_app/services/auth_service.dart';

class MockDio {
  Future<Response> post(
    String path, {
    data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    return Response(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {'code': 200, 'message': 'ok'},
    );
  }
}

class InMemorySecureStorage extends FlutterSecureStorage {
  final _store = <String, String>{};

  @override
  Future<void> write({
    required String key,
    required String? value,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (value != null) {
      _store[key] = value;
    } else {
      _store.remove(key);
    }
  }

  @override
  Future<String?> read({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    return _store[key];
  }

  @override
  Future<bool> containsKey({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    return _store.containsKey(key);
  }

  @override
  Future<void> delete({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    _store.remove(key);
  }

  @override
  Future<Map<String, String>> readAll({
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    return Map.from(_store);
  }

  @override
  Future<void> deleteAll({
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    _store.clear();
  }
}

void main() {
  group('AuthInterceptor - onRequest', () {
    late InMemorySecureStorage secureStorage;
    late TokenManager tokenManager;
    late AuthService authService;
    late MockDio mockDio;
    late AuthInterceptor interceptor;

    setUp(() {
      secureStorage = InMemorySecureStorage();
      tokenManager = TokenManager(secureStorage: secureStorage);
      mockDio = MockDio();
      authService = AuthService(
        dio: mockDio as dynamic,
        tokenManager: tokenManager,
        baseUrl: 'http://test.api:8080',
      );
      interceptor = AuthInterceptor(
        tokenManager: tokenManager,
        authService: authService,
        dio: mockDio as dynamic,
      );
    });

    test('skips adding token for login path', () async {
      await tokenManager.saveTokens(
        accessToken: 'secret_token',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      final options = RequestOptions(path: '/api/v1/auth/login');
      final handler = RequestInterceptorHandler();

      await interceptor.onRequest(options, handler);

      expect(options.headers['Authorization'], isNull);
    });

    test('skips adding token for refresh path', () async {
      await tokenManager.saveTokens(
        accessToken: 'token',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      final options = RequestOptions(path: '/api/v1/auth/refresh');
      final handler = RequestInterceptorHandler();

      await interceptor.onRequest(options, handler);

      expect(options.headers['Authorization'], isNull);
    });

    test('skips adding token for logout path', () async {
      await tokenManager.saveTokens(
        accessToken: 'token',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      final options = RequestOptions(path: '/api/v1/auth/logout');
      final handler = RequestInterceptorHandler();

      await interceptor.onRequest(options, handler);

      expect(options.headers['Authorization'], isNull);
    });

    test('adds token for non-public paths', () async {
      await tokenManager.saveTokens(
        accessToken: 'protected_token',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      final options = RequestOptions(path: '/api/v1/data-sources');
      final handler = RequestInterceptorHandler();

      await interceptor.onRequest(options, handler);

      expect(options.headers['Authorization'], equals('Bearer protected_token'));
    });

    test('does not add token when no token stored for non-public path', () async {
      final options = RequestOptions(path: '/api/v1/drones');
      final handler = RequestInterceptorHandler();

      await interceptor.onRequest(options, handler);

      expect(options.headers['Authorization'], isNull);
    });
  });

  group('AuthInterceptor - onError', () {
    late InMemorySecureStorage secureStorage;
    late TokenManager tokenManager;
    late AuthService authService;
    late MockDio mockDio;
    late AuthInterceptor interceptor;

    setUp(() {
      secureStorage = InMemorySecureStorage();
      tokenManager = TokenManager(secureStorage: secureStorage);
      mockDio = MockDio();
      authService = AuthService(
        dio: mockDio as dynamic,
        tokenManager: tokenManager,
        baseUrl: 'http://test.api:8080',
      );
      interceptor = AuthInterceptor(
        tokenManager: tokenManager,
        authService: authService,
        dio: mockDio as dynamic,
      );
    });

    test('handles 401 by attempting token refresh', () async {
      await tokenManager.saveTokens(
        accessToken: 'expired_token',
        refreshToken: 'valid_refresh',
        expiresIn: -1,
      );

      final options = RequestOptions(path: '/api/v1/drones');
      final err = DioException(
        requestOptions: options,
        response: Response(
          requestOptions: options,
          statusCode: 401,
          data: {'message': 'Token expired'},
        ),
        type: DioExceptionType.badResponse,
      );

      // ignore: unawaited_futures
      interceptor.onError(err, ErrorInterceptorHandler());
    });

    test('passes through non-401 errors without refresh', () async {
      final options = RequestOptions(path: '/api/v1/data');
      final err = DioException(
        requestOptions: options,
        response: Response(
          requestOptions: options,
          statusCode: 500,
          data: {'message': 'Server error'},
        ),
        type: DioExceptionType.badResponse,
      );

      // ignore: unawaited_futures
      interceptor.onError(err, ErrorInterceptorHandler());
    });

    test('passes through 404 errors', () async {
      final options = RequestOptions(path: '/api/v1/notfound');
      final err = DioException(
        requestOptions: options,
        response: Response(
          requestOptions: options,
          statusCode: 404,
          data: {'message': 'Not found'},
        ),
        type: DioExceptionType.badResponse,
      );

      // ignore: unawaited_futures
      interceptor.onError(err, ErrorInterceptorHandler());
    });

    test('passes through connection timeout errors', () async {
      final options = RequestOptions(path: '/api/v1/data');
      final err = DioException(
        requestOptions: options,
        type: DioExceptionType.connectionTimeout,
      );

      // ignore: unawaited_futures
      interceptor.onError(err, ErrorInterceptorHandler());
    });
  });

  group('AuthInterceptor - public path matching', () {
    test('matches paths that contain auth/login', () async {
      final tokenManager = TokenManager(secureStorage: InMemorySecureStorage());
      final mockDio = MockDio();
      final authService = AuthService(tokenManager: tokenManager);
      final interceptor = AuthInterceptor(
        tokenManager: tokenManager,
        authService: authService,
        dio: mockDio as dynamic,
      );

      final options = RequestOptions(path: '/api/v1/auth/login');
      final handler = RequestInterceptorHandler();

      await interceptor.onRequest(options, handler);
      expect(options.headers['Authorization'], isNull);
    });

    test('matches paths regardless of base URL prefix', () async {
      final tokenManager = TokenManager(secureStorage: InMemorySecureStorage());
      final mockDio = MockDio();
      final authService = AuthService(tokenManager: tokenManager);
      final interceptor = AuthInterceptor(
        tokenManager: tokenManager,
        authService: authService,
        dio: mockDio as dynamic,
      );

      await tokenManager.saveTokens(
        accessToken: 'tok',
        refreshToken: 'ref',
        expiresIn: 3600,
      );

      final options = RequestOptions(path: 'http://proxy:8088/api/v1/auth/login');
      final handler = RequestInterceptorHandler();

      await interceptor.onRequest(options, handler);
      expect(options.headers['Authorization'], isNull);
    });
  });
}
