import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/services/art_frame_performance.dart';

void main() {
  test('reports exact sample counts and monotonic percentiles', () {
    final summary = ArtFrameSnapshot.fromDurations(
      [8, 12, 17, 22, 35, 48, double.nan, double.infinity, -3],
      decodedImageBytes: 12 * 1024 * 1024,
    );
    expect(summary.samples, 6);
    expect(summary.p50Ms, lessThanOrEqualTo(summary.p95Ms));
    expect(summary.p95Ms, lessThanOrEqualTo(summary.p99Ms));
    expect(summary.over16Ms, 4);
    expect(summary.over33Ms, 2);
    expect(summary.report, contains('12.0 MiB'));
    expect(summary.report, contains('Not total device RAM'));
  });

  test('empty frame capture is a truthful zero-sample report', () {
    final summary = ArtFrameSnapshot.fromDurations(const []);
    expect(summary.samples, 0);
    expect(summary.p95Ms, 0);
    expect(summary.over16Ms, 0);
  });
}
