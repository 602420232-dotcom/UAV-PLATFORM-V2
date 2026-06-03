import 'dart:convert';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

import '../core/utils/logger.dart';
import 'network_monitor.dart';

/// 数据库连接管理（单例）
///
/// 使用 sqflite 在本地创建 SQLite 数据库，包含三张表：
/// - [cached_paths]：路径规划缓存
/// - [cached_weather]：气象数据缓存
/// - [sync_queue]：离线期间产生的待同步操作队列
class DatabaseHelper {
  DatabaseHelper._();

  static final DatabaseHelper _instance = DatabaseHelper._();
  static DatabaseHelper get instance => _instance;

  Database? _database;

  static const String _dbName = 'uav_offline.db';
  static const int _dbVersion = 1;

  // 表名
  static const String tableCachedPaths = 'cached_paths';
  static const String tableCachedWeather = 'cached_weather';
  static const String tableSyncQueue = 'sync_queue';

  /// 获取数据库实例，懒初始化
  Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final dbPath = join(dir.path, _dbName);
      return await openDatabase(
        dbPath,
        version: _dbVersion,
        onCreate: _onCreate,
      );
    } catch (e) {
      LogUtil.e('初始化数据库失败', e);
      rethrow;
    }
  }

  Future<void> _onCreate(Database db, int version) async {
    // 路径规划缓存表
    await db.execute('''
      CREATE TABLE $tableCachedPaths (
        id TEXT PRIMARY KEY,
        drone_id TEXT NOT NULL,
        data TEXT NOT NULL,
        cached_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL
      )
    ''');

    // 气象数据缓存表
    await db.execute('''
      CREATE TABLE $tableCachedWeather (
        id TEXT PRIMARY KEY,
        location_key TEXT NOT NULL,
        data TEXT NOT NULL,
        cached_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL
      )
    ''');

    // 同步队列表
    await db.execute('''
      CREATE TABLE $tableSyncQueue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        retry_count INTEGER NOT NULL DEFAULT 0,
        max_retries INTEGER NOT NULL DEFAULT 3,
        status TEXT NOT NULL DEFAULT 'pending'
      )
    ''');

    // 索引
    await db.execute(
        'CREATE INDEX idx_cached_paths_drone ON $tableCachedPaths(drone_id)');
    await db.execute(
        'CREATE INDEX idx_cached_weather_location ON $tableCachedWeather(location_key)');
    await db.execute(
        'CREATE INDEX idx_sync_queue_status ON $tableSyncQueue(status)');

    LogUtil.i('离线数据库表结构创建完成');
  }

  /// 关闭数据库
  Future<void> close() async {
    final db = _database;
    if (db != null && db.isOpen) {
      await db.close();
      _database = null;
      LogUtil.i('离线数据库已关闭');
    }
  }
}

/// 离线数据管理器
///
/// 基于 SQLite 的离线缓存与同步管理，提供以下能力：
/// - 路径规划数据本地缓存（TTL 支持）
/// - 气象数据本地缓存（TTL 支持）
/// - 离线操作队列（网络恢复后自动同步）
/// - 缓存过期清理
/// - 网络状态感知
class OfflineManager {
  factory OfflineManager() => _instance;
  OfflineManager._() : _dbHelper = DatabaseHelper.instance {
    _monitor = NetworkMonitor();
  }
  static final OfflineManager _instance = OfflineManager._();

  final DatabaseHelper _dbHelper;
  final NetworkMonitor _monitor;

  // ---------- 默认 TTL 常量 ----------

  /// 路径规划缓存 TTL（默认 30 分钟）
  static const Duration _defaultPathPlanTtl = Duration(minutes: 30);

  /// 气象数据缓存 TTL（默认 15 分钟）
  static const Duration _defaultWeatherTtl = Duration(minutes: 15);

  // ---------- 公开属性 ----------

  /// 当前是否在线（委托给 NetworkMonitor）
  bool get isOnline => _monitor.currentStatus.isConnected;

  /// 初始化（由 main.dart 调用）
  void init() {
    _monitor.init();
  }

  /// 释放资源
  Future<void> dispose() async {
    _monitor.dispose();
    await _dbHelper.close();
  }

  // ============================================================
  //  路径规划缓存
  // ============================================================

  /// 缓存路径规划数据
  ///
  /// [id] 路径规划唯一标识
  /// [droneId] 关联无人机 ID
  /// [data] 路径规划的完整 JSON 数据
  /// [ttl] 可选自定义有效期，默认 [_defaultPathPlanTtl]
  Future<void> cachePathPlan({
    required String id,
    required String droneId,
    required Map<String, dynamic> data,
    Duration ttl = _defaultPathPlanTtl,
  }) async {
    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;

      await db.insert(
        DatabaseHelper.tableCachedPaths,
        {
          'id': id,
          'drone_id': droneId,
          'data': json.encode(data),
          'cached_at': now,
          'expires_at': now + ttl.inMilliseconds,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      LogUtil.i('路径规划已缓存: $id (TTL: ${ttl.inMinutes} 分钟)');
    } catch (e) {
      LogUtil.w('缓存路径规划失败: $id', e);
    }
  }

  /// 获取缓存的路径规划数据
  ///
  /// 若缓存不存在或已过期返回 `null`。
  Future<Map<String, dynamic>?> getCachedPathPlan(String id) async {
    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;

      final rows = await db.query(
        DatabaseHelper.tableCachedPaths,
        where: 'id = ? AND expires_at > ?',
        whereArgs: [id, now],
        limit: 1,
      );

      if (rows.isEmpty) {
        // 清理已过期的记录
        await _deleteExpired(DatabaseHelper.tableCachedPaths);
        return null;
      }

      final dataStr = rows.first['data'] as String;
      return json.decode(dataStr) as Map<String, dynamic>;
    } catch (e) {
      LogUtil.w('读取缓存路径规划失败: $id', e);
      return null;
    }
  }

  /// 批量获取无人机的所有有效路径规划
  Future<List<Map<String, dynamic>>> getCachedPathPlansByDrone(
      String droneId) async {
    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;

      final rows = await db.query(
        DatabaseHelper.tableCachedPaths,
        where: 'drone_id = ? AND expires_at > ?',
        whereArgs: [droneId, now],
      );

      return rows.map((r) {
        final data = json.decode(r['data'] as String) as Map<String, dynamic>;
        return data;
      }).toList();
    } catch (e) {
      LogUtil.w('批量读取路径规划缓存失败: $droneId', e);
      return [];
    }
  }

  // ============================================================
  //  气象数据缓存
  // ============================================================

  /// 缓存气象数据
  ///
  /// [locationKey] 位置标识（如 "lat,lng" 或城市 ID）
  /// [data] 气象数据的完整 JSON
  /// [ttl] 可选自定义有效期，默认 [_defaultWeatherTtl]
  Future<void> cacheWeatherData({
    required String locationKey,
    required Map<String, dynamic> data,
    Duration ttl = _defaultWeatherTtl,
  }) async {
    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;

      // 使用 locationKey 作为主键，便于覆盖更新
      await db.insert(
        DatabaseHelper.tableCachedWeather,
        {
          'id': locationKey,
          'location_key': locationKey,
          'data': json.encode(data),
          'cached_at': now,
          'expires_at': now + ttl.inMilliseconds,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      LogUtil.i('气象数据已缓存: $locationKey (TTL: ${ttl.inMinutes} 分钟)');
    } catch (e) {
      LogUtil.w('缓存气象数据失败: $locationKey', e);
    }
  }

  /// 获取缓存的指定位置气象数据
  Future<Map<String, dynamic>?> getCachedWeatherData(
      String locationKey) async {
    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;

      final rows = await db.query(
        DatabaseHelper.tableCachedWeather,
        where: 'location_key = ? AND expires_at > ?',
        whereArgs: [locationKey, now],
        limit: 1,
      );

      if (rows.isEmpty) {
        await _deleteExpired(DatabaseHelper.tableCachedWeather);
        return null;
      }

      final dataStr = rows.first['data'] as String;
      return json.decode(dataStr) as Map<String, dynamic>;
    } catch (e) {
      LogUtil.w('读取缓存气象数据失败: $locationKey', e);
      return null;
    }
  }

  /// 删除指定位置的过期气象缓存
  Future<void> deleteCachedWeather(String locationKey) async {
    try {
      final db = await _dbHelper.database;
      await db.delete(
        DatabaseHelper.tableCachedWeather,
        where: 'location_key = ?',
        whereArgs: [locationKey],
      );
    } catch (e) {
      LogUtil.w('删除气象缓存失败: $locationKey', e);
    }
  }

  // ============================================================
  //  同步队列
  // ============================================================

  /// 将操作加入同步队列
  ///
  /// 当离线状态下产生需要同步到服务端的操作时调用。
  /// [operationType] 操作类型（如 "sync_path_plan", "upload_weather"）
  /// [payload] 操作数据（会被 JSON 序列化）
  /// [maxRetries] 最大重试次数，默认 3
  Future<void> addToSyncQueue({
    required String operationType,
    required Map<String, dynamic> payload,
    int maxRetries = 3,
  }) async {
    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;

      await db.insert(DatabaseHelper.tableSyncQueue, {
        'operation_type': operationType,
        'payload': json.encode(payload),
        'created_at': now,
        'retry_count': 0,
        'max_retries': maxRetries,
        'status': 'pending',
      });
      LogUtil.i('已加入同步队列: $operationType');
    } catch (e) {
      LogUtil.w('加入同步队列失败: $operationType', e);
    }
  }

  /// 获取同步队列中的待处理操作数量
  Future<int> getPendingSyncCount() async {
    try {
      final db = await _dbHelper.database;
      final result = await db.rawQuery(
        'SELECT COUNT(*) AS count FROM ${DatabaseHelper.tableSyncQueue} WHERE status = ?',
        ['pending'],
      );
      return Sqflite.firstIntValue(result) ?? 0;
    } catch (e) {
      LogUtil.w('获取同步队列数量失败', e);
      return 0;
    }
  }

  /// 处理同步队列
  ///
  /// 在网络可用时调用，遍历所有 `pending` 状态的操作，
  /// 依次尝试执行 [syncHandler] 回调。执行成功后标记为 `synced`，
  /// 失败后递增重试计数，超过 [maxRetries] 则标记为 `failed`。
  ///
  /// [syncHandler] 由上层注入，负责实际的网络请求逻辑。
  /// 返回成功同步的操作数量。
  Future<int> processSyncQueue({
    required Future<bool> Function(
      String operationType,
      Map<String, dynamic> payload,
    ) syncHandler,
  }) async {
    // 离线时不处理
    if (!isOnline) {
      LogUtil.w('设备离线，跳过同步队列处理');
      return 0;
    }

    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;

      // 取出所有待处理的操作，按创建时间升序
      final pendingItems = await db.query(
        DatabaseHelper.tableSyncQueue,
        where: 'status = ?',
        whereArgs: ['pending'],
        orderBy: 'created_at ASC',
      );

      if (pendingItems.isEmpty) return 0;

      int successCount = 0;

      for (final item in pendingItems) {
        final id = item['id'] as int;
        final operationType = item['operation_type'] as String;
        final payloadStr = item['payload'] as String;
        final retryCount = item['retry_count'] as int;
        final maxRetries = item['max_retries'] as int;

        try {
          final payload = json.decode(payloadStr) as Map<String, dynamic>;
          final success = await syncHandler(operationType, payload);

          if (success) {
            await db.update(
              DatabaseHelper.tableSyncQueue,
              {'status': 'synced'},
              where: 'id = ?',
              whereArgs: [id],
            );
            successCount++;
            LogUtil.i('同步操作成功: $operationType');
          } else {
            await _handleSyncFailure(db, id, retryCount, maxRetries);
          }
        } catch (e) {
          LogUtil.w('同步操作执行异常: $operationType', e);
          await _handleSyncFailure(db, id, retryCount, maxRetries);
        }
      }

      if (successCount > 0) {
        LogUtil.i('同步队列处理完成，成功 $successCount / ${pendingItems.length}');
      }

      // 清理已同步和失败的记录（保留 24 小时用于调试）
      await _cleanupSyncedQueue(db, now);

      return successCount;
    } catch (e) {
      LogUtil.w('处理同步队列失败', e);
      return 0;
    }
  }

  /// 处理单条同步失败：递增重试次数或标记为失败
  Future<void> _handleSyncFailure(
    Database db,
    int id,
    int retryCount,
    int maxRetries,
  ) async {
    final newRetryCount = retryCount + 1;
    if (newRetryCount >= maxRetries) {
      await db.update(
        DatabaseHelper.tableSyncQueue,
        {
          'retry_count': newRetryCount,
          'status': 'failed',
        },
        where: 'id = ?',
        whereArgs: [id],
      );
      LogUtil.w('同步操作已达最大重试次数，标记为失败: id=$id');
    } else {
      await db.update(
        DatabaseHelper.tableSyncQueue,
        {'retry_count': newRetryCount},
        where: 'id = ?',
        whereArgs: [id],
      );
    }
  }

  /// 清理已同步和失败的记录（保留最近 24 小时）
  Future<void> _cleanupSyncedQueue(Database db, int now) async {
    const keepDuration = Duration(hours: 24);
    final cutoff = now - keepDuration.inMilliseconds;

    await db.delete(
      DatabaseHelper.tableSyncQueue,
      where: 'status IN (?, ?) AND created_at < ?',
      whereArgs: ['synced', 'failed', cutoff],
    );
  }

  // ============================================================
  //  缓存管理
  // ============================================================

  /// 删除指定表的所有过期记录
  Future<void> _deleteExpired(String table) async {
    try {
      final db = await _dbHelper.database;
      final now = DateTime.now().millisecondsSinceEpoch;
      final deleted = await db.delete(
        table,
        where: 'expires_at < ?',
        whereArgs: [now],
      );
      if (deleted > 0) {
        LogUtil.i('清理过期缓存: $table, 共 $deleted 条');
      }
    } catch (e) {
      LogUtil.w('清理过期缓存失败: $table', e);
    }
  }

  /// 清理所有过期缓存
  Future<void> clearExpiredCache() async {
    await _deleteExpired(DatabaseHelper.tableCachedPaths);
    await _deleteExpired(DatabaseHelper.tableCachedWeather);
  }

  /// 清除全部缓存（包括同步队列）
  Future<void> clearCache() async {
    try {
      final db = await _dbHelper.database;
      await db.delete(DatabaseHelper.tableCachedPaths);
      await db.delete(DatabaseHelper.tableCachedWeather);
      await db.delete(DatabaseHelper.tableSyncQueue);
      LogUtil.i('全部缓存已清除');
    } catch (e) {
      LogUtil.w('清除全部缓存失败', e);
    }
  }

  /// 仅清除同步队列
  Future<void> clearSyncQueue() async {
    try {
      final db = await _dbHelper.database;
      await db.delete(DatabaseHelper.tableSyncQueue);
      LogUtil.i('同步队列已清除');
    } catch (e) {
      LogUtil.w('清除同步队列失败', e);
    }
  }

  // ============================================================
  //  兼容旧版 API
  // ============================================================

  /// （旧版）基于文件系统的通用缓存写入
  ///
  /// 保留以兼容已有调用方。新代码请使用专有的 [cachePathPlan] /
  /// [cacheWeatherData] 方法。
  Future<void> cacheData(String key, Map<String, dynamic> data) async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/cache_$key.json');
      await file.writeAsString(
        json.encode({
          'timestamp': DateTime.now().millisecondsSinceEpoch,
          'data': data,
        }),
      );
    } catch (e) {
      LogUtil.w('缓存数据失败: $key', e);
    }
  }

  /// （旧版）基于文件系统的通用缓存读取
  ///
  /// 保留以兼容已有调用方。新代码请使用专有的 [getCachedPathPlan] /
  /// [getCachedWeatherData] 方法。
  Future<Map<String, dynamic>?> getCachedData(
    String key, {
    Duration maxAge = const Duration(hours: 1),
  }) async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/cache_$key.json');
      if (!await file.exists()) return null;

      final content =
          json.decode(await file.readAsString()) as Map<String, dynamic>;
      final timestamp =
          DateTime.fromMillisecondsSinceEpoch(content['timestamp'] as int);
      if (DateTime.now().difference(timestamp) > maxAge) {
        await file.delete();
        return null;
      }
      return content['data'] as Map<String, dynamic>?;
    } catch (e) {
      LogUtil.w('读取缓存失败: $key', e);
      return null;
    }
  }
}
