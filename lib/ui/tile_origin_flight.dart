import 'package:flutter/material.dart';

/// Transition from the actual selected tile's viewport-local rect.
/// If the viewer switches to another artwork, reverse is a neutral fade
/// instead of falsely flying a different painting to the original tile.
class TileOriginFlight extends StatelessWidget {
  const TileOriginFlight({
    super.key,
    required this.animation,
    required this.originRect,
    required this.originalArtworkKey,
    required this.currentArtworkKey,
    required this.child,
  });

  final Animation<double> animation;
  final Rect originRect;
  final String originalArtworkKey;
  final ValueListenable<String> currentArtworkKey;
  final Widget child;

  @visibleForTesting
  static double startingScale(Size screen, Rect anchor) {
    if (screen.width <= 0 || screen.height <= 0 ||
        anchor.width <= 0 || anchor.height <= 0) return 1;
    return (anchor.width / screen.width)
        .clamp(.12, .85).toDouble();
  }

  @visibleForTesting
  static Offset originDelta(Size screen, Rect anchor) =>
      anchor.center - Offset(screen.width / 2, screen.height / 2);

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: Listenable.merge([animation, currentArtworkKey]),
    child: child,
    builder: (context, content) {
      if (currentArtworkKey.value != originalArtworkKey) {
        return FadeTransition(opacity: animation, child: content);
      }
      final screen = MediaQuery.sizeOf(context);
      final anchor = originRect;
      final t = Curves.easeOutCubic.transform(
        animation.value.clamp(0.0, 1.0).toDouble());
      final start = startingScale(screen, anchor);
      final delta = originDelta(screen, anchor);
      return Transform.translate(
        key: const Key('artdrift-origin-flight'),
        offset: delta * (1 - t),
        child: Transform.scale(
          scale: start + (1 - start) * t,
          child: Opacity(
            opacity: (.2 + .8 * t).clamp(0.0, 1.0).toDouble(),
            child: content,
          ),
        ),
      );
    },
  );
}
