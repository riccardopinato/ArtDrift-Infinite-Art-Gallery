import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/art_frame_performance.dart';
import '../services/art_image_delivery_metrics.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

Future<void> showArtDriftSettings(BuildContext context) =>
    showModalBottomSheet<void>(
      context: context, backgroundColor: Colors.transparent,
      isScrollControlled: true, useSafeArea: true,
      builder: (context) => const _ArtDriftSettingsSheet(),
    );

class _ArtDriftSettingsSheet extends StatefulWidget {
  const _ArtDriftSettingsSheet();
  @override
  State<_ArtDriftSettingsSheet> createState() => _ArtDriftSettingsState();
}

class _ArtDriftSettingsState extends State<_ArtDriftSettingsSheet> {
  static String t(String key) => ArtDriftLocale.text(key);
  static const _museumHeading = <String, List<String>>{
    'it': ['Il tuo', 'museo.'],
    'en': ['Your', 'museum.'],
    'fr': ['Votre', 'musée.'],
    'es': ['Tu', 'museo.'],
    'de': ['Dein', 'Museum.'],
    'pt': ['O seu', 'museu.'],
  };
  static const _visitPreference = <String, String>{
    'it': 'Le preferenze della tua visita.',
    'en': 'Your visit, your preferences.',
    'fr': 'Les préférences de votre visite.',
    'es': 'Las preferencias de tu visita.',
    'de': 'Einstellungen für deinen Besuch.',
    'pt': 'As preferências da sua visita.',
  };

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.of(context);
    final available = math.max(1.0,
      mq.size.height - mq.viewInsets.bottom - mq.padding.top - 12);
    final height = math.min(mq.size.height * .88, available);
    final heading = _museumHeading[ArtDriftLocale.current.value]
        ?? _museumHeading['en']!;
    return SizedBox(height: height,
      child: ParchmentPanel(child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            const BrushMark(size: 22),
            const SizedBox(width: 10),
            Expanded(child: Text('ARTDRIFT  ✧  ' + t('settings').toUpperCase(),
              style: const TextStyle(color: ArtPaper.gold, fontSize: 10,
                letterSpacing: 1.3))),
            IconButton(key: const Key('artdrift-curator-close'),
              tooltip: t('close'), onPressed: () => Navigator.pop(context),
              icon: const Icon(Icons.close, color: ArtPaper.ink)),
          ]),
          const Divider(color: ArtPaper.gold, height: 8),
          Expanded(child: ListView(
            key: const Key('artdrift-curator-scroll'),
            children: [
              const SizedBox(height: 18),
              Text(heading[0], style: const TextStyle(
                color: ArtPaper.ink, fontSize: 36,
                fontFamily: 'serif', height: 1.06)),
              Text(heading[1], style: const TextStyle(
                color: Color(0xFF937047), fontSize: 36,
                fontFamily: 'serif', height: 1.1,
                fontStyle: FontStyle.italic)),
              const SizedBox(height: 9),
              Text(_visitPreference[ArtDriftLocale.current.value]
                  ?? _visitPreference['en']!,
                style: const TextStyle(
                  color: Color(0xFF816D57), fontFamily: 'serif',
                  fontSize: 12)),
              const SizedBox(height: 24),
              _SectionHeading(number: '01', text: t('language')),
              const SizedBox(height: 12),
              LayoutBuilder(builder: (context, bounds) {
                final width = math.max(1.0, (bounds.maxWidth - 9) / 2);
                return Wrap(spacing: 9, runSpacing: 9,
                  children: [for (final code in ArtDriftLocale.codes)
                    SizedBox(width: width, child: _LanguageChoice(
                      code: code,
                      selected: ArtDriftLocale.current.value == code,
                      onTap: () async {
                        await ArtDriftLocale.select(code);
                        if (mounted) setState(() {});
                      },
                    ))]);
              }),
              const SizedBox(height: 12),
              Text(t('languageNote'), style: const TextStyle(
                color: Color(0xFF725B40), fontSize: 12, height: 1.5)),
              const SizedBox(height: 24),
              _SectionHeading(number: '02', text: t('about')),
              const SizedBox(height: 8),
              _ActionTile(
                icon: Icons.auto_awesome_outlined, title: t('pro'),
                subtitle: t('proStatus'), onTap: () => _showDocument(context,
                  t('pro'), t('proDescription') + '\\n\\n' + t('proComing')),
              ),
              _ActionTile(
                icon: Icons.verified_user_outlined, title: t('about'),
                subtitle: t('privacyTitle'), onTap: () => _showDocument(context,
                  t('privacyTitle'), t('privacyBody')),
              ),
              _ActionTile(
                icon: Icons.museum_outlined, title: t('license'),
                subtitle: 'Open Access · Public Domain / CC0',
                onTap: () => _showDocument(context,t('license'),t('licenseBody')),
              ),
              const SizedBox(height: 23),
              _SectionHeading(number: '03', text: _performanceTitle()),
              const SizedBox(height: 8),
              _ActionTile(
                icon: Icons.speed_rounded,
                title: _performanceTitle(),
                subtitle: _performanceSubtitle(),
                onTap: () => _showPerformanceDiagnostics(context),
              ),
              const SizedBox(height: 24),
              const Divider(color: ArtPaper.gold),
              const Center(child: Text('ARTDRIFT  ·  INFINITE ART GALLERY',
                style: TextStyle(color: Color(0xFF765A3F), fontSize: 10,
                  letterSpacing: 1.4))),
              const SizedBox(height: 13),
            ],
          )),
        ],
      )));
  }

  String _performanceTitle() {
    const titles = <String, String>{
      'it':'Prestazioni Android','en':'Android performance',
      'fr':'Performances Android','es':'Rendimiento Android',
      'de':'Android-Leistung','pt':'Desempenho Android',
    };
    return titles[ArtDriftLocale.current.value] ?? titles['en']!;
  }

  String _performanceSubtitle() {
    const disabled = <String, String>{
      'it':'Misura i tempi dei frame solo sul dispositivo',
      'en':'Measure frame times locally on this device',
      'fr':'Mesure locale des temps de rendu',
      'es':'Mide localmente los tiempos de fotograma',
      'de':'Framezeiten lokal auf diesem Gerät messen',
      'pt':'Mede os tempos de quadro neste aparelho',
    };
    return disabled[ArtDriftLocale.current.value] ?? disabled['en']!;
  }

  Future<void> _showPerformanceDiagnostics(BuildContext context) =>
      showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (dialogContext, update) {
            final monitor = ArtFramePerformance.instance;
            final report = monitor.snapshot().report + '\n\n' +
                ArtImageDeliveryMetrics.instance.report;
            final language = ArtDriftLocale.current.value;
            String label(String italian, String english) =>
                language == 'it' ? italian : english;
            return AlertDialog(
              backgroundColor: ArtPaper.ivory,
              title: Text(_performanceTitle(),
                style: const TextStyle(color: ArtPaper.ink)),
              content: SizedBox(
                width: 360,
                child: SingleChildScrollView(
                  child: SelectableText(report,
                    style: const TextStyle(color: ArtPaper.ink,
                      fontSize: 12, height: 1.5)))),
              actions: [
                TextButton(
                  onPressed: () {
                    if (monitor.isRecording) {
                      monitor.stop();
                    } else {
                      monitor.start();
                    }
                    update(() {});
                  },
                  child: Text(monitor.isRecording
                    ? label('Ferma','Stop')
                    : label('Avvia','Start'),
                    style: const TextStyle(color: ArtPaper.ink)),
                ),
                TextButton(
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(
                      text: monitor.snapshot().report + '\n\n' +
                      ArtImageDeliveryMetrics.instance.report));
                  },
                  child: Text(label('Copia report','Copy report'),
                    style: const TextStyle(color: ArtPaper.ink)),
                ),
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: Text(t('close'),
                    style: const TextStyle(color: ArtPaper.ink)),
                ),
              ],
            );
          },
        ),
      );

  Future<void> _showDocument(BuildContext context, String title, String body) =>
      showDialog<void>(context: context, builder: (context) => AlertDialog(
        backgroundColor: ArtPaper.ivory,
        shape: RoundedRectangleBorder(side: const BorderSide(color: ArtPaper.gold),
            borderRadius: BorderRadius.circular(14)),
        title: Text(title, style: const TextStyle(
          color: ArtPaper.ink, fontFamily:'serif')),
        content: SingleChildScrollView(child: Text(body,
          style: const TextStyle(color: ArtPaper.ink, fontSize: 13, height: 1.6))),
        actions: [TextButton(onPressed: () => Navigator.pop(context),
          child: Text(t('close'), style: const TextStyle(color: ArtPaper.ink)))],
      ));
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({required this.icon, required this.title,
    required this.subtitle, required this.onTap});
  final IconData icon;
  final String title, subtitle;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: OrnateFrame(shadow: false, padding: EdgeInsets.zero,
      child: ListTile(
        leading: Icon(icon, color: ArtPaper.gold),
        title: Text(title, style: const TextStyle(color: ArtPaper.ink,
          fontSize: 16, fontFamily: 'serif')),
        subtitle: Text(subtitle, style: const TextStyle(color: Color(0xFF785C3C),
          fontSize: 11)),
        trailing: const Icon(Icons.chevron_right, color: ArtPaper.gold),
        onTap: onTap,
      )),
  );
}

class _SectionHeading extends StatelessWidget {
  const _SectionHeading({required this.number, required this.text});
  final String number, text;

  @override
  Widget build(BuildContext context) => Container(
    decoration: const BoxDecoration(border: Border(
      top: BorderSide(color: Color(0xFFBBA68B)))),
    padding: const EdgeInsets.only(top: 11),
    child: Row(children: [
      Expanded(child: Text('$number / ' + text.toUpperCase(),
        style: const TextStyle(
          fontFamily: 'serif', fontSize: 10, letterSpacing: 1.15,
          color: Color(0xFF937149)))),
      const Text('✦', style: TextStyle(
        color: Color(0xFFB2966C), fontSize: 14)),
    ]),
  );
}

class _LanguageChoice extends StatelessWidget {
  const _LanguageChoice({
    required this.code, required this.selected, required this.onTap,
  });
  final String code;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true, selected: selected,
    label: ArtDriftLocale.names[code],
    child: Material(color: Colors.transparent, child: InkWell(
      key: Key('artdrift-language-$code'),
      onTap: onTap,
      borderRadius: BorderRadius.circular(5),
      child: Container(
        constraints: const BoxConstraints(minHeight: 48),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: selected
              ? const Color(0xFFD9C19E) : const Color(0xFFF7ECDB),
          border: Border.all(color: selected
              ? const Color(0xFF907048) : const Color(0xFFC1AF94)),
          borderRadius: BorderRadius.circular(5),
        ),
        child: Row(children: [
          Expanded(child: Text(ArtDriftLocale.names[code]!,
            maxLines: 2, overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: ArtPaper.ink,
              fontFamily: 'serif', fontSize: 13))),
          const SizedBox(width: 4),
          Text(code.toUpperCase(), style: const TextStyle(
            color: Color(0xFF8F6B45), fontSize: 10,
            fontWeight: FontWeight.w600)),
        ]),
      ),
    )),
  );
}
