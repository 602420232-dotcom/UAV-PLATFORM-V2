import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:uav_path_planning_app/services/auth_service.dart';
import 'package:uav_path_planning_app/services/token_manager.dart';

class MockDio {
  final _responseQueue = <Response>[];
  final _errorQueue = <DioException>[];
  int postCallCount = 0;
  String? lastPostPath;
  dynamic lastPostData;

  void queueResponse(Response response) => _responseQueue.add(response);
  void queueError(DioException error) => _errorQueue.add(error);

  Future<Response> post(
    String path, {
    data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    postCallCount++;
    lastPostPath = path;
    lastPostData = data;

    if (_errorQueue.isNotEmpty) {
      throw _errorQueue.removeAt(0);
    }
    if (_responseQueue.isNotEmpty) {
      return _responseQueue.removeAt(0);
    }
    return Response(
      requestOptions: RequestOptions(path: path),
      statusCode: 200,
      data: {
        'code': 200,
        'data': {
          'accessToken': 'default_token',
          'refreshToken': 'default_refresh',
          'expiresIn': 3600,
        },
      },
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
  group('AuthService - login', () {
    late MockDio mockDio;
    late InMemorySecureStorage secureStorage;
    late TokenManager tokenManager;
    late AuthService authService;

    setUp(() {
      mockDio = MockDio();
      secureStorage = InMemorySecureStorage();
      tokenManager = TokenManager(secureStorage: secureStorage);
      authService = AuthService(
        dio: mockDio as dynamic,
        tokenManager: tokenManager,
        baseUrl: 'http://test.api:8080',
      );
    });

    test('returns success with tokens on valid credentials', () async {
      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          statusCode: 200,
          data: {
            'code': 200,
            'data': {
              'accessToken': 'access_token_123',
              'refreshToken': 'refresh_token_456',
              'expiresIn': 7200,
              'user': {
                'id': 1,
                'username': 'testuser',
                'role': 'USER',
              },
            },
          },
        ),
      );

      final result = await authService.login('testuser', 'password123');

      expect(result.success, isTrue);
      expect(result.accessToken, equals('access_token_123'));
      expect(result.refreshToken, equals('refresh_token_456'));
      expect(result.expiresIn, equals(7200));
      expect(result.user, isNotNull);
      expect(result.user!.username, equals('testuser'));
    });

    test('tokens are persisted to TokenManager on successful login', () async {
      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          statusCode: 200,
          data: {
            'code': 200,
            'data': {
              'accessToken': 'persisted_token',
              'refreshToken': 'persisted_refresh',
              'expiresIn': 3600,
            },
          },
        ),
      );

      await authService.login('user', 'pass');

      final storedAccess = await tokenManager.getAccessToken();
      final storedRefresh = await tokenManager.getRefreshToken();
      expect(storedAccess, equals('persisted_token'));
      expect(storedRefresh, equals('persisted_refresh'));
    });

    test('returns failure on wrong password', () async {
      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          statusCode: 200,
          data: {
            'code': 401,
            'message': 'Invalid username or password',
          },
        ),
      );

      final result = await authService.login('testuser', 'wrong_password');

      expect(result.success, isFalse);
      expect(result.errorMessage, contains('Invalid'));
    });

    test('returns failure on server error response', () async {
      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          statusCode: 500,
          data: {'message': 'Internal server error'},
        ),
      );

      final result = await authService.login('testuser', 'password');

      expect(result.success, isFalse);
    });

    test('returns failure on connection timeout', () async {
      mockDio.queueError(
        DioException(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          type: DioExceptionType.connectionTimeout,
        ),
      );

      final result = await authService.login('testuser', 'password');

      expect(result.success, isFalse);
      expect(result.errorMessage, contains('Connection timeout'));
    });

    test('returns failure on bad response with status code 401', () async {
      mockDio.queueError(
        DioException(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          response: Response(
            requestOptions: RequestOptions(path: '/api/v1/auth/login'),
            statusCode: 401,
            data: {'message': 'Unauthorized'},
          ),
          type: DioExceptionType.badResponse,
        ),
      );

      final result = await authService.login('testuser', 'wrong');

      expect(result.success, isFalse);
      expect(result.errorMessage, contains('Authentication failed'));
    });

    test('uses default expiresIn of 3600 when not provided', () async {
      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          statusCode: 200,
          data: {
            'code': 200,
            'data': {
              'accessToken': 'token_no_expiry',
              'refreshToken': 'refresh_no_expiry',
            },
          },
        ),
      );

      final result = await authService.login('user', 'pass');

      expect(result.success, isTrue);
      expect(result.expiresIn, equals(3600));
    });

    test('sends correct request body', () async {
      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/login'),
          statusCode: 200,
          data: {
            'code': 200,
            'data': {
              'accessToken': 'tok',
              'refreshToken': 'ref',
              'expiresIn': 3600,
            },
          },
        ),
      );

      await authService.login('myuser', 'mypass');

      expect(mockDio.lastPostPath, contains('/api/v1/auth/login'));
      expect(
        mockDio.lastPostData,
        equals({'username': 'myuser', 'password': 'mypass'}),
      );
    });
  });

  group('AuthService - refreshToken', () {
    late MockDio mockDio;
    late InMemorySecureStorage secureStorage;
    late TokenManager tokenManager;
    late AuthService authService;

    setUp(() {
      mockDio = MockDio();
      secureStorage = InMemorySecureStorage();
      tokenManager = TokenManager(secureStorage: secureStorage);
      authService = AuthService(
        dio: mockDio as dynamic,
        tokenManager: tokenManager,
        baseUrl: 'http://test.api:8080',
      );
    });

    test('returns success with new tokens', () async {
      await tokenManager.saveTokens(
        accessToken: 'old_token',
        refreshToken: 'old_refresh',
        expiresIn: 3600,
      );

      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/refresh'),
          statusCode: 200,
          data: {
            'code': 200,
            'data': {
              'accessToken': 'new_access_token',
              'refreshToken': 'new_refresh_token',
              'expiresIn': 7200,
            },
          },
        ),
      );

      final result = await authService.refreshToken();

      expect(result.success, isTrue);
      expect(result.accessToken, equals('new_access_token'));
    });

    test('persists new tokens after refresh', () async {
      await tokenManager.saveTokens(
        accessToken: 'old',
        refreshToken: 'old_ref',
        expiresIn: 3600,
      );

      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/refresh'),
          statusCode: 200,
          data: {
            'code': 200,
            'data': {
              'accessToken': 'fresh_token',
              'refreshToken': 'fresh_refresh',
              'expiresIn': 3600,
            },
          },
        ),
      );

      await authService.refreshToken();

      expect(await tokenManager.getAccessToken(), equals('fresh_token'));
      expect(await tokenManager.getRefreshToken(), equals('fresh_refresh'));
    });

    test('returns failure when no refresh token is available', () async {
      final result = await authService.refreshToken();

      expect(result.success, isFalse);
      expect(result.errorMessage, contains('No refresh token'));
    });

    test('clears tokens on refresh failure', () async {
      await tokenManager.saveTokens(
        accessToken: 'will_be_cleared',
        refreshToken: 'will_be_cleared_ref',
        expiresIn: 3600,
      );

      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/refresh'),
          statusCode: 401,
          data: {'message': 'Invalid refresh token'},
        ),
      );

      await authService.refreshToken();

      expect(await tokenManager.getAccessToken(), isNull);
      expect(await tokenManager.getRefreshToken(), isNull);
    });

    test('clears tokens on network error during refresh', () async {
      await tokenManager.saveTokens(
        accessToken: 'to_clear',
        refreshToken: 'to_clear_ref',
        expiresIn: 3600,
      );

      mockDio.queueError(
        DioException(
          requestOptions: RequestOptions(path: '/api/v1/auth/refresh'),
          type: DioExceptionType.connectionError,
        ),
      );

      await authService.refreshToken();

      expect(await tokenManager.getAccessToken(), isNull);
    });
  });

  group('AuthService - logout', () {
    late MockDio mockDio;
    late InMemorySecureStorage secureStorage;
    late TokenManager tokenManager;
    late AuthService authService;

    setUp(() {
      mockDio = MockDio();
      secureStorage = InMemorySecureStorage();
      tokenManager = TokenManager(secureStorage: secureStorage);
      authService = AuthService(
        dio: mockDio as dynamic,
        tokenManager: tokenManager,
        baseUrl: 'http://test.api:8080',
      );
    });

    test('clears tokens after successful logout', () async {
      await tokenManager.saveTokens(
        accessToken: 'logout_token',
        refreshToken: 'logout_refresh',
        expiresIn: 3600,
      );

      mockDio.queueResponse(
        Response(
          requestOptions: RequestOptions(path: '/api/v1/auth/logout'),
          statusCode: 200,
          data: {'code': 200, 'message': 'Logged out'},
        ),
      );

      await authService.logout();

      expect(await tokenManager.getAccessToken(), isNull);
      expect(await tokenManager.getRefreshToken(), isNull);
    });

    test('clears tokens even when logout API fails', () async {
      await tokenManager.saveTokens(
        accessToken: 'token',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      mockDio.queueError(
        DioException(
          requestOptions: RequestOptions(path: '/api/v1/auth/logout'),
          type: DioExceptionType.connectionError,
        ),
      );

      await authService.logout();

      expect(await tokenManager.getAccessToken(), isNull);
    });
  });

  group('AuthService - isLoggedIn', () {
    test('returns true when valid token exists', () async {
      final secureStorage = InMemorySecureStorage();
      final tokenManager = TokenManager(secureStorage: secureStorage);
      final authService = AuthService(tokenManager: tokenManager);

      await tokenManager.saveTokens(
        accessToken: 'valid',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      final loggedIn = await authService.isLoggedIn();
      expect(loggedIn, isTrue);
    });

    test('returns false when no token', () async {
      final secureStorage = InMemorySecureStorage();
      final tokenManager = TokenManager(secureStorage: secureStorage);
      final authService = AuthService(tokenManager: tokenManager);

      final loggedIn = await authService.isLoggedIn();
      expect(loggedIn, isFalse);
    });
  });
}
