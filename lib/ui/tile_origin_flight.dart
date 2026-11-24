import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/artwork.dart';
import 'artwork_preview_image.dart';

/// Museum painting flight: animate ONLY the selected artwork preview from
/// its actual tapped canvas rectangle. The document/controls behind it fade
/// into place; the full route is never scaled down as a fake painting.
///
/// If previous/next changes artwork identity, exit is an ordinary fade.
/// The canvas camera and tile identities are untouched.
class TileOriginFlight extends StatelessWidget {
  const TileOriginFlight({
    super.key,
    required this.animation,
    required this.originRect,
    required this.originArtwork,
    required this.originalArtworkKey,
    required this.currentArtworkKey,
    required this.child,
  });

  final Animation<double> animation;
  /// Global (screen) coordinates, measured before navigation opens.
  final Rect originRect;
  final Artwork originArtwork;
  final String originalArtworkKey;
  final ValueListenable<String> currentArtworkKey;
  final Widget child;

  @visibleForTesting
  static double startingScale(Size screen, Rect anchor) {
    if (screen.width <= 0 || screen.height <= 0 ||
        anchor.width <= 0 || anchor.height <= 0) return 1;
    return (anchor.width / screen.width).clamp(.12, .85).toDouble();
  }

  @visibleForTesting
  static Offset originDelta(Size screen, Rect anchor) =>
      anchor.center - Offset(screen.width / 2, screen.height / 2);

  /// Same fixed ratio used by ArtworkDetail's walnut frame.
  static double frameAspectFor(Artwork artwork) {
    final known = artwork.imageWidth != null &&
        artwork.imageHeight != null &&
        artwork.imageWidth! > 0 && artwork.imageHeight! > 0;
    return known ? artwork.naturalAspectRatio : .76;
  }

  /// Pixel-space destination on the *top artwork area* (not the entire page).
  /// The frame's dimensions remain locked to the first viewed artwork.
  @visibleForTesting
  static Rect targetFrameRect(Size screen, EdgeInsets safe, double aspect) {
    final usableHeight = math.max(
        1.0, screen.height - safe.top - safe.bottom);
    final wide = screen.width >= 740;
    final captionHeight = wide ? 0.0
        : (usableHeight * .35).clamp(175.0, 310.0).toDouble();
    final counterHeight = wide ? 0.0 : 22.0;
    final artworkAreaHeight = math.max(
        1.0, usableHeight - 52 - captionHeight - counterHeight);
    final artworkAreaWidth = math.max(
        1.0, screen.width - (wide ? 295.0 : 0.0) - 86);
    final targetWidth = math.min(
      math.max(1.0, artworkAreaWidth - 8),
      math.max(1.0, artworkAreaHeight - 18) * aspect,
    );
    final targetHeight = math.max(1.0, targetWidth / aspect);
    final centerX = wide ? (screen.width - 295) / 2 : screen.width / 2;
    final centerY = safe.top + 52 + artworkAreaHeight / 2;
    return Rect.fromCenter(
      center: Offset(centerX, centerY),
      width: targetWidth, height: targetHeight,
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([animation, currentArtworkKey]),
      child: child,
      builder: (context, page) {
        final t = animation.value.clamp(0.0, 1.0).toDouble();
        if (MediaQuery.disableAnimationsOf(context) ||
            currentArtworkKey.value != originalArtworkKey ||
            originRect.width <= 0 || originRect.height <= 0) {
          return FadeTransition(opacity: animation, child: page);
        }

        final screen = MediaQuery.sizeOf(context);
        final destination = targetFrameRect(
          screen, MediaQuery.paddingOf(context),
          frameAspectFor(originArtwork),
        );
        final motion = Curves.easeInOutCubic.transform(t);
        final movingRect = Rect.lerp(originRect, destination, motion)!;
        // Only the real painting moves. Rest of the room slides into view
        // softly underneath, rather than being scaled from a canvas tile.
        final pageOpacity = ((t - .48) / .52)
            .clamp(0.0, 1.0).toDouble();
        final previewOpacity = t >= .86
            ? ((1 - t) / .14).clamp(0.0, 1.0).toDouble()
            : 1.0;
        final walnut = ((t - .12) / .72).clamp(0.0, 1.0).toDouble();

        return Stack(fit: StackFit.expand, children: [
          Opacity(opacity: pageOpacity, child: page),
          if (t < 1.0)
            Positioned.fromRect(
              key: const Key('artdrift-origin-flight'),
              rect: movingRect,
              child: Opacity(
                opacity: previewOpacity,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: Color.lerp(
                      const Color(0xFF25232A),
                      const Color(0xFF5F3924), walnut),
                    border: Border.all(
                      color: Color.lerp(Colors.transparent,
                        const Color(0xFFD1AC73), walnut)!,
                      width: 2 * walnut),
                  ),
                  child: Padding(
                    padding: EdgeInsets.all(12 * walnut),
                    child: ClipRect(
                      child: ArtworkPreviewImage(
                        key: const Key('artdrift-flight-artwork-only'),
                        artwork: originArtwork,
                        fit: BoxFit.contain, cacheWidth: 360),
                    ),
                  ),
                ),
              ),
            ),
        ]);
      },
    );
  }
}
