import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'world_layout.dart';

/// One full-screen canvas. The widget tree contains only visible artwork tiles.
/// A detail route does not dispose this view or reset its camera.
class DriftCanvas<T> extends StatefulWidget {
  const DriftCanvas({super.key, required this.items, required this.onOpen,
    required this.tileBuilder, required this.cameraKey,
    required this.compactBrand, required this.fullBrand,
    required this.hintText, required this.recenterTooltip});

  final List<T> items;
  final ValueChanged<T> onOpen;
  final Widget Function(BuildContext, T, double) tileBuilder;
  final String cameraKey, compactBrand, fullBrand, hintText, recenterTooltip;

  @override
  State<DriftCanvas<T>> createState() => _DriftCanvasState<T>();
}

class _DriftCanvasState<T> extends State<DriftCanvas<T>>
    with SingleTickerProviderStateMixin {
  final _world = const InfiniteWorld();
  late final AnimationController _momentum;
  Offset _offset = Offset.zero;
  Offset _worldAtGestureStart = Offset.zero;
  Offset _flingFrom = Offset.zero;
  Offset _flingDistance = Offset.zero;
  double _zoom = 1;
  double _zoomAtGestureStart = 1;
  bool _cameraInitialized = false;
  Size _viewport = Size.zero;

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
    _restoreCamera();
  }

  Future<void> _restoreCamera() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted || !prefs.containsKey(widget.cameraKey + '.x')) return;
    setState(() {
      _offset = Offset(prefs.getDouble(widget.cameraKey + '.x') ?? 0,
          prefs.getDouble(widget.cameraKey + '.y') ?? 0);
      _zoom = (prefs.getDouble(widget.cameraKey + '.zoom') ?? 1)
          .clamp(0.55, 2.7).toDouble();
      _cameraInitialized = true;
    });
  }

  Future<void> _saveCamera() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(widget.cameraKey + '.x', _offset.dx);
    await prefs.setDouble(widget.cameraKey + '.y', _offset.dy);
    await prefs.setDouble(widget.cameraKey + '.zoom', _zoom);
  }

  void _resetCamera() {
    _momentum.stop();
    setState(() {
      _offset = Offset(_viewport.width / 2, _viewport.height / 2);
      _zoom = 1;
    });
    _saveCamera();
  }

  void _start(ScaleStartDetails details) {
    _momentum.stop();
    _zoomAtGestureStart = _zoom;
    _worldAtGestureStart = (details.localFocalPoint - _offset) / _zoom;
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

  @override
  void dispose() {
    _momentum.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      _viewport = Size(constraints.maxWidth, constraints.maxHeight);
      if (!_cameraInitialized) {
        _offset = Offset(_viewport.width / 2, _viewport.height / 2);
        _cameraInitialized = true;
      }
      // Only draw what the user can see, plus a narrow prefetch margin.
      final bounds = Rect.fromLTRB(
        (-_offset.dx - 240) / _zoom,
        (-_offset.dy - 240) / _zoom,
        (_viewport.width - _offset.dx + 240) / _zoom,
        (_viewport.height - _offset.dy + 240) / _zoom,
      );
      final tiles = _world.visible(bounds, widget.items.length);
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
                    onTap: () => widget.onOpen(widget.items[tile.artworkIndex]),
                    child: ColoredBox(
                      color: const Color(0xFF24232A),
                      child: widget.tileBuilder(context, widget.items[tile.artworkIndex], _zoom),
                    ),
                  ),
                ),
            ]),
          ),
        ),
        Positioned(
          left: 19, top: 14,
          child: IgnorePointer(
            child: SafeArea(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xB5101015),
                  borderRadius: BorderRadius.circular(6)),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  child: Text(_viewport.width < 460 ? widget.compactBrand : widget.fullBrand,
                    style: TextStyle(color: Colors.white,
                      fontSize: _viewport.width < 460 ? 16 : 18,
                      letterSpacing: -0.5, fontWeight: FontWeight.w700)),
                ),
              ),
            ),
          ),
        ),
        Positioned(
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
        Positioned(
          bottom: 16, left: 16, right: 16,
          child: SafeArea(
            top: false,
            child: IgnorePointer(
              child: Center(child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xB8111116),
                  borderRadius: BorderRadius.circular(30)),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 17, vertical: 9),
                  child: Text(widget.hintText,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white70, fontSize: 11)),
                ),
              )),
            ),
          ),
        ),
      ]);
    });
  }
}
