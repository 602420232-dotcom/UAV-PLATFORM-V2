import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
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
  late InMemorySecureStorage secureStorage;
  late TokenManager tokenManager;

  setUp(() {
    secureStorage = InMemorySecureStorage();
    tokenManager = TokenManager(secureStorage: secureStorage);
  });

  group('saveTokens', () {
    test('saves access token, refresh token, and expiry', () async {
      await tokenManager.saveTokens(
        accessToken: 'test_access_token',
        refreshToken: 'test_refresh_token',
        expiresIn: 3600,
      );

      final accessToken = await tokenManager.getAccessToken();
      final refreshToken = await tokenManager.getRefreshToken();

      expect(accessToken, equals('test_access_token'));
      expect(refreshToken, equals('test_refresh_token'));
    });

    test('saves future expiry timestamp', () async {
      await tokenManager.saveTokens(
        accessToken: 'token',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      final isExpired = await tokenManager.isTokenExpired();
      expect(isExpired, isFalse);
    });

    test('overwrites existing tokens', () async {
      await tokenManager.saveTokens(
        accessToken: 'first_token',
        refreshToken: 'first_refresh',
        expiresIn: 3600,
      );

      await tokenManager.saveTokens(
        accessToken: 'second_token',
        refreshToken: 'second_refresh',
        expiresIn: 7200,
      );

      final accessToken = await tokenManager.getAccessToken();
      expect(accessToken, equals('second_token'));
    });
  });

  group('getAccessToken', () {
    test('returns null when no access token stored', () async {
      final token = await tokenManager.getAccessToken();
      expect(token, isNull);
    });

    test('returns stored access token', () async {
      await tokenManager.saveTokens(
        accessToken: 'my_token',
        refreshToken: 'my_refresh',
        expiresIn: 3600,
      );

      final token = await tokenManager.getAccessToken();
      expect(token, equals('my_token'));
    });

    test('returns null after clearTokens', () async {
      await tokenManager.saveTokens(
        accessToken: 'temp_token',
        refreshToken: 'temp_refresh',
        expiresIn: 3600,
      );
      await tokenManager.clearTokens();

      final token = await tokenManager.getAccessToken();
      expect(token, isNull);
    });
  });

  group('getRefreshToken', () {
    test('returns null when no refresh token stored', () async {
      final token = await tokenManager.getRefreshToken();
      expect(token, isNull);
    });

    test('returns stored refresh token', () async {
      await tokenManager.saveTokens(
        accessToken: 'acc',
        refreshToken: 'ref',
        expiresIn: 3600,
      );

      final token = await tokenManager.getRefreshToken();
      expect(token, equals('ref'));
    });
  });

  group('isTokenExpired', () {
    test('returns true when no expiry stored', () async {
      final expired = await tokenManager.isTokenExpired();
      expect(expired, isTrue);
    });

    test('returns true when expiry timestamp is invalid', () async {
      await secureStorage.write(key: 'token_expiry', value: 'not_a_number');

      final expired = await tokenManager.isTokenExpired();
      expect(expired, isTrue);
    });

    test('returns false when token is still valid', () async {
      await tokenManager.saveTokens(
        accessToken: 'valid_token',
        refreshToken: 'valid_refresh',
        expiresIn: 3600,
      );

      final expired = await tokenManager.isTokenExpired();
      expect(expired, isFalse);
    });
  });

  group('isTokenExpiringSoon', () {
    test('returns true when no expiry stored', () async {
      final expiring = await tokenManager.isTokenExpiringSoon();
      expect(expiring, isTrue);
    });

    test('returns false when expiry is far in the future', () async {
      await tokenManager.saveTokens(
        accessToken: 'token',
        refreshToken: 'refresh',
        expiresIn: 3600,
      );

      final expiring = await tokenManager.isTokenExpiringSoon(threshold: const Duration(minutes: 5));
      expect(expiring, isFalse);
    });

    test('returns true when custom threshold is large', () async {
      await tokenManager.saveTokens(
        accessToken: 'token',
        refreshToken: 'refresh',
        expiresIn: 10,
      );

      final expiring = await tokenManager.isTokenExpiringSoon(threshold: const Duration(hours: 1));
      expect(expiring, isTrue);
    });
  });

  group('clearTokens', () {
    test('clears all stored tokens', () async {
      await tokenManager.saveTokens(
        accessToken: 'acc',
        refreshToken: 'ref',
        expiresIn: 3600,
      );

      await tokenManager.clearTokens();

      expect(await tokenManager.getAccessToken(), isNull);
      expect(await tokenManager.getRefreshToken(), isNull);
      expect(await tokenManager.isTokenExpired(), isTrue);
    });

    test('can be called multiple times without error', () async {
      await tokenManager.saveTokens(
        accessToken: 'acc',
        refreshToken: 'ref',
        expiresIn: 3600,
      );

      await tokenManager.clearTokens();
      await tokenManager.clearTokens();

      expect(await tokenManager.getAccessToken(), isNull);
    });
  });

  group('hasValidToken', () {
    test('returns false when no access token stored', () async {
      final valid = await tokenManager.hasValidToken();
      expect(valid, isFalse);
    });

    test('returns false when token is expired', () async {
      await secureStorage.write(key: 'access_token', value: 'some_token');
      final pastTimestamp = (DateTime.now().millisecondsSinceEpoch - 60000).toString();
      await secureStorage.write(key: 'token_expiry', value: pastTimestamp);

      final valid = await tokenManager.hasValidToken();
      expect(valid, isFalse);
    });

    test('returns true when valid token exists', () async {
      await tokenManager.saveTokens(
        accessToken: 'valid_token',
        refreshToken: 'valid_refresh',
        expiresIn: 3600,
      );

      final valid = await tokenManager.hasValidToken();
      expect(valid, isTrue);
    });
  });
}
