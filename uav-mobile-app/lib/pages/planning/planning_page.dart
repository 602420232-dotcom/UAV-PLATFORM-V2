import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../config/app_config.dart';
import '../../providers/app_providers.dart';
import '../../services/planning_service.dart';
import '../../widgets/common/app_widgets.dart';

class PlanningPage extends ConsumerStatefulWidget {
  const PlanningPage({super.key});

  @override
  ConsumerState<PlanningPage> createState() => _PlanningPageState();
}

class _PlanningPageState extends ConsumerState<PlanningPage> {
  final MapController _mapController = MapController();
  final List<LatLng> _waypoints = [
    const LatLng(39.9042, 116.4074),
  ];
  final List<LatLng> _plannedPath = [];
  bool _isPlanning = false;
  bool _showResults = false;
  Map<String, dynamic>? _planResult;

  void _onTapMap(TapPosition tapPosition, LatLng point) {
    setState(() {
      _waypoints.add(point);
    });
  }

  void _addWaypointAtCoords() {
    final latCtrl = TextEditingController(text: '39.9042');
    final lngCtrl = TextEditingController(text: '116.4074');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('手动输入坐标'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: latCtrl,
              decoration: const InputDecoration(labelText: '纬度 (latitude)'),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: lngCtrl,
              decoration: const InputDecoration(labelText: '经度 (longitude)'),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
          FilledButton(
            onPressed: () {
              final lat = double.tryParse(latCtrl.text);
              final lng = double.tryParse(lngCtrl.text);
              if (lat != null && lng != null) {
                setState(() {
                  _waypoints.add(LatLng(lat, lng));
                });
              }
              Navigator.pop(ctx);
            },
            child: const Text('添加'),
          ),
        ],
      ),
    );
  }

  Future<void> _executePlanning() async {
    if (_waypoints.length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('至少需要 2 个任务点'), backgroundColor: AppConfig.warningColor),
      );
      return;
    }

    setState(() {
      _isPlanning = true;
      _showResults = false;
    });

    try {
      final planningService = PlanningService();
      final dronesAsync = ref.read(dronesProvider);

      final waypoints = _waypoints.asMap().entries.map((e) {
        return {
          'lat': e.value.latitude,
          'lng': e.value.longitude,
          'order': e.key,
        };
      }).toList();

      final droneList = dronesAsync.valueOrNull ?? [];

      final result = await planningService.fullPlanning(
        drones: {
          'available': droneList.map((d) => d.toJson()).toList(),
        },
        tasks: {
          'waypoints': waypoints,
          'count': waypoints.length,
        },
        weatherData: {
          'source': 'auto',
        },
        constraints: {
          'maxWindSpeed': 10,
          'minVisibility': 5000,
        },
      );

      setState(() {
        _planResult = result;
        _plannedPath.clear();
        _plannedPath.addAll(_waypoints);
        _showResults = true;
        _isPlanning = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('路径规划完成！'), backgroundColor: AppConfig.successColor),
        );
      }
    } catch (e) {
      setState(() => _isPlanning = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('规划失败: $e'), backgroundColor: AppConfig.errorColor),
        );
      }
    }
  }

  void _clearWaypoints() {
    setState(() {
      _waypoints.clear();
      _waypoints.add(const LatLng(39.9042, 116.4074));
      _plannedPath.clear();
      _showResults = false;
      _planResult = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width >= 768;

    return Scaffold(
      appBar: AppBar(
        title: const Text('路径规划'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_location),
            onPressed: _addWaypointAtCoords,
            tooltip: '输入坐标添加任务点',
          ),
          IconButton(
            icon: const Icon(Icons.clear_all),
            onPressed: _clearWaypoints,
            tooltip: '清空',
          ),
        ],
      ),
      body: isDesktop ? _buildDesktopLayout() : _buildMobileLayout(),
    );
  }

  Widget _buildMobileLayout() {
    return Column(
      children: [
        Expanded(flex: 3, child: _buildMap()),
        Expanded(flex: 2, child: _buildConfigPanel()),
      ],
    );
  }

  Widget _buildDesktopLayout() {
    return Row(
      children: [
        SizedBox(width: 360, child: _buildConfigPanel()),
        const VerticalDivider(width: 1),
        Expanded(child: _buildMap()),
      ],
    );
  }

  Widget _buildConfigPanel() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SectionTitle(title: '任务点列表'),
          const Text('点击地图添加任务点，或点击上方 ✏️ 手动输入坐标',
              style: TextStyle(fontSize: 12, color: Colors.grey)),
          const SizedBox(height: 8),
          ..._waypoints.asMap().entries.map((entry) {
            final idx = entry.key;
            final wp = entry.value;
            return Card(
              margin: const EdgeInsets.only(bottom: 6),
              child: ListTile(
                dense: true,
                leading: CircleAvatar(
                  radius: 14,
                  backgroundColor: idx == 0 ? AppConfig.successColor : AppConfig.warningColor,
                  child: Text(
                    idx == 0 ? '起' : '$idx',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
                title: Text(idx == 0 ? '起点' : '任务点 $idx', style: const TextStyle(fontSize: 14)),
                subtitle: Text(
                  '${wp.latitude.toStringAsFixed(4)}, ${wp.longitude.toStringAsFixed(4)}',
                  style: const TextStyle(fontSize: 11),
                ),
                trailing: idx == 0
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: () => setState(() => _waypoints.remove(wp)),
                      ),
              ),
            );
          }),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _waypoints.length < 2 || _isPlanning ? null : _executePlanning,
            icon: _isPlanning
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.route),
            label: Text(_isPlanning ? '规划中...' : '执行路径规划'),
            style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          ),
          if (_showResults && _planResult != null) ...[
            const SizedBox(height: 16),
            const Divider(),
            const SectionTitle(title: '规划结果'),
            _buildResultItem('任务点数量', '${_waypoints.length} 个'),
            _buildResultItem('总距离', '${(_planResult!['total_distance'] ?? '--')}'),
            _buildResultItem('预估时间', '${(_planResult!['estimated_time'] ?? '--')}'),
            _buildResultItem('风险等级', '${(_planResult!['risk_level'] ?? '--')}'),
            if (_planResult!['drones_assigned'] != null)
              _buildResultItem('分配无人机', '${_planResult!['drones_assigned']}'),
          ],
        ],
      ),
    );
  }

  Widget _buildResultItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildMap() {
    final markers = <Marker>[];
    for (var i = 0; i < _waypoints.length; i++) {
      final wp = _waypoints[i];
      if (i == 0) {
        markers.add(Marker(
          point: wp,
          width: 40,
          height: 40,
          child: const Icon(Icons.flight_takeoff, color: AppConfig.successColor, size: 32),
        ));
      } else {
        markers.add(Marker(
          point: wp,
          width: 30,
          height: 30,
          child: Container(
            decoration: BoxDecoration(
              color: AppConfig.warningColor,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
            ),
            child: Center(
              child: Text(
                '$i',
                style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ));
      }
    }

    final polylines = <Polyline>[];
    if (_plannedPath.isNotEmpty) {
      polylines.add(Polyline(
        points: _plannedPath,
        color: AppConfig.primaryColor,
        strokeWidth: 3,
      ));
    }

    return Stack(
      children: [
        FlutterMap(
          mapController: _mapController,
          options: MapOptions(
            initialCenter: const LatLng(39.9042, 116.4074),
            initialZoom: 13,
            onTap: _onTapMap,
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.uav.planning',
            ),
            MarkerLayer(markers: markers),
            PolylineLayer(polylines: polylines),
          ],
        ),
        Positioned(
          top: 8,
          right: 8,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('💡 提示', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  const SizedBox(height: 4),
                  const Text('点击地图添加任务点', style: TextStyle(fontSize: 11, color: Colors.grey)),
                  const Text('✏️ 按钮手动输入坐标', style: TextStyle(fontSize: 11, color: Colors.grey)),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
