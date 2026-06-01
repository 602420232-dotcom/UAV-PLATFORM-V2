import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/app_config.dart';
import '../../services/monitoring_service.dart';
import '../../providers/app_providers.dart';

class MonitoringPage extends ConsumerStatefulWidget {
  const MonitoringPage({super.key});

  @override
  ConsumerState<MonitoringPage> createState() => _MonitoringPageState();
}

class _MonitoringPageState extends ConsumerState<MonitoringPage> {
  bool _isLoading = true;
  String? _error;
  Map<String, dynamic>? _health;
  List<Map<String, dynamic>> _services = [];
  final List<Map<String, dynamic>> _algoPerf = const [];
  int _activeServices = 0;
  int _activeTasks = 0;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _loadData();
    _startAutoRefresh();
  }

  @override
  void dispose() {
    _stopAutoRefresh();
    super.dispose();
  }

  void _startAutoRefresh() {
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) {
        _loadData();
      }
    });
  }

  void _stopAutoRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = null;
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final monitorService = AppMonitoringService();

      final systemStatus = await monitorService.getSystemStatus();
      final serviceStatusList = await monitorService.getServiceStatus();

      setState(() {
        _isLoading = false;
        _health = systemStatus.toJson();
        _services = serviceStatusList.map((s) => s.toJson()).toList();
        _activeServices = _services.where((s) => s['isOnline'] == true).length;
        _activeTasks = ref.read(tasksProvider).valueOrNull?.where((t) => t.status == '执行中').length ?? 0;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('系统监控'),
        actions: [
          IconButton(
            icon: _isLoading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.dns, size: 48, color: Colors.grey),
                      const SizedBox(height: 12),
                      Text('加载失败: $_error', style: const TextStyle(color: Colors.grey), textAlign: TextAlign.center),
                      const SizedBox(height: 12),
                      ElevatedButton(onPressed: _loadData, child: const Text('重试')),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildOverviewGrid(context),
                        const SizedBox(height: 16),
                        _buildServiceStatus(context),
                        const SizedBox(height: 16),
                        _buildAlgorithmPerformance(context),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildOverviewGrid(BuildContext context) {
    final healthStatus = _health?['status']?.toString() ?? '--';
    final memory = _health?['components']?['memory']?['details']?['usage']?.toString() ?? '--';

    final items = [
      ('服务状态', '$_activeServices/${_services.length}', Icons.dns, _activeServices == _services.length ? AppConfig.successColor : AppConfig.warningColor),
      ('系统健康', healthStatus, Icons.favorite, healthStatus == 'UP' ? AppConfig.successColor : AppConfig.errorColor),
      ('内存使用', memory, Icons.storage, AppConfig.infoColor),
      ('活跃任务', '$_activeTasks', Icons.task, AppConfig.primaryColor),
    ];

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      childAspectRatio: 1.4,
      children: items.map((item) {
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(item.$3, color: item.$4, size: 28),
                const SizedBox(height: 8),
                Text(item.$2, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: item.$4)),
                Text(item.$1, style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildServiceStatus(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('服务状态', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            if (_services.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: Text('暂无服务数据', style: TextStyle(color: Colors.grey))),
              )
            else
              ..._services.map((s) {
                final name = s['name']?.toString() ?? '';
                final isOnline = s['isOnline'] == true;
                final responseTime = s['responseTime']?.toString() ?? '--';
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Row(
                    children: [
                      Icon(
                        isOnline ? Icons.check_circle : Icons.error,
                        size: 18,
                        color: isOnline ? AppConfig.successColor : AppConfig.errorColor,
                      ),
                      const SizedBox(width: 8),
                      Expanded(child: Text(name, style: const TextStyle(fontWeight: FontWeight.w500))),
                      Text(
                        '${responseTime}ms',
                        style: TextStyle(
                          color: (double.tryParse(responseTime) ?? 0) > 200 ? AppConfig.warningColor : AppConfig.successColor,
                        ),
                      ),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildAlgorithmPerformance(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('算法性能', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            if (_algoPerf.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: Text('暂无算法数据', style: TextStyle(color: Colors.grey))),
              )
            else
              ..._algoPerf.map((a) {
                final name = a['name']?.toString() ?? '';
                final avgTime = (a['avgTime'] as num?)?.toDouble() ?? 0;
                final successRate = (a['successRate'] as num?)?.toDouble() ?? 0;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Row(
                    children: [
                      SizedBox(width: 70, child: Text(name, style: const TextStyle(fontWeight: FontWeight.w500))),
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: successRate / 100,
                            minHeight: 8,
                            backgroundColor: const Color.fromARGB(38, 158, 158, 158),
                            valueColor: AlwaysStoppedAnimation<Color>(
                              successRate > 97 ? AppConfig.successColor : AppConfig.warningColor,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      SizedBox(width: 55, child: Text('${avgTime}s', textAlign: TextAlign.right, style: const TextStyle(fontSize: 13))),
                      SizedBox(
                        width: 45,
                        child: Text(
                          '${successRate.toStringAsFixed(0)}%',
                          textAlign: TextAlign.right,
                          style: TextStyle(
                            color: successRate > 97 ? AppConfig.successColor : AppConfig.warningColor,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }
}
