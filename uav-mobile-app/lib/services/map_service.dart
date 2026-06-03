import 'dart:math';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

/// 地图服务 - 提供离线地图缓存和无人机路径显示功能
class MapService {
  MapService._internal();

  factory MapService() => _instance;

  static final MapService _instance = MapService._internal();

  // 离线瓦片缓存
  final Map<String, Uint8List> _tileCache = {};

  // 默认瓦片URL模板
  static const String _tileUrlTemplate =
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  /// 获取地图瓦片图层
  TileLayer getTileLayer({
    String? urlTemplate,
    double maxZoom = 19,
    double minZoom = 1,
  }) {
    return TileLayer(
      urlTemplate: urlTemplate ?? _tileUrlTemplate,
      userAgentPackageName: 'com.uav.mobile',
      maxZoom: maxZoom,
      minZoom: minZoom,
    );
  }

  /// 创建路径规划路线
  PolylineLayer createRoutePolyline({
    required List<LatLng> points,
    Color color = Colors.blue,
    double strokeWidth = 3.0,
  }) {
    return PolylineLayer(
      polylines: [
        Polyline(
          points: points,
          color: color,
          strokeWidth: strokeWidth,
          isDotted: false,
        ),
      ],
    );
  }

  /// 创建无人机标记
  MarkerLayer createDroneMarker({
    required LatLng position,
    String? label,
    double heading = 0.0,
  }) {
    return MarkerLayer(
      markers: [
        Marker(
          point: position,
          width: 40,
          height: 40,
          child: Transform.rotate(
            angle: heading * pi / 180,
            child: const Icon(
              Icons.flight,
              color: Colors.blue,
              size: 32,
            ),
          ),
        ),
        if (label != null)
          Marker(
            point: position,
            width: 100,
            height: 30,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.black87,
                borderRadius: BorderRadius.circular(4),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              child: Text(
                label,
                style: const TextStyle(color: Colors.white, fontSize: 12),
                textAlign: TextAlign.center,
              ),
            ),
          ),
      ],
    );
  }

  /// 创建禁飞区/危险区域
  PolygonLayer createNoFlyZones(List<LatLng> zonePoints) {
    return PolygonLayer(
      polygons: [
        Polygon(
          points: zonePoints,
          color: Colors.red.withValues(alpha: 0.2),
          borderColor: Colors.red,
          borderStrokeWidth: 2,
          isFilled: true,
        ),
      ],
    );
  }

  /// 计算两点距离 (Haversine公式)
  static double calculateDistance(LatLng p1, LatLng p2) {
    const R = 6371000; // 地球半径(米)
    final dLat = _toRadians(p2.latitude - p1.latitude);
    final dLng = _toRadians(p2.longitude - p1.longitude);
    final a = sin(dLat / 2) * sin(dLat / 2) +
        cos(_toRadians(p1.latitude)) *
            cos(_toRadians(p2.latitude)) *
            sin(dLng / 2) *
            sin(dLng / 2);
    return R * 2 * atan2(sqrt(a), sqrt(1 - a));
  }

  static double _toRadians(double degree) => degree * pi / 180;
}
