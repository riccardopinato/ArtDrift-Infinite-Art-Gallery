import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'localization.dart';

/// Museum-style loading/error surface. Presentation only: no timers, downloads,
/// simulated offline successes or changes to the real CatalogService lifecycle.
class MuseumPortal extends StatelessWidget {
  const MuseumPortal.loading({super.key})
      : unavailable = false, onRetry = null;
  const MuseumPortal.unavailable({super.key, required this.onRetry})
      : unavailable = true;

  final bool unavailable;
  final VoidCallback? onRetry;
  static const _gold = Color(0xFFC9A574);
  static const _ivory = Color(0xFFF2E7D8);
  static const _muted = Color(0xFFCAB9A5);
  static String _t(String key) => ArtDriftLocale.text(key);

  @override
  Widget build(BuildContext context) {
    final fontScale = MediaQuery.textScalerOf(context).scale(1);
    return Scaffold(
      backgroundColor: const Color(0xFF101117),
      body: SafeArea(child: LayoutBuilder(builder: (context, constraints) {
        final compact = constraints.maxHeight < 550 || fontScale > 1.35;
        return DecoratedBox(
          decoration: const BoxDecoration(gradient: RadialGradient(
            center: Alignment(0, -.22), radius: 1.15,
            colors: [Color(0xFF302922), Color(0xFF141419), Color(0xFF101117)],
          )),
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(22, 20, 22, 12),
              child: const Row(children: [
                Text('ARTDRIFT', style: TextStyle(color: _gold,
                    fontSize: 10, letterSpacing: 2)),
                Spacer(),
                Text('∞', style: TextStyle(color: _gold, fontSize: 25)),
              ])),
            const Divider(color: Color(0x706F573F), height: 1, indent: 22, endIndent: 22),
            Expanded(child: SingleChildScrollView(
              key: const Key('artdrift-portal-scroll'),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: math.max(0, constraints.maxHeight - 91)),
                child: Center(child: Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: 25, vertical: compact ? 16 : 32),
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                    if (unavailable)
                      const _MuseumEmblem(unavailable: true)
                    else
                      const _MuseumEmblem(unavailable: false),
                    SizedBox(height: compact ? 17 : 25),
                    Text(unavailable ? '02 / INTERRUZIONE' : '01 / INGRESSO',
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 10,
                        color: _gold, letterSpacing: 1.7)),
                    const SizedBox(height: 12),
                    if (!unavailable) ...[
                      Text(_t('portalLine1'),
                        key: const Key('artdrift-portal-line1'),
                        textAlign: TextAlign.center,
                        style: TextStyle(color: _ivory,
                          fontSize: compact ? 26 : 30,
                          fontFamily: 'serif')),
                      const SizedBox(height: 5),
                      Text(_t('portalLine2'),
                        key: const Key('artdrift-portal-line2'),
                        textAlign: TextAlign.center,
                        style: TextStyle(color: _gold,
                          fontSize: compact ? 20 : 23,
                          fontFamily: 'serif', fontStyle: FontStyle.italic)),
                    ] else ...[
                      Text(_t('portalError'),
                        key: const Key('artdrift-portal-error'),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: _ivory,
                          fontSize: 23, fontFamily: 'serif')),
                    ],
                    const SizedBox(height: 16),
                    const Row(mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _OrnamentRule(), SizedBox(width: 12),
                        Text('❦', style: TextStyle(color: _gold, fontSize: 20)),
                        SizedBox(width: 12), _OrnamentRule(),
                      ]),
                    const SizedBox(height: 16),
                    Text(unavailable ? _t('portalErrorBody') : _t('portalLoading'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: _muted,
                        fontFamily: 'serif', fontSize: 13, height: 1.55)),
                    const SizedBox(height: 22),
                    if (unavailable)
                      Semantics(button: true, child: OutlinedButton.icon(
                        key: const Key('artdrift-portal-retry'),
                        onPressed: onRetry,
                        icon: const Icon(Icons.refresh_rounded),
                        label: Text(_t('portalRetry')),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFF31271D),
                          backgroundColor: const Color(0xFFE7D8BE),
                          side: const BorderSide(color: _gold),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 26, vertical: 14),
                        )))
                    else
                      SizedBox(width: 165, child:
                        MediaQuery.disableAnimationsOf(context)
                          ? const LinearProgressIndicator(
                              key: Key('artdrift-portal-progress'),
                              value: .45, color: _gold,
                              backgroundColor: Color(0xFF594733))
                          : const LinearProgressIndicator(
                              key: Key('artdrift-portal-progress'),
                              color: _gold,
                              backgroundColor: Color(0xFF594733))),
                  ]),
                )),
              ),
            )),
            const Divider(color: Color(0x706F573F), height: 1, indent: 22, endIndent: 22),
            const Padding(padding: EdgeInsets.fromLTRB(22, 10, 22, 16),
              child: Row(children: [
                Text('UN MUSEO SENZA FINE', style: TextStyle(
                  color: _gold, fontSize: 9, letterSpacing: 1.4)),
                Spacer(),
                Text('✦', style: TextStyle(color: _gold, fontSize: 16)),
              ])),
          ]),
        );
      })),
    );
  }
}

class _OrnamentRule extends StatelessWidget {
  const _OrnamentRule();
  @override
  Widget build(BuildContext context) => Container(
    width: 36, height: 1, color: const Color(0xFF907756));
}

class _MuseumEmblem extends StatelessWidget {
  const _MuseumEmblem({required this.unavailable});
  final bool unavailable;

  @override
  Widget build(BuildContext context) => Container(
    width: unavailable ? 112 : 129,
    height: unavailable ? 112 : 151,
    padding: const EdgeInsets.all(6),
    decoration: BoxDecoration(
      gradient: const LinearGradient(colors: [
        Color(0xFF4A3022), Color(0xFFB28B59), Color(0xFF382317)]),
      border: Border.all(color: const Color(0xFFC5A574), width: 2),
      borderRadius: BorderRadius.only(
        topLeft: Radius.circular(unavailable ? 65 : 75),
        topRight: Radius.circular(unavailable ? 65 : 75),
        bottomLeft: const Radius.circular(3),
        bottomRight: const Radius.circular(3))),
    child: Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1F),
        border: Border.all(color: const Color(0xFFCFB387)),
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(unavailable ? 59 : 70),
          topRight: Radius.circular(unavailable ? 59 : 70))),
      child: Center(child: unavailable
        ? const Icon(Icons.auto_awesome_outlined,
            size: 48, color: Color(0xFFC5A574))
        : const Column(mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('✧', style: TextStyle(
                fontSize: 23, color: Color(0xFFC5A574))),
              SizedBox(height: 8),
              Text('AD', style: TextStyle(
                fontFamily: 'serif', fontSize: 43,
                fontStyle: FontStyle.italic, color: Color(0xFFF2E6D2))),
              SizedBox(height: 10),
              Text('INFINITE ART', style: TextStyle(
                fontSize: 8, letterSpacing: 1, color: Color(0xFFBFAB8E))),
            ])),
    ),
  );
}
