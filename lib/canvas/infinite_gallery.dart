import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/artwork.dart';
import 'world_layout.dart';

/// One full-screen canvas. The widget tree contains only visible artwork tiles.
/// A detail route does not dispose this view or reset its camera.
class InfiniteGallery extends StatefulWidget {
  const InfiniteGallery({super.key, required this.artworks, required this.onOpen});
  final List<Artwork> artworks;
  final ValueChanged<Artwork> onOpen;

  @override
  State<InfiniteGallery> createState() => _InfiniteGalleryState();
}

class _InfiniteGalleryState extends State<InfiniteGallery>
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
    if (!mounted || !prefs.containsKey('artdrift.camera.x')) return;
    setState(() {
      _offset = Offset(prefs.getDouble('artdrift.camera.x') ?? 0,
          prefs.getDouble('artdrift.camera.y') ?? 0);
      _zoom = (prefs.getDouble('artdrift.camera.zoom') ?? 1)
          .clamp(0.55, 2.7).toDouble();
      _cameraInitialized = true;
    });
  }

  Future<void> _saveCamera() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('artdrift.camera.x', _offset.dx);
    await prefs.setDouble('artdrift.camera.y', _offset.dy);
    await prefs.setDouble('artdrift.camera.zoom', _zoom);
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

  Widget _preview(Artwork art) {
    if (art.hasBundledPreview) {
      return Image.asset(
        art.bootstrapAsset,
        fit: BoxFit.cover,
        filterQuality: FilterQuality.low,
        cacheWidth: 240,
        gaplessPlayback: true,
        errorBuilder: (_, error, stack) => const ColoredBox(
          color: Color(0xFF24232A),
          child: Center(child: Icon(Icons.image_not_supported_outlined,
              color: Colors.white30, size: 22)),
        ),
      );
    }
    return const ColoredBox(
      color: Color(0xFF24232A),
      child: Center(child: Icon(Icons.image_not_supported_outlined,
          color: Colors.white30, size: 22)),
    );
  }

  Widget _tileImage(Artwork art) {
    // Real bundled WebP previews show on the very first frame even offline.
    // Zooming in opts into a higher-detail remote IIIF rendition only then.
    if (art.hasBundledPreview && _zoom <= 1.65) return _preview(art);
    return Image.network(
      art.imageUrl(width: 400),
      fit: BoxFit.cover,
      filterQuality: FilterQuality.low,
      cacheWidth: 400,
      gaplessPlayback: true,
      loadingBuilder: (context, child, progress) =>
          progress == null ? child : _preview(art),
      errorBuilder: (_, error, stack) => _preview(art),
    );
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
      final tiles = _world.visible(bounds, widget.artworks.length);
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
                    onTap: () => widget.onOpen(widget.artworks[tile.artworkIndex]),
                    child: ColoredBox(
                      color: const Color(0xFF24232A),
                      child: _tileImage(widget.artworks[tile.artworkIndex]),
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
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: Text('artdrift  ∞',
                    style: TextStyle(color: Colors.white, fontSize: 18,
                      letterSpacing: -0.5, fontWeight: FontWeight.w700)),
                ),
              ),
            ),
          ),
        ),
        Positioned(
          right: 16, top: 14,
          child: SafeArea(
            child: Tooltip(
              message: 'Torna al centro',
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
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 17, vertical: 9),
                  child: Text('Trascina per esplorare  ·  Tocca un’opera',
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
