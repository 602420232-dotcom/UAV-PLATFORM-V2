import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:uav_path_planning_app/core/network/api_interceptor.dart';
import 'package:uav_path_planning_app/services/token_manager.dart';

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
  group('ApiInterceptor - onRequest', () {
    late InMemorySecureStorage secureStorage;
    late TokenManager tokenManager;

    setUp(() {
      secureStorage = InMemorySecureStorage();
      tokenManager = TokenManager(secureStorage: secureStorage);
    });

    test('adds Authorization header when token exists', () async {
      await tokenManager.saveTokens(
        accessToken: 'my_bearer_token',
        refreshToken: 'my_refresh',
        expiresIn: 3600,
      );

      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(
        options.headers['Authorization'],
        equals('Bearer my_bearer_token'),
      );
    });

    test('does not add Authorization header when no token', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(options.headers['Authorization'], isNull);
    });

    test('adds X-Request-ID header', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(options.headers['X-Request-ID'], isNotNull);
      expect(
        (options.headers['X-Request-ID'] as String).startsWith('MOB-'),
        isTrue,
      );
    });

    test('adds X-Client-Type header', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(options.headers['X-Client-Type'], equals('mobile-app'));
    });

    test('adds X-Client-Version header', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(options.headers['X-Client-Version'], equals('1.0.0'));
    });

    test('calls handler.next after processing', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final handler = RequestInterceptorHandler();

      interceptor.onRequest(options, handler);

      expect(options.headers['X-Client-Type'], equals('mobile-app'));
    });
  });

  group('ApiInterceptor - onError', () {
    test('handles 401 error gracefully', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/protected');
      final err = DioException(
        requestOptions: options,
        response: Response(
          requestOptions: options,
          statusCode: 401,
          data: {'message': 'Unauthorized'},
        ),
        type: DioExceptionType.badResponse,
      );
      final handler = ErrorInterceptorHandler();

      interceptor.onError(err, handler);
    });

    test('passes through non-401 errors', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final err = DioException(
        requestOptions: options,
        response: Response(
          requestOptions: options,
          statusCode: 403,
          data: {'message': 'Forbidden'},
        ),
        type: DioExceptionType.badResponse,
      );

      interceptor.onError(err, ErrorInterceptorHandler());
    });

    test('passes through connection errors', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/data');
      final err = DioException(
        requestOptions: options,
        type: DioExceptionType.connectionTimeout,
      );

      interceptor.onError(err, ErrorInterceptorHandler());
    });
  });

  group('X-Request-ID format', () {
    test('generates unique request IDs', () async {
      final interceptor = ApiInterceptor();
      final options1 = RequestOptions(path: '/api/a');
      final options2 = RequestOptions(path: '/api/b');

      interceptor.onRequest(options1, RequestInterceptorHandler());
      interceptor.onRequest(options2, RequestInterceptorHandler());

      final id1 = options1.headers['X-Request-ID'] as String;
      final id2 = options2.headers['X-Request-ID'] as String;
      expect(id1, isNot(equals(id2)));
    });

    test('request ID starts with MOB-', () async {
      final interceptor = ApiInterceptor();
      final options = RequestOptions(path: '/api/test');

      interceptor.onRequest(options, RequestInterceptorHandler());

      final requestId = options.headers['X-Request-ID'] as String;
      expect(requestId.startsWith('MOB-'), isTrue);
    });
  });
}
