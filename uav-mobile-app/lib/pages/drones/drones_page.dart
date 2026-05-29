import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/app_config.dart';
import '../../models/drone.dart';
import '../../providers/app_providers.dart';

class DronesPage extends ConsumerStatefulWidget {
  const DronesPage({super.key});

  @override
  ConsumerState<DronesPage> createState() => _DronesPageState();
}

class _DronesPageState extends ConsumerState<DronesPage> {
  int get onlineCount => drones.where((d) => d.status == '在线').length;
  int get taskingCount => drones.where((d) => d.status == '执行任务').length;
  int get idleCount => drones.where((d) => d.status == '待命').length;

  List<DroneModel> get drones {
    final asyncVal = ref.watch(dronesProvider);
    return asyncVal.valueOrNull ?? [];
  }

  Color _statusColor(String status) {
    switch (status) {
      case '在线':
        return AppConfig.successColor;
      case '执行任务':
        return AppConfig.infoColor;
      case '待命':
        return AppConfig.warningColor;
      case '维护中':
        return Colors.purple;
      case '故障':
        return AppConfig.errorColor;
      default:
        return Colors.grey;
    }
  }

  Color _batteryColor(double battery) {
    if (battery > 60) return AppConfig.successColor;
    if (battery > 30) return AppConfig.warningColor;
    return AppConfig.errorColor;
  }

  IconData _batteryIcon(double battery) {
    if (battery > 80) return Icons.battery_full;
    if (battery > 50) return Icons.battery_5_bar;
    if (battery > 20) return Icons.battery_3_bar;
    return Icons.battery_alert;
  }

  Future<void> _showAddEditDialog({DroneModel? existing}) async {
    final nameCtrl = TextEditingController(text: existing?.name ?? '');
    final modelCtrl = TextEditingController(text: existing?.model ?? '');
    final typeCtrl = TextEditingController(text: existing?.type ?? '多旋翼');
    final payloadCtrl =
        TextEditingController(text: existing?.maxPayload.toString() ?? '2.0');
    final flightTimeCtrl =
        TextEditingController(text: existing?.maxFlightTime.toString() ?? '30');
    final speedCtrl =
        TextEditingController(text: existing?.maxSpeed.toString() ?? '15');

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(existing != null ? '编辑无人机' : '添加无人机'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(
                    labelText: '名称', hintText: '例: 猎鹰-1号',),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: modelCtrl,
                decoration: const InputDecoration(
                    labelText: '型号', hintText: '例: DJI-M300',),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: typeCtrl,
                decoration: const InputDecoration(
                    labelText: '类型', hintText: '多旋翼 / 固定翼 / 混合动力',),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: payloadCtrl,
                      decoration: const InputDecoration(labelText: '载重(kg)'),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: flightTimeCtrl,
                      decoration: const InputDecoration(labelText: '续航(min)'),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: speedCtrl,
                decoration: const InputDecoration(labelText: '最大速度(m/s)'),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('取消'),),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(existing != null ? '保存' : '添加'),
          ),
        ],
      ),
    );

    if (result != true) return;

    final drone = DroneModel(
      id: existing?.id ?? 'D-${DateTime.now().millisecondsSinceEpoch}',
      name: nameCtrl.text.trim(),
      model: modelCtrl.text.trim(),
      type: typeCtrl.text.trim(),
      maxPayload: double.tryParse(payloadCtrl.text) ?? 2.0,
      maxFlightTime: double.tryParse(flightTimeCtrl.text) ?? 30.0,
      maxSpeed: double.tryParse(speedCtrl.text) ?? 15.0,
      status: existing?.status ?? '待命',
      battery: existing?.battery ?? 100.0,
    );

    try {
      if (existing != null) {
        await ref.read(dronesProvider.notifier).updateDrone(existing.id, drone);
      } else {
        await ref.read(dronesProvider.notifier).addDrone(drone);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('操作失败: $e'), backgroundColor: AppConfig.errorColor,),
        );
      }
    }
  }

  Future<void> _deleteDrone(DroneModel drone) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('确认删除'),
        content: Text('确定要删除 "${drone.name}" 吗？'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('取消'),),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style:
                FilledButton.styleFrom(backgroundColor: AppConfig.errorColor),
            child: const Text('删除'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    try {
      await ref.read(dronesProvider.notifier).removeDrone(drone.id);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('删除失败: $e'), backgroundColor: AppConfig.errorColor,),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final asyncDrones = ref.watch(dronesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('无人机管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(dronesProvider.notifier).refresh(),
            tooltip: '刷新',
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddEditDialog(),
            tooltip: '添加无人机',
          ),
        ],
      ),
      body: asyncDrones.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
              const SizedBox(height: 12),
              Text('加载失败: $err', style: const TextStyle(color: Colors.grey)),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: () => ref.read(dronesProvider.notifier).refresh(),
                child: const Text('重试'),
              ),
            ],
          ),
        ),
        data: (drones) {
          if (drones.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.rocket_launch, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('暂无无人机',
                      style: TextStyle(fontSize: 18, color: Colors.grey),),
                  const SizedBox(height: 8),
                  const Text('点击右下角 + 添加第一架无人机',
                      style: TextStyle(color: Colors.grey),),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: () => _showAddEditDialog(),
                    icon: const Icon(Icons.add),
                    label: const Text('添加无人机'),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              _buildStatusBar(context),
              Expanded(child: _buildDronesList(context, drones)),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddEditDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildStatusBar(BuildContext context) {
    final d = drones;
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: _statCard('总数', '${d.length}', Icons.rocket_launch,
                AppConfig.primaryColor,),
          ),
          Expanded(
            child: _statCard(
                '待命', '$idleCount', Icons.check_circle, AppConfig.successColor,),
          ),
          Expanded(
            child: _statCard(
                '任务中', '$taskingCount', Icons.flight, AppConfig.infoColor,),
          ),
          Expanded(
            child: _statCard(
                '在线', '$onlineCount', Icons.wifi, AppConfig.successColor,),
          ),
        ],
      ),
    );
  }

  Widget _statCard(String label, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 4),
            Text(value,
                style: TextStyle(
                    fontSize: 18, fontWeight: FontWeight.bold, color: color,),),
            Text(label,
                style: const TextStyle(fontSize: 11, color: Colors.grey),),
          ],
        ),
      ),
    );
  }

  Widget _buildDronesList(BuildContext context, List<DroneModel> drones) {
    return RefreshIndicator(
      onRefresh: () => ref.read(dronesProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: drones.length,
        itemBuilder: (context, index) {
          final drone = drones[index];
          return _buildDroneCard(context, drone);
        },
      ),
    );
  }

  Widget _buildDroneCard(BuildContext context, DroneModel drone) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showDroneDetail(context, drone),
        onLongPress: () => _showContextMenu(context, drone),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: const Color(0x1A1677FF),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child:
                        Icon(Icons.rocket, color: _statusColor(drone.status)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(drone.name,
                            style: const TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold,),),
                        const SizedBox(height: 2),
                        Text('${drone.model} · ${drone.type}',
                            style: const TextStyle(
                                color: Colors.grey, fontSize: 12,),),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2,),
                        decoration: BoxDecoration(
                          color: const Color(0x261677FF),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          drone.status,
                          style: TextStyle(
                              color: _statusColor(drone.status), fontSize: 12,),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(_batteryIcon(drone.battery),
                              size: 14, color: _batteryColor(drone.battery),),
                          Text(' ${drone.battery.toStringAsFixed(0)}%',
                              style: TextStyle(
                                  color: _batteryColor(drone.battery),
                                  fontSize: 12,),),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _droneInfoChip('载重', '${drone.maxPayload}kg'),
                  const SizedBox(width: 8),
                  _droneInfoChip('续航', '${drone.maxFlightTime}min'),
                  const SizedBox(width: 8),
                  _droneInfoChip('速度', '${drone.maxSpeed}m/s'),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _droneInfoChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: const Color.fromARGB(25, 158, 158, 158),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text('$label: $value',
          style: const TextStyle(color: Colors.grey, fontSize: 11),),
    );
  }

  void _showContextMenu(BuildContext context, DroneModel drone) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.edit),
              title: const Text('编辑'),
              onTap: () {
                Navigator.pop(ctx);
                _showAddEditDialog(existing: drone);
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete, color: AppConfig.errorColor),
              title: const Text('删除',
                  style: TextStyle(color: AppConfig.errorColor),),
              onTap: () {
                Navigator.pop(ctx);
                _deleteDrone(drone);
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showDroneDetail(BuildContext context, DroneModel drone) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.55,
          maxChildSize: 0.85,
          minChildSize: 0.35,
          expand: false,
          builder: (context, scrollController) {
            return SingleChildScrollView(
              controller: scrollController,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                          color: Colors.grey[300],
                          borderRadius: BorderRadius.circular(2),),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Center(
                    child: Column(
                      children: [
                        Icon(Icons.rocket,
                            size: 48, color: _statusColor(drone.status),),
                        const SizedBox(height: 8),
                        Text(drone.name,
                            style: const TextStyle(
                                fontSize: 22, fontWeight: FontWeight.bold,),),
                        const SizedBox(height: 4),
                        Text('${drone.model} · ${drone.type}',
                            style: const TextStyle(color: Colors.grey),),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                          child: _detailCard(
                              '状态', drone.status, _statusColor(drone.status),),),
                      Expanded(
                          child: _detailCard('电量', '${drone.battery}%',
                              _batteryColor(drone.battery),),),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _detailRow('ID', drone.id),
                  _detailRow('型号', drone.model),
                  _detailRow('类型', drone.type),
                  _detailRow('最大载重', '${drone.maxPayload} kg'),
                  _detailRow('最大续航', '${drone.maxFlightTime} min'),
                  _detailRow('最大速度', '${drone.maxSpeed} m/s'),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            Navigator.pop(context);
                            _showAddEditDialog(existing: drone);
                          },
                          icon: const Icon(Icons.edit),
                          label: const Text('编辑'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            Navigator.pop(context);
                            _deleteDrone(drone);
                          },
                          icon: const Icon(Icons.delete,
                              color: AppConfig.errorColor,),
                          label: const Text('删除',
                              style: TextStyle(color: AppConfig.errorColor),),
                          style: OutlinedButton.styleFrom(
                              foregroundColor: AppConfig.errorColor,),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _detailCard(String label, String value, Color color) {
    return Card(
      color: const Color(0x141677FF),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(
                    fontSize: 20, fontWeight: FontWeight.bold, color: color,),),
            Text(label,
                style: const TextStyle(color: Colors.grey, fontSize: 12),),
          ],
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(
              width: 80,
              child: Text(label, style: const TextStyle(color: Colors.grey)),),
          Expanded(
              child: Text(value,
                  style: const TextStyle(fontWeight: FontWeight.w500),),),
        ],
      ),
    );
  }
}
