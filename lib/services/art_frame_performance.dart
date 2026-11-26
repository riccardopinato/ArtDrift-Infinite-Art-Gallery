import 'dart:collection';
import 'dart:ui' show FrameTiming;

import 'package:flutter/painting.dart';
import 'package:flutter/scheduler.dart';

/// Local, opt-in frame diagnostics. Never uploads data or samples media.
class ArtFramePerformance {
  ArtFramePerformance._() {
    _callback = _record;
  }
  static final ArtFramePerformance instance = ArtFramePerformance._();

  static const int maxSamples = 3600;
  final Queue<double> _frameMs = Queue<double>();
  late final void Function(List<FrameTiming>) _callback;
  bool _isRecording = false;

  bool get isRecording => _isRecording;

  void start() {
    if (_isRecording) return;
    _frameMs.clear();
    _isRecording = true;
    SchedulerBinding.instance.addTimingsCallback(_callback);
  }

  void stop() {
    if (!_isRecording) return;
    SchedulerBinding.instance.removeTimingsCallback(_callback);
    _isRecording = false;
  }

  void clear() => _frameMs.clear();

  void _record(List<FrameTiming> timings) {
    if (!_isRecording) return;
    for (final timing in timings) {
      final spanMs = timing.totalSpan.inMicroseconds / 1000.0;
      if (!spanMs.isFinite || spanMs < 0) continue;
      _frameMs.addLast(spanMs);
      if (_frameMs.length > maxSamples) _frameMs.removeFirst();
    }
  }

  ArtFrameSnapshot snapshot() => ArtFrameSnapshot.fromDurations(
    _frameMs,
    decodedImageBytes: PaintingBinding.instance.imageCache.currentSizeBytes,
  );
}

/// Frame-time distributions are *not* network speed or a device RAM metric.
/// Over-16.7ms thresholds are only a 60Hz reference, not measured dropped frames
/// on high-refresh panels. No fictitious FPS are derived from frame durations.
class ArtFrameSnapshot {
  const ArtFrameSnapshot({
    required this.samples,
    required this.p50Ms,
    required this.p95Ms,
    required this.p99Ms,
    required this.over16Ms,
    required this.over33Ms,
    required this.decodedImageBytes,
  });

  final int samples;
  final double p50Ms;
  final double p95Ms;
  final double p99Ms;
  final int over16Ms;
  final int over33Ms;
  final int decodedImageBytes;

  static ArtFrameSnapshot fromDurations(Iterable<double> durations,
      {int decodedImageBytes = 0}) {
    final sorted = durations.where((ms) => ms.isFinite && ms >= 0).toList()
      ..sort();
    if (sorted.isEmpty) {
      return ArtFrameSnapshot(samples: 0, p50Ms: 0, p95Ms: 0,
        p99Ms: 0, over16Ms: 0, over33Ms: 0,
        decodedImageBytes: decodedImageBytes);
    }
    double percentile(double q) {
      final index = ((sorted.length - 1) * q).ceil();
      return sorted[index];
    }
    return ArtFrameSnapshot(
      samples: sorted.length,
      p50Ms: percentile(.50),
      p95Ms: percentile(.95),
      p99Ms: percentile(.99),
      over16Ms: sorted.where((ms) => ms > 16.67).length,
      over33Ms: sorted.where((ms) => ms > 33.33).length,
      decodedImageBytes: decodedImageBytes,
    );
  }

  String get report => [
    'Art Drift — local Android frame diagnostics',
    'Sampled frames: $samples',
    'Frame totalSpan p50: ${p50Ms.toStringAsFixed(2)} ms',
    'Frame totalSpan p95: ${p95Ms.toStringAsFixed(2)} ms',
    'Frame totalSpan p99: ${p99Ms.toStringAsFixed(2)} ms',
    'Frames >16.67ms (60Hz reference only): $over16Ms',
    'Frames >33.33ms: $over33Ms',
    'Decoded Flutter image cache: ${(decodedImageBytes / 1048576).toStringAsFixed(1)} MiB',
    'Not total device RAM, actual FPS or a visual-zero-hole certification.',
  ].join('\n');
}
