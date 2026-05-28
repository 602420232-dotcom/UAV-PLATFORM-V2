import 'package:flutter_test/flutter_test.dart';

import 'package:uav_path_planning_app/main.dart';

void main() {
  testWidgets('App renders smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const UAVApp());

    expect(find.text('无人机路径规划系统'), findsWidgets);
  });
}
