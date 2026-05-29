import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/app_config.dart';
import '../../models/data_source.dart';
import '../../providers/app_providers.dart';

class DataSourcePage extends ConsumerStatefulWidget {
  const DataSourcePage({super.key});

  @override
  ConsumerState<DataSourcePage> createState() => _DataSourcePageState();
}

class _DataSourcePageState extends ConsumerState<DataSourcePage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  String _typeLabel(String type) {
    switch (type) {
      case 'ground_station':
        return '地面站';
      case 'buoy':
        return '浮标';
      case 'satellite':
        return '卫星';
      case 'radar':
        return '雷达';
      case 'weather_station':
        return '气象站';
      default:
        return type;
    }
  }

  Future<void> _showAddEditDialog({DataSourceModel? existing}) async {
    final nameCtrl = TextEditingController(text: existing?.name ?? '');
    var type = existing?.type ?? 'ground_station';

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(existing != null ? '编辑数据源' : '添加数据源'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: '名称', hintText: '例: 北京地面站'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: type,
                decoration: const InputDecoration(labelText: '类型'),
                items: const [
                  DropdownMenuItem(value: 'ground_station', child: Text('地面站')),
                  DropdownMenuItem(value: 'buoy', child: Text('浮标')),
                  DropdownMenuItem(value: 'satellite', child: Text('卫星')),
                  DropdownMenuItem(value: 'radar', child: Text('雷达')),
                  DropdownMenuItem(value: 'weather_station', child: Text('气象站')),
                ],
                onChanged: (v) => setDialogState(() => type = v ?? type),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(existing != null ? '保存' : '添加')),
          ],
        ),
      ),
    );

    if (result != true) return;

    final source = DataSourceModel(
      id: existing?.id ?? 'DS-${DateTime.now().millisecondsSinceEpoch}',
      name: nameCtrl.text.trim(),
      type: type,
      status: existing?.status ?? 'active',
    );

    try {
      if (existing != null) {
        await ref.read(dataSourcesProvider.notifier).updateSource(existing.id, source);
      } else {
        await ref.read(dataSourcesProvider.notifier).addSource(source);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('操作失败: $e'), backgroundColor: AppConfig.errorColor),
        );
      }
    }
  }

  Future<void> _deleteSource(DataSourceModel source) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('确认删除'),
        content: Text('确定要删除 "${source.name}" 吗？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(backgroundColor: AppConfig.errorColor),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      await ref.read(dataSourcesProvider.notifier).removeSource(source.id);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('删除失败: $e'), backgroundColor: AppConfig.errorColor),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final asyncSources = ref.watch(dataSourcesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('数据源管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(dataSourcesProvider.notifier).refresh(),
            tooltip: '刷新',
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '数据源列表'),
            Tab(text: '连接测试'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          asyncSources.when(
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
                    onPressed: () => ref.read(dataSourcesProvider.notifier).refresh(),
                    child: const Text('重试'),
                  ),
                ],
              ),
            ),
            data: (sources) {
              if (sources.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_queue, size: 64, color: Colors.grey),
                      const SizedBox(height: 16),
                      const Text('暂无数据源', style: TextStyle(fontSize: 18, color: Colors.grey)),
                      const SizedBox(height: 8),
                      const Text('点击右下角 + 添加第一个数据源', style: TextStyle(color: Colors.grey)),
                      const SizedBox(height: 16),
                      FilledButton.icon(
                        onPressed: () => _showAddEditDialog(),
                        icon: const Icon(Icons.add),
                        label: const Text('添加数据源'),
                      ),
                    ],
                  ),
                );
              }
              return RefreshIndicator(
                onRefresh: () => ref.read(dataSourcesProvider.notifier).refresh(),
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: sources.length,
                  itemBuilder: (context, index) {
                    final source = sources[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: source.status == 'active'
                                ? const Color.fromARGB(25, 82, 196, 26)
                                : const Color.fromARGB(25, 158, 158, 158),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(
                            source.status == 'active' ? Icons.cloud_done : Icons.cloud_off,
                            color: source.status == 'active' ? AppConfig.successColor : Colors.grey,
                          ),
                        ),
                        title: Text(source.name, style: const TextStyle(fontWeight: FontWeight.w500)),
                        subtitle: Text('${_typeLabel(source.type)} · ${source.status == 'active' ? '活跃' : '不活跃'}'),
                        trailing: PopupMenuButton<String>(
                          onSelected: (action) {
                            switch (action) {
                              case 'edit':
                                _showAddEditDialog(existing: source);
                              case 'delete':
                                _deleteSource(source);
                            }
                          },
                          itemBuilder: (context) => [
                            const PopupMenuItem(value: 'edit', child: Text('编辑')),
                            const PopupMenuItem(
                              value: 'delete',
                              child: Text('删除', style: TextStyle(color: Colors.red)),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          ),
          _buildTestPanel(context),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddEditDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildTestPanel(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('数据源类型', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: ['ground_station', 'buoy', 'satellite', 'radar', 'weather_station'].map((type) {
                      return ChoiceChip(
                        label: Text(_typeLabel(type)),
                        selected: false,
                        onSelected: (_) {},
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('上传测试文件', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.upload_file),
                    label: const Text('选择文件'),
                  ),
                  const SizedBox(height: 4),
                  const Text('支持格式: CSV, JSON, NetCDF, HDF5', style: TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('数据源连接测试完成'), backgroundColor: AppConfig.successColor),
              );
            },
            icon: const Icon(Icons.play_arrow),
            label: const Text('执行测试'),
            style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          ),
        ],
      ),
    );
  }
}
