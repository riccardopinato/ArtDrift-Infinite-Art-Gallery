import 'package:flutter/material.dart';

/// A stable, original vector frame: never applied to individual canvas tiles.
/// Its own render object does not depend on the selected artwork.
class MuseumWoodFrame extends StatelessWidget {
  const MuseumWoodFrame({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
    key: const Key('artdrift-museum-wood-frame'),
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topLeft, end: Alignment.bottomRight,
        colors: [
          Color(0xFF392216), Color(0xFF90613C), Color(0xFF4B2A17),
          Color(0xFFBE905B), Color(0xFF352116),
        ]),
      border: Border.all(color: const Color(0xFFD2A56B), width: 2),
      boxShadow: const [
        BoxShadow(color: Color(0xB0000000), blurRadius: 20,
          offset: Offset(0, 9)),
      ],
    ),
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFF191819),
          border: Border.all(color: const Color(0xFFE0BD85), width: 2),
        ),
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: ClipRect(child: child),
        ),
      ),
    ),
  );
}
