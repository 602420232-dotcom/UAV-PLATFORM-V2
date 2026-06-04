import 'package:shared_preferences/shared_preferences.dart';

/// 本地存储管理器
/// 使用 SharedPreferences 存储非敏感数据
class LocalStorage {
  LocalStorage._();

  factory LocalStorage() {
    _instance ??= LocalStorage._();
    return _instance!;
  }
  static SharedPreferences? _prefs;
  static LocalStorage? _instance;

  /// 初始化存储
  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  /// 获取实例
  static SharedPreferences get prefs {
    if (_prefs == null) {
      throw Exception(
        'LocalStorage not initialized. Call LocalStorage.init() first.',
      );
    }
    return _prefs!;
  }

  // Keys
  static const String _themeModeKey = 'theme_mode';
  static const String _localeKey = 'locale';
  static const String _serverUrlKey = 'server_url';
  static const String _lastSyncTimeKey = 'last_sync_time';
  static const String _offlineModeKey = 'offline_mode';
  static const String _mapTypeKey = 'map_type';
  static const String _autoSyncKey = 'auto_sync';

  // Theme
  Future<bool> setThemeMode(String mode) async {
    return await prefs.setString(_themeModeKey, mode);
  }

  String getThemeMode() {
    return prefs.getString(_themeModeKey) ?? 'light';
  }

  // Locale
  Future<bool> setLocale(String locale) async {
    return await prefs.setString(_localeKey, locale);
  }

  String? getLocale() {
    return prefs.getString(_localeKey);
  }

  // Server URL
  Future<bool> setServerUrl(String url) async {
    return await prefs.setString(_serverUrlKey, url);
  }

  String getServerUrl() {
    return prefs.getString(_serverUrlKey) ?? 'http://localhost:8088';
  }

  // Last Sync Time
  Future<bool> setLastSyncTime(DateTime time) async {
    return await prefs.setString(_lastSyncTimeKey, time.toIso8601String());
  }

  DateTime? getLastSyncTime() {
    final str = prefs.getString(_lastSyncTimeKey);
    if (str != null) {
      return DateTime.tryParse(str);
    }
    return null;
  }

  // Offline Mode
  Future<bool> setOfflineMode(bool enabled) async {
    return await prefs.setBool(_offlineModeKey, enabled);
  }

  bool getOfflineMode() {
    return prefs.getBool(_offlineModeKey) ?? false;
  }

  // Map Type
  Future<bool> setMapType(String type) async {
    return await prefs.setString(_mapTypeKey, type);
  }

  String getMapType() {
    return prefs.getString(_mapTypeKey) ?? 'openstreetmap';
  }

  // Auto Sync
  Future<bool> setAutoSync(bool enabled) async {
    return await prefs.setBool(_autoSyncKey, enabled);
  }

  bool getAutoSync() {
    return prefs.getBool(_autoSyncKey) ?? true;
  }

  /// 清除所有数据
  Future<bool> clearAll() async {
    return await prefs.clear();
  }

  /// 移除指定键
  Future<bool> remove(String key) async {
    return await prefs.remove(key);
  }
}
