import 'package:flutter/material.dart';

/// Ad slot layout contract, not an ads SDK.
/// The canvas owns precisely the space above any *measured* banner, and owns
/// the full content area when no banner is present. Never pad the canvas for
/// an ad that is not loaded.
class ArtAdAwareViewport extends StatelessWidget {
  const ArtAdAwareViewport({
    super.key,
    required this.child,
    this.bannerHeight = 0,
  });

  final Widget child;
  final double bannerHeight;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final maxHeight = constraints.maxHeight;
      final desired = bannerHeight.isFinite
          ? bannerHeight.clamp(0.0, maxHeight).toDouble()
          : 0.0;
      // A QA banner is only a geometric placeholder. It accepts no swipes
      // and is never advertised as a real or loaded paid advertisement.
      return Column(children: [
        Expanded(child: ClipRect(
          child: SizedBox.expand(
            key: const Key('artdrift-ad-aware-canvas-region'),
            child: child))),
        if (desired > 0)
          SizedBox(
            key: const Key('artdrift-qa-ad-reserved-region'),
            height: desired,
            width: double.infinity,
            child: const Semantics(
              label: 'Area pubblicitaria simulata per collaudo',
              child: ColoredBox(color: Color(0xFF302B29),
                child: Center(child: Text('AD SLOT · QA ONLY',
                  style: TextStyle(
                    color: Color(0xFFD2C0A2), letterSpacing: 1.5,
                    fontSize: 10)))),
            ),
          ),
      ]);
    });
  }
}
