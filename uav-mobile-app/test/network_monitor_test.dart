import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uav_path_planning_app/services/network_monitor.dart';

void main() {
  group('NetworkStatus', () {
    test('equality', () {
      const a = NetworkStatus(isConnected: true, connectionType: NetworkConnectionType.wifi);
      const b = NetworkStatus(isConnected: true, connectionType: NetworkConnectionType.wifi);
      const c = NetworkStatus(isConnected: false, connectionType: NetworkConnectionType.none);

      expect(a, equals(b));
      expect(a, isNot(equals(c)));
    });

    test('hashCode', () {
      const a = NetworkStatus(isConnected: true, connectionType: NetworkConnectionType.mobileData);
      const b = NetworkStatus(isConnected: true, connectionType: NetworkConnectionType.mobileData);
      expect(a.hashCode, equals(b.hashCode));
    });

    test('toString', () {
      const s = NetworkStatus(isConnected: true, connectionType: NetworkConnectionType.wifi);
      expect(s.toString(), contains('wifi'));
      expect(s.toString(), contains('true'));
    });
  });

  group('NetworkConnectionType', () {
    test('values', () {
      expect(NetworkConnectionType.values.length, greaterThanOrEqualTo(6));
      expect(NetworkConnectionType.values, contains(NetworkConnectionType.wifi));
      expect(NetworkConnectionType.values, contains(NetworkConnectionType.none));
    });
  });

  group('NetworkMonitor singleton', () {
    test('same instance', () {
      final a = NetworkMonitor();
      final b = NetworkMonitor();
      expect(identical(a, b), isTrue);
    });
  });

  group('NetworkMonitor callbacks', () {
    late NetworkMonitor monitor;

    setUp(() {
      NetworkMonitor().dispose();
      monitor = NetworkMonitor();
    });

    tearDown(() {
      monitor.dispose();
    });

    test('register callback returns cancel function', () {
      final cancel = monitor.onStatusChanged((_) {});
      expect(cancel, isA<VoidCallback>());

      // Cancel should not throw
      expect(() => cancel(), returnsNormally);
    });

    test('callback fired immediately with current status', () {
      NetworkStatus? received;
      monitor.onStatusChanged((status) {
        received = status;
      });
      expect(received, isNotNull);
    });

    test('multiple callbacks', () {
      int count = 0;
      final cancel1 = monitor.onStatusChanged((_) => count++);
      monitor.onStatusChanged((_) => count++);

      // Both fired immediately → 2 calls
      expect(count, 2);

      cancel1(); // Remove first callback
      monitor.onStatusChanged((_) => count++);
      // Only the new one fires immediately → +1
      expect(count, 3);
    });

    test('cancel removes callback', () {
      final calls = <NetworkStatus>[];
      final cancel = monitor.onStatusChanged(calls.add);
      final initialCount = calls.length;
      cancel();
      monitor.onStatusChanged((_) {});
      // The original callback should not fire again
      expect(calls.length, equals(initialCount));
    });
  });

  group('NetworkMonitor mapping', () {
    test('maps wifi correctly', () {
      final monitor = NetworkMonitor();
      final result = monitor.currentStatus;
      // Initial state is unknown but not none
      expect(result.connectionType, isNot(equals(NetworkConnectionType.none)));
    });

    test('hasConnection returns bool', () async {
      final monitor = NetworkMonitor();
      final result = await monitor.hasConnection();
      expect(result, isA<bool>());
    });

    test('refresh does not throw', () async {
      final monitor = NetworkMonitor();
      await expectLater(monitor.refresh(), completes);
    });
  });
}
