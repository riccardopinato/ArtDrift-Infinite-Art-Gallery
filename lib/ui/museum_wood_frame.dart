import 'package:flutter/material.dart';

/// Original walnut museum frame, confined to the opened artwork.
/// Uses a single lightweight vector inlay rather than external image assets.
class MuseumWoodFrame extends StatelessWidget {
  const MuseumWoodFrame({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
    key: const Key('artdrift-museum-wood-frame'),
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topLeft, end: Alignment.bottomRight,
        stops: [0, .16, .38, .62, .84, 1],
        colors: [
          Color(0xFF322013), Color(0xFF91633E), Color(0xFF4C2C1B),
          Color(0xFF2C1B12), Color(0xFFB18A55), Color(0xFF322014),
        ]),
      border: Border.all(color: const Color(0xFFCEAD78), width: 2),
      boxShadow: const [
        BoxShadow(color: Color(0x99000000), blurRadius: 18,
          offset: Offset(0, 7)),
      ],
    ),
    child: CustomPaint(
      foregroundPainter: const _WalnutInlayPainter(),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFF18171A),
            border: Border.all(color: const Color(0xFFB9945B), width: 1.5),
          ),
          child: Padding(
            padding: const EdgeInsets.all(2),
            child: ClipRect(child: child),
          ),
        ),
      ),
    ),
  );
}

class _WalnutInlayPainter extends CustomPainter {
  const _WalnutInlayPainter();

  @override
  void paint(Canvas canvas, Size size) {
    if (size.width < 45 || size.height < 45) return;
    final gold = Paint()
      ..color = const Color(0xD7E1BE80)
      ..style = PaintingStyle.stroke
      ..strokeWidth = .75;
    final dark = Paint()
      ..color = const Color(0xAB20120C)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.1;
    for (final inset in [4.0, 7.0, 11.0]) {
      final bounds = Rect.fromLTRB(inset, inset,
          size.width - inset, size.height - inset);
      canvas.drawRect(bounds, inset == 7 ? gold : dark);
    }
    // Four restrained carved corner flourishes on the outer wood only.
    void corner(double x, double y, double sx, double sy) {
      canvas.save();
      canvas.translate(x, y);
      canvas.scale(sx, sy);
      final flourish = Path()
        ..moveTo(4, 25)
        ..quadraticBezierTo(8, 13, 17, 9)
        ..quadraticBezierTo(25, 6, 31, 5);
      canvas.drawPath(flourish, gold);
      canvas.drawCircle(const Offset(8, 8), 1.7,
          Paint()..color = const Color(0xB4EAC68F));
      canvas.restore();
    }
    corner(0, 0, 1, 1);
    corner(size.width, 0, -1, 1);
    corner(0, size.height, 1, -1);
    corner(size.width, size.height, -1, -1);
  }

  @override
  bool shouldRepaint(covariant _WalnutInlayPainter oldDelegate) => false;
}
