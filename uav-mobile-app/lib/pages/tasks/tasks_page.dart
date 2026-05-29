import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/app_config.dart';
import '../../models/task.dart';
import '../../providers/app_providers.dart';

class TasksPage extends ConsumerStatefulWidget {
  const TasksPage({super.key});

  @override
  ConsumerState<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends ConsumerState<TasksPage> {
  List<TaskModel> get tasks {
    final asyncVal = ref.watch(tasksProvider);
    return asyncVal.valueOrNull ?? [];
  }

  Color _statusColor(String status) {
    switch (status) {
      case '待分配':
        return AppConfig.infoColor;
      case '已分配':
        return AppConfig.warningColor;
      case '执行中':
        return Colors.purple;
      case '已完成':
        return AppConfig.successColor;
      case '已取消':
        return AppConfig.errorColor;
      default:
        return Colors.grey;
    }
  }

  Color _priorityColor(String priority) {
    switch (priority) {
      case '高':
        return AppConfig.errorColor;
      case '中':
        return AppConfig.warningColor;
      case '低':
        return AppConfig.successColor;
      default:
        return Colors.grey;
    }
  }

  String _typeLabel(String type) {
    switch (type) {
      case 'delivery':
        return '配送';
      case 'inspection':
        return '巡检';
      case 'rescue':
        return '救援';
      case 'survey':
        return '测绘';
      default:
        return type;
    }
  }

  Future<void> _showAddEditDialog({TaskModel? existing}) async {
    final nameCtrl = TextEditingController(text: existing?.name ?? '');
    final descCtrl = TextEditingController(text: existing?.description ?? '');
    var type = existing?.type ?? 'delivery';
    var priority = existing?.priority ?? '中';

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(existing != null ? '编辑任务' : '新建任务'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: '任务名称', hintText: '例: 市区物流配送'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: descCtrl,
                  decoration: const InputDecoration(labelText: '描述', hintText: '可选'),
                  maxLines: 2,
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: type,
                  decoration: const InputDecoration(labelText: '任务类型'),
                  items: const [
                    DropdownMenuItem(value: 'delivery', child: Text('配送')),
                    DropdownMenuItem(value: 'inspection', child: Text('巡检')),
                    DropdownMenuItem(value: 'rescue', child: Text('救援')),
                    DropdownMenuItem(value: 'survey', child: Text('测绘')),
                  ],
                  onChanged: (v) => setDialogState(() => type = v ?? type),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: priority,
                  decoration: const InputDecoration(labelText: '优先级'),
                  items: const [
                    DropdownMenuItem(value: '高', child: Text('高', style: TextStyle(color: AppConfig.errorColor))),
                    DropdownMenuItem(value: '中', child: Text('中', style: TextStyle(color: AppConfig.warningColor))),
                    DropdownMenuItem(value: '低', child: Text('低', style: TextStyle(color: AppConfig.successColor))),
                  ],
                  onChanged: (v) => setDialogState(() => priority = v ?? priority),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
            FilledButton(
              onPressed: nameCtrl.text.trim().isEmpty ? null : () => Navigator.pop(ctx, true),
              child: Text(existing != null ? '保存' : '创建'),
            ),
          ],
        ),
      ),
    );

    if (result != true) return;

    final task = TaskModel(
      id: existing?.id ?? 'T-${DateTime.now().millisecondsSinceEpoch}',
      name: nameCtrl.text.trim(),
      type: type,
      status: existing?.status ?? '待分配',
      priority: priority,
      description: descCtrl.text.trim().isEmpty ? null : descCtrl.text.trim(),
      waypoints: existing?.waypoints ?? [],
      createdAt: existing?.createdAt ?? DateTime.now(),
      completionTime: existing?.completionTime,
    );

    try {
      if (existing != null) {
        await ref.read(tasksProvider.notifier).updateTask(existing.id, task);
      } else {
        await ref.read(tasksProvider.notifier).addTask(task);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('操作失败: $e'), backgroundColor: AppConfig.errorColor),
        );
      }
    }
  }

  Future<void> _deleteTask(TaskModel task) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('确认删除'),
        content: Text('确定要删除 "${task.name}" 吗？'),
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
      await ref.read(tasksProvider.notifier).removeTask(task.id);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('删除失败: $e'), backgroundColor: AppConfig.errorColor),
        );
      }
    }
  }

  Future<void> _updateStatus(TaskModel task, String newStatus) async {
    try {
      await ref.read(tasksProvider.notifier).updateTask(
            task.id,
            task.copyWith(status: newStatus, completionTime: newStatus == '已完成' ? DateTime.now() : null),
          );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('状态更新失败: $e'), backgroundColor: AppConfig.errorColor),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final asyncTasks = ref.watch(tasksProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('任务管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(tasksProvider.notifier).refresh(),
            tooltip: '刷新',
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddEditDialog(),
            tooltip: '添加任务',
          ),
        ],
      ),
      body: asyncTasks.when(
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
                onPressed: () => ref.read(tasksProvider.notifier).refresh(),
                child: const Text('重试'),
              ),
            ],
          ),
        ),
        data: (tasks) {
          if (tasks.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.task_alt, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('暂无任务', style: TextStyle(fontSize: 18, color: Colors.grey)),
                  const SizedBox(height: 8),
                  const Text('点击右下角 + 创建第一个任务', style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: () => _showAddEditDialog(),
                    icon: const Icon(Icons.add),
                    label: const Text('创建任务'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => ref.read(tasksProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: tasks.length,
              itemBuilder: (context, index) => _buildTaskCard(context, tasks[index]),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddEditDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildTaskCard(BuildContext context, TaskModel task) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showTaskDetail(context, task),
        onLongPress: () => _showTaskContextMenu(context, task),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(task.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color.fromARGB(38, 22, 119, 255),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(task.status, style: TextStyle(color: _statusColor(task.status), fontSize: 12)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _infoChip(Icons.label_outline, _typeLabel(task.type)),
                  const SizedBox(width: 8),
                  _infoChip(Icons.flag_outlined, '${task.priority}优先级', color: _priorityColor(task.priority)),
                  const SizedBox(width: 8),
                  _infoChip(Icons.location_on_outlined, '${task.waypoints.length} 个航点'),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('创建: ${_formatTime(task.createdAt)}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  if (task.completionTime != null)
                    Text('完成: ${_formatTime(task.completionTime!)}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _infoChip(IconData icon, String text, {Color? color}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color ?? Colors.grey),
        const SizedBox(width: 3),
        Text(text, style: TextStyle(color: color ?? Colors.grey, fontSize: 12)),
      ],
    );
  }

  void _showTaskContextMenu(BuildContext context, TaskModel task) {
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
                _showAddEditDialog(existing: task);
              },
            ),
            if (task.status == '待分配' || task.status == '已分配')
              ListTile(
                leading: const Icon(Icons.play_arrow, color: AppConfig.successColor),
                title: const Text('开始执行'),
                onTap: () {
                  Navigator.pop(ctx);
                  _updateStatus(task, '执行中');
                },
              ),
            if (task.status == '执行中')
              ListTile(
                leading: const Icon(Icons.check_circle, color: AppConfig.successColor),
                title: const Text('标记完成'),
                onTap: () {
                  Navigator.pop(ctx);
                  _updateStatus(task, '已完成');
                },
              ),
            if (task.status != '已完成' && task.status != '已取消')
              ListTile(
                leading: const Icon(Icons.cancel, color: AppConfig.warningColor),
                title: const Text('取消任务'),
                onTap: () {
                  Navigator.pop(ctx);
                  _updateStatus(task, '已取消');
                },
              ),
            ListTile(
              leading: const Icon(Icons.delete, color: AppConfig.errorColor),
              title: const Text('删除', style: TextStyle(color: AppConfig.errorColor)),
              onTap: () {
                Navigator.pop(ctx);
                _deleteTask(task);
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showTaskDetail(BuildContext context, TaskModel task) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.6,
          maxChildSize: 0.9,
          minChildSize: 0.4,
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
                      decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(task.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  _detailItem('任务ID', task.id),
                  _detailItem('类型', _typeLabel(task.type)),
                  _detailItem('状态', task.status),
                  _detailItem('优先级', task.priority),
                  _detailItem('航点数', '${task.waypoints.length}'),
                  if (task.description != null) _detailItem('描述', task.description!),
                  _detailItem('创建时间', _formatTime(task.createdAt)),
                  if (task.completionTime != null) _detailItem('完成时间', _formatTime(task.completionTime!)),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      if (task.status == '待分配' || task.status == '已分配')
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () {
                              Navigator.pop(context);
                              _updateStatus(task, '执行中');
                            },
                            icon: const Icon(Icons.play_arrow),
                            label: const Text('执行任务'),
                          ),
                        ),
                      if (task.status == '执行中')
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () {
                              Navigator.pop(context);
                              _updateStatus(task, '已完成');
                            },
                            icon: const Icon(Icons.check),
                            label: const Text('标记完成'),
                            style: ElevatedButton.styleFrom(backgroundColor: AppConfig.successColor),
                          ),
                        ),
                      if (task.status != '已完成') ...[
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () {
                              Navigator.pop(context);
                              _showAddEditDialog(existing: task);
                            },
                            icon: const Icon(Icons.edit),
                            label: const Text('编辑'),
                          ),
                        ),
                      ],
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

  Widget _detailItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(width: 80, child: Text(label, style: const TextStyle(color: Colors.grey))),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500))),
        ],
      ),
    );
  }

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}
