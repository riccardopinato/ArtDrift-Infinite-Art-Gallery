import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'world_layout.dart';

/// Optional, source-owned warmup for artwork or local-device thumbnails.
/// Implementations must bound I/O and memory; the core never reads user files.
typedef DriftPrefetchItem<T> = Future<void> Function(
    BuildContext context, T item, double zoom);

/// Infinite mosaic shared by Art Drift and Gallery Drift.
/// Camera/world mapping and tile identity remain unchanged.
class DriftCanvas<T> extends StatefulWidget {
  const DriftCanvas({
    super.key,
    required this.items,
    required this.onOpen,
    required this.tileBuilder,
    required this.cameraKey,
    required this.compactBrand,
    required this.fullBrand,
    required this.hintText,
    required this.recenterTooltip,
    this.prefetchItem,
    this.onOpenAtRect,
    this.onTileLongPress,
    this.onCanvasGestureStart,
    this.onImmersiveChanged,
    this.museumControls = false,
  });

  final List<T> items;
  final ValueChanged<T> onOpen;
  final Widget Function(BuildContext, T, double) tileBuilder;
  final String cameraKey, compactBrand, fullBrand, hintText, recenterTooltip;
  final DriftPrefetchItem<T>? prefetchItem;

  /// Optional source-app presentation hooks. Rect is in viewport-local
  /// coordinates; all previous callers remain source-agnostic.
  final void Function(T item, Rect viewportRect)? onOpenAtRect;
  final void Function(T item, Rect viewportRect)? onTileLongPress;
  final VoidCallback? onCanvasGestureStart;
  final ValueChanged<bool>? onImmersiveChanged;
  /// The default is false to preserve Gallery Drift's existing controls.
  final bool museumControls;

  @override
  State<DriftCanvas<T>> createState() => _DriftCanvasState<T>();
}

class _DriftCanvasState<T> extends State<DriftCanvas<T>>
    with TickerProviderStateMixin {
  final _world = const InfiniteWorld();
  late final AnimationController _momentum;
  late final Ticker _autoTicker;
  Duration? _lastAutoFrame;
  Timer? _dimTimer;
  Timer? _prefetchTimer;
  Rect _prefetchBounds = Rect.zero;
  Offset? _previousPrefetchCenter;
  Offset _movementSincePrefetch = Offset.zero;
  final Set<String> _warmKeys = <String>{};
  final List<String> _warmOrder = <String>[];

  Offset _offset = Offset.zero;
  Offset _worldAtGestureStart = Offset.zero;
  Offset _flingFrom = Offset.zero;
  Offset _flingDistance = Offset.zero;
  double _zoom = 1;
  double _zoomAtGestureStart = 1;
  bool _cameraInitialized = false;
  bool _autoRunning = false;
  bool _controlsDimmed = false;
  bool _museumImmersive = false;
  bool _museumSpeedMenuOpen = false;
  int _autoSpeed = 25;
  Size _viewport = Size.zero;

  static const int _prefetchBatchSize = 8;
  static const int _warmHistoryLimit = 256;

  @visibleForTesting
  static int nextSpeed(int current) => current >= 100 ? 25 : current + 25;

  @visibleForTesting
  static double speedPixelsPerSecond(int percent) =>
      (percent.clamp(25, 100) / 25) * 36.0;

  @override
  void initState() {
    super.initState();
    _momentum = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 450),
    )..addListener(() {
        if (!mounted) return;
        final progress = Curves.decelerate.transform(_momentum.value);
        setState(() => _offset = _flingFrom + _flingDistance * progress);
      });
    _autoTicker = createTicker(_tickAuto);
    _scheduleDim();
    _restoreCamera();
  }

  void _scheduleDim() {
    _dimTimer?.cancel();
    _dimTimer = Timer(const Duration(seconds: 3), () {
      if (mounted) setState(() => _controlsDimmed = true);
    });
  }

  void _activateControls() {
    if (_controlsDimmed) setState(() => _controlsDimmed = false);
    _scheduleDim();
  }

  void _tickAuto(Duration elapsed) {
    if (!_autoRunning || !mounted) return;
    final previous = _lastAutoFrame;
    if (previous == null) {
      _lastAutoFrame = elapsed;
      return;
    }
    // Accumulate short 60/90/120 Hz frames. Updating the reference timestamp
    // before this gate would discard every sub-30 ms frame and freeze Auto.
    final elapsedSinceMove = elapsed - previous;
    if (elapsedSinceMove < const Duration(milliseconds: 30)) return;
    _lastAutoFrame = elapsed;
    // Cap long suspended frames: no sudden jump when a tab becomes active.
    final seconds = (elapsedSinceMove.inMicroseconds / 1000000.0)
        .clamp(0.0, 0.05);
    if (seconds <= 0) return;
    // Move the artwork up so the camera explores new rows below it.
    setState(() => _offset = Offset(
      _offset.dx, _offset.dy - speedPixelsPerSecond(_autoSpeed) * seconds));
  }

  void _pauseAuto() {
    if (!_autoRunning) return;
    _autoTicker.stop();
    _lastAutoFrame = null;
    _autoRunning = false;
    _saveCamera();
  }

  void _toggleAuto() {
    _activateControls();
    _momentum.stop();
    setState(() {
      if (_autoRunning) {
        _pauseAuto();
      } else {
        _autoRunning = true;
        _lastAutoFrame = null;
        _autoTicker.start();
      }
    });
  }

  Future<void> _chooseSpeed(int speed) async {
    if (!const [25, 50, 75, 100].contains(speed)) return;
    _activateControls();
    setState(() {
      _autoSpeed = speed;
      _museumSpeedMenuOpen = false;
    });
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('${widget.cameraKey}.autoSpeed', speed);
  }

  Future<void> _changeSpeed() => _chooseSpeed(nextSpeed(_autoSpeed));

  void _toggleMuseumImmersive() {
    if (!widget.museumControls) return;
    setState(() {
      _museumImmersive = !_museumImmersive;
      _museumSpeedMenuOpen = false;
    });
    widget.onImmersiveChanged?.call(_museumImmersive);
  }

  Future<void> _restoreCamera() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    final speed = prefs.getInt('${widget.cameraKey}.autoSpeed');
    setState(() {
      if (speed != null && const [25, 50, 75, 100].contains(speed)) {
        _autoSpeed = speed;
      }
      if (prefs.containsKey('${widget.cameraKey}.x')) {
        _offset = Offset(
          prefs.getDouble('${widget.cameraKey}.x') ?? 0,
          prefs.getDouble('${widget.cameraKey}.y') ?? 0);
        _zoom = (prefs.getDouble('${widget.cameraKey}.zoom') ?? 1)
            .clamp(0.55, 2.7).toDouble();
        _cameraInitialized = true;
      }
    });
  }

  Future<void> _saveCamera() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('${widget.cameraKey}.x', _offset.dx);
    await prefs.setDouble('${widget.cameraKey}.y', _offset.dy);
    await prefs.setDouble('${widget.cameraKey}.zoom', _zoom);
  }

  void _resetCamera() {
    _pauseAuto();
    _momentum.stop();
    setState(() {
      _offset = Offset(_viewport.width / 2, _viewport.height / 2);
      _zoom = 1;
    });
    _saveCamera();
  }

  void _start(ScaleStartDetails details) {
    if (_museumSpeedMenuOpen) setState(() => _museumSpeedMenuOpen = false);
    widget.onCanvasGestureStart?.call();
    _pauseAuto(); // A manual gesture always has priority.
    _momentum.stop();
    _zoomAtGestureStart = _zoom;
    _worldAtGestureStart = (details.localFocalPoint - _offset) / _zoom;
    _activateControls();
  }

  void _update(ScaleUpdateDetails details) {
    final nextZoom = (_zoomAtGestureStart * details.scale)
        .clamp(0.55, 2.7).toDouble();
    setState(() {
      _zoom = nextZoom;
      _offset = details.localFocalPoint - _worldAtGestureStart * nextZoom;
    });
  }

  void _end(ScaleEndDetails details) {
    final velocity = details.velocity.pixelsPerSecond;
    if (velocity.distance > 150) {
      _flingFrom = _offset;
      _flingDistance = Offset(
        (velocity.dx * 0.22).clamp(-350.0, 350.0),
        (velocity.dy * 0.22).clamp(-350.0, 350.0));
      _momentum.forward(from: 0).whenComplete(_saveCamera);
    } else {
      _saveCamera();
    }
  }

  void _queuePrefetch(Rect visible) {
    if (widget.prefetchItem == null || widget.items.isEmpty) return;
    _prefetchBounds = visible;
    // Accumulate movement during the batching window: a single 60/120 Hz
    // frame is too small to indicate direction accurately.
    final previous = _previousPrefetchCenter;
    if (previous != null) {
      final delta = visible.center - previous;
      if (delta.distanceSquared < visible.longestSide * visible.longestSide) {
        _movementSincePrefetch += delta;
      }
    }
    _previousPrefetchCenter = visible.center;
    if (_prefetchTimer != null) return;
    _prefetchTimer = Timer(const Duration(milliseconds: 260), () {
      _prefetchTimer = null;
      if (mounted) _warmNearby(_prefetchBounds);
    });
  }

  void _warmNearby(Rect visible) {
    final prefetch = widget.prefetchItem;
    if (!mounted || prefetch == null || widget.items.isEmpty ||
        visible.isEmpty) return;
    final movement = _movementSincePrefetch;
    _movementSincePrefetch = Offset.zero;
    final nearby = DriftPrefetchPlan.window(
        visible, movement, auto: _autoRunning);
    final focus = DriftPrefetchPlan.focus(
        visible, movement, auto: _autoRunning);
    final priority = Rect.fromCenter(
        center: focus, width: visible.width, height: visible.height);
    final futureTiles = _world.visible(nearby, widget.items.length,
        limit: 240, priorityViewport: priority);
    futureTiles.sort((a, b) {
      final aDelta = (a.rect.center - focus).distanceSquared;
      final bDelta = (b.rect.center - focus).distanceSquared;
      return aDelta.compareTo(bDelta);
    });
    var warmed = 0;
    final tier = _zoom > 1.65 ? 2 : 1;
    for (final tile in futureTiles) {
      if (warmed >= _prefetchBatchSize) break;
      final key = '${tile.artworkIndex}:$tier';
      if (!_warmKeys.add(key)) continue;
      _warmOrder.add(key);
      if (_warmOrder.length > _warmHistoryLimit) {
        _warmKeys.remove(_warmOrder.removeAt(0));
      }
      warmed++;
      // No dependency on any museum API, photo permission, or decoder here.
      unawaited(Future.sync(() =>
          prefetch(context, widget.items[tile.artworkIndex], _zoom))
          .catchError((Object error, StackTrace trace) {}));
    }
    if (warmed == _prefetchBatchSize) _queuePrefetch(visible);
  }

  @override
  void didUpdateWidget(covariant DriftCanvas<T> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(oldWidget.items, widget.items)) {
      _warmKeys.clear();
      _warmOrder.clear();
      _previousPrefetchCenter = null;
      _movementSincePrefetch = Offset.zero;
    }
  }

  @override
  void dispose() {
    _autoTicker.dispose();
    _momentum.dispose();
    _dimTimer?.cancel();
    _prefetchTimer?.cancel();
    super.dispose();
  }

  Widget _autoControls() {
    if (widget.museumControls) return _museumAutoControls();
    final label = _autoRunning ? 'Pausa' : 'Auto';
    final labelIcon = _autoRunning ? Icons.pause_rounded : Icons.play_arrow_rounded;
    return AnimatedOpacity(
      duration: const Duration(milliseconds: 350),
      opacity: _controlsDimmed ? 0.32 : 1.0,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Tooltip(
          message: _autoRunning ? 'Ferma lo scorrimento automatico' :
              'Avvia lo scorrimento automatico',
          child: SizedBox(height: 40, width: 104,
            child: FilledButton(
              key: const ValueKey('drift-auto-toggle'),
              onPressed: _toggleAuto,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 5),
                backgroundColor: const Color(0xE51B1B22),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  side: BorderSide(color: _autoRunning
                      ? const Color(0xFFE5C8A5) : Colors.white24),
                  borderRadius: BorderRadius.circular(9))),
              child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                Icon(labelIcon, size: 17),
                const SizedBox(width: 4),
                Text(label, style: const TextStyle(fontSize: 12)),
              ]))),
        ),
        const SizedBox(height: 5),
        Tooltip(
          message: 'Velocità scorrimento automatico: premi per cambiare',
          child: SizedBox(height: 37, width: 68,
            child: OutlinedButton(
              key: const ValueKey('drift-auto-speed'),
              onPressed: _changeSpeed,
              style: OutlinedButton.styleFrom(
                backgroundColor: const Color(0xD91B1B22),
                foregroundColor: Colors.white,
                padding: EdgeInsets.zero,
                side: const BorderSide(color: Colors.white30),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8))),
              child: Text('$_autoSpeed%',
                style: const TextStyle(
                  fontSize: 12, fontWeight: FontWeight.w600)))),
        ),
      ]),
    );
  }

  Widget _museumAutoControls() => AnimatedOpacity(
    duration: const Duration(milliseconds: 350),
    opacity: _controlsDimmed ? .28 : 1.0,
    child: Row(
    mainAxisSize: MainAxisSize.min, children: [
      SizedBox(height: 40, width: 89, child: TextButton.icon(
        key: const ValueKey('drift-auto-toggle'),
        onPressed: _toggleAuto,
        style: TextButton.styleFrom(
          backgroundColor: const Color(0xE51B1B22),
          foregroundColor: const Color(0xFFF1E3CE),
          side: BorderSide(color: _autoRunning
              ? const Color(0xFFE5C8A5) : Colors.white30),
          padding: const EdgeInsets.symmetric(horizontal: 4)),
        icon: Icon(_autoRunning ? Icons.pause_rounded
            : Icons.play_arrow_rounded, size: 17),
        label: Text(_autoRunning ? 'Pausa' : 'Auto',
          style: const TextStyle(fontSize: 12)),
      )),
      const SizedBox(width: 7),
      SizedBox(height: 40, width: 65, child: OutlinedButton(
        key: const ValueKey('drift-auto-speed'),
        onPressed: () {
          _activateControls();
          setState(() => _museumSpeedMenuOpen = !_museumSpeedMenuOpen);
        },
        style: OutlinedButton.styleFrom(
          backgroundColor: const Color(0xD91B1B22),
          foregroundColor: const Color(0xFFF1E3CE),
          padding: EdgeInsets.zero,
          side: const BorderSide(color: Colors.white30)),
        child: Text('$_autoSpeed% ▾',
          style: const TextStyle(fontSize: 11)),
      )),
    ]),
  );

  Widget _museumSpeedMenu() => Material(
    elevation: 8,
    color: const Color(0xFFF1E5D0),
    child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 202),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(12, 9, 12, 5),
          child: Text('IL RITMO DELLA VISITA',
            style: TextStyle(fontSize: 9,
              letterSpacing: 1.4, color: Color(0xFF907149)))),
        for (final speed in const [25, 50, 75, 100])
          SizedBox(height: 42, width: 202, child: TextButton(
            key: ValueKey('drift-museum-speed-$speed'),
            onPressed: () => _chooseSpeed(speed),
            style: TextButton.styleFrom(
              alignment: Alignment.centerLeft,
              foregroundColor: const Color(0xFF58432E)),
            child: Text(
              '${speed == 25 ? 'Lento' : speed == 50 ? 'Regolare' : speed == 75 ? 'Veloce' : 'Molto veloce'} · $speed%',
              style: TextStyle(fontSize: 12,
                fontWeight: _autoSpeed == speed
                    ? FontWeight.bold : FontWeight.normal)),
          )),
      ]),
    ),
  );

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      _viewport = Size(constraints.maxWidth, constraints.maxHeight);
      if (!_cameraInitialized) {
        _offset = Offset(_viewport.width / 2, _viewport.height / 2);
        _cameraInitialized = true;
      }
      // Narrow render overdraw stays bounded; separate prefetch is farther out.
      final bounds = Rect.fromLTRB(
        (-_offset.dx - 240) / _zoom,
        (-_offset.dy - 240) / _zoom,
        (_viewport.width - _offset.dx + 240) / _zoom,
        (_viewport.height - _offset.dy + 240) / _zoom,
      );
      final actualViewport = Rect.fromLTRB(
        -_offset.dx / _zoom, -_offset.dy / _zoom,
        (_viewport.width - _offset.dx) / _zoom,
        (_viewport.height - _offset.dy) / _zoom,
      );
      final tiles = _world.visible(bounds, widget.items.length,
          priorityViewport: actualViewport);
      _queuePrefetch(actualViewport);
      return Stack(fit: StackFit.expand, children: [
        GestureDetector(
          behavior: HitTestBehavior.opaque,
          onScaleStart: _start,
          onScaleUpdate: _update,
          onScaleEnd: _end,
          child: ClipRect(
            child: Stack(children: [
              for (final tile in tiles)
                Positioned(
                  key: ValueKey(tile.key),
                  left: tile.rect.left * _zoom + _offset.dx,
                  top: tile.rect.top * _zoom + _offset.dy,
                  width: tile.rect.width * _zoom,
                  height: tile.rect.height * _zoom,
                  child: GestureDetector(
                    onTap: () {
                      _pauseAuto();
                      final item = widget.items[tile.artworkIndex];
                      final onOpenAtRect = widget.onOpenAtRect;
                      if (onOpenAtRect != null) {
                        onOpenAtRect(item, Rect.fromLTWH(
                          tile.rect.left * _zoom + _offset.dx,
                          tile.rect.top * _zoom + _offset.dy,
                          tile.rect.width * _zoom,
                          tile.rect.height * _zoom));
                      } else {
                        widget.onOpen(item);
                      }
                    },
                    onLongPress: widget.onTileLongPress == null
                      ? null : () {
                          _pauseAuto();
                          widget.onTileLongPress!(
                            widget.items[tile.artworkIndex], Rect.fromLTWH(
                              tile.rect.left * _zoom + _offset.dx,
                              tile.rect.top * _zoom + _offset.dy,
                              tile.rect.width * _zoom,
                              tile.rect.height * _zoom));
                        },
                    child: ColoredBox(
                      color: const Color(0xFF24232A),
                      child: widget.tileBuilder(context,
                          widget.items[tile.artworkIndex], _zoom),
                    ),
                  ),
                ),
            ]),
          ),
        ),
        if (!_museumImmersive) Positioned(
          left: 19, top: 14,
          child: SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IgnorePointer(child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xB5101015),
                    borderRadius: BorderRadius.circular(6)),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 8),
                    child: Text(_viewport.width < 460
                        ? widget.compactBrand : widget.fullBrand,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: _viewport.width < 460 ? 16 : 18,
                        letterSpacing: -0.5, fontWeight: FontWeight.w700)),
                  ),
                )),
                const SizedBox(height: 6),
                _autoControls(),
              ],
            ),
          ),
        ),
        if (widget.museumControls && _museumSpeedMenuOpen && !_museumImmersive)
          Positioned(left: 19, top: 133,
            child: _museumSpeedMenu()),
        if (widget.museumControls)
          Positioned(left: 16, bottom: 73,
            child: SafeArea(top: false, child: TextButton(
              key: const ValueKey('drift-museum-immersive'),
              onPressed: _toggleMuseumImmersive,
              style: TextButton.styleFrom(
                foregroundColor: const Color(0xFFF1E3CE),
                backgroundColor: const Color(0xE31B1B22),
                side: const BorderSide(color: Color(0xFF9F805B))),
              child: Text(_museumImmersive
                  ? '◎ Mostra comandi' : '◌ Immersione',
                style: const TextStyle(fontSize: 11)),
            ))),
        if (!_museumImmersive) Positioned(
          right: 16, bottom: 73,
          child: SafeArea(top: false,
            child: Tooltip(
              message: widget.recenterTooltip,
              child: IconButton.filledTonal(
                onPressed: _resetCamera,
                icon: const Icon(Icons.center_focus_strong),
                style: IconButton.styleFrom(
                  backgroundColor: const Color(0xC71B1B22),
                  foregroundColor: Colors.white),
              ),
            ),
          ),
        ),
        if (!_museumImmersive) Positioned(
          bottom: 16, left: 16, right: 16,
          child: SafeArea(
            top: false,
            child: IgnorePointer(
              child: Center(child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xB8111116),
                  borderRadius: BorderRadius.circular(30)),
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 17, vertical: 9),
                  child: Text(widget.hintText,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: Colors.white70, fontSize: 11)),
                ),
              )),
            ),
          ),
        ),
      ]);
    });
  }
}
