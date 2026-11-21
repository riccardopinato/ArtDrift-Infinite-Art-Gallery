import 'dart:math' as math;
import 'package:flutter/material.dart';

/// Lightweight original decorative vector geometry: no bitmaps or fonts added.
abstract final class ArtPaper {
  static const ink = Color(0xFF493522);
  static const gold = Color(0xFF94703F);
  static const ivory = Color(0xFFF5E9CD);
  static const faded = Color(0xFFDBC49A);
  static const pale = Color(0xFFF9F1DF);
}

class BrushMark extends StatelessWidget {
  const BrushMark({super.key, this.size = 20});
  final double size;
  @override
  Widget build(BuildContext context) => CustomPaint(
    size: Size.square(size), painter: _BrushPainter());
}

class _BrushPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(size.width / 2, size.height / 2);
    canvas.rotate(-math.pi / 4);
    final paint = Paint()..style = PaintingStyle.fill;
    paint.color = const Color(0xFF4D3424);
    canvas.drawRRect(RRect.fromRectAndRadius(
      Rect.fromLTWH(-1.6, -7.0, 3.2, 13.0),
      const Radius.circular(1.5)), paint);
    paint.color = ArtPaper.gold;
    canvas.drawRRect(RRect.fromRectAndRadius(
      Rect.fromLTWH(-2.6, 3.8, 5.2, 4.0),
      const Radius.circular(0.7)), paint);
    final tip = Path()..moveTo(-2.6, 7.0)..quadraticBezierTo(
      -3.2, 10.0, 0.0, 13.0)..quadraticBezierTo(3.2, 10.0, 2.6, 7.0)..close();
    paint.color = const Color(0xFF583728);
    canvas.drawPath(tip, paint);
    canvas.restore();
  }
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class OrnateFrame extends StatelessWidget {
  const OrnateFrame({super.key, required this.child, this.padding = const EdgeInsets.all(12),
    this.radius = 10, this.shadow = true});
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final bool shadow;
  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topLeft, end: Alignment.bottomRight,
        colors: [ArtPaper.pale, ArtPaper.ivory, ArtPaper.faded],
      ),
      borderRadius: BorderRadius.circular(radius),
      border: Border.all(color: ArtPaper.gold, width: 1.2),
      boxShadow: shadow ? const [
        BoxShadow(color: Color(0x88000000), blurRadius: 14, offset: Offset(0, 4)),
      ] : const [],
    ),
    child: Padding(padding: padding, child: child),
  );
}

class ParchmentPanel extends StatelessWidget {
  const ParchmentPanel({super.key, required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topLeft, end: Alignment.bottomRight,
        colors: [Color(0xFFF5E9CA), Color(0xFFEAD9B5), Color(0xFFD7BF91)],
      ),
      borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      border: Border.all(color: const Color(0xFF927044), width: 1.5),
      boxShadow: const [BoxShadow(color: Color(0xAA000000), blurRadius: 30)],
    ),
    child: ClipRRect(
      borderRadius: const BorderRadius.vertical(top: Radius.circular(23)),
      child: CustomPaint(painter: _OrnamentPainter(),
          child: Padding(padding: const EdgeInsets.fromLTRB(19, 24, 19, 16),
            child: child)),
    ),
  );
}

class _OrnamentPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = ArtPaper.gold.withValues(alpha: 0.55)
      ..strokeWidth = 0.85..style = PaintingStyle.stroke;
    final path = Path();
    const border = 10.0;
    path.moveTo(border, 45); path.lineTo(border, size.height - 14);
    path.moveTo(size.width-border, 45);
    path.lineTo(size.width-border, size.height-14);
    path.moveTo(border+8, 11); path.lineTo(size.width-border-8, 11);
    path.moveTo(border+8, size.height-10);
    path.lineTo(size.width-border-8, size.height-10);
    canvas.drawPath(path, paint);
    for (final x in [border + 8, size.width - border - 8]) {
      for (final y in [13.0, size.height - 13.0]) {
        final diamond = Path()..moveTo(x, y-4)
          ..lineTo(x+4, y)..lineTo(x, y+4)..lineTo(x-4,y)..close();
        canvas.drawPath(diamond, paint);
      }
    }
  }
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
