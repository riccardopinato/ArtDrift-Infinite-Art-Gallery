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
  @override
  Widget build(BuildContext context) {
    final height = MediaQuery.sizeOf(context).height;
    final maxHeight = math.min(height * .84,
        height - MediaQuery.viewInsetsOf(context).bottom - 24);
    return SizedBox(height: math.max(280.0, maxHeight),
      child: ParchmentPanel(child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            const BrushMark(size: 24), const SizedBox(width: 12),
            Expanded(child: Text(t('settings'), style: const TextStyle(
              color: ArtPaper.ink, fontSize: 25, fontFamily: 'serif',
              fontWeight: FontWeight.bold))),
            IconButton(tooltip: t('close'), onPressed: () => Navigator.pop(context),
              icon: const Icon(Icons.close, color: ArtPaper.ink)),
          ]),
          const Divider(color: ArtPaper.gold),
          Expanded(child: ListView(children: [
            const SizedBox(height: 12),
            Text(t('language'), style: const TextStyle(
              color: ArtPaper.ink, fontSize: 17, fontFamily:'serif')),
            const SizedBox(height: 10),
            Wrap(spacing: 7, runSpacing: 7,
              children: [for (final code in ArtDriftLocale.codes)
                ChoiceChip(
                  label: Text(ArtDriftLocale.names[code]!),
                  selected: ArtDriftLocale.current.value == code,
                  selectedColor: const Color(0xFFAE8C5E),
                  backgroundColor: ArtPaper.pale,
                  side: const BorderSide(color: Color(0xFF9A784E)),
                  labelStyle: const TextStyle(color: ArtPaper.ink, fontSize: 12),
                  onSelected: (_) async {
                    await ArtDriftLocale.select(code);
                    if (mounted) setState(() {});
                  },
                )],
            ),
            const SizedBox(height: 9),
            Text(t('languageNote'), style: const TextStyle(
              color: Color(0xFF725B40), fontSize: 12)),
            const SizedBox(height: 24),
            _ActionTile(
              icon: Icons.speed_rounded,
              title: _performanceTitle(),
              subtitle: _performanceSubtitle(),
              onTap: () => _showPerformanceDiagnostics(context),
            ),
            _ActionTile(
              icon: Icons.auto_awesome_outlined, title: t('pro'),
              subtitle: t('proStatus'), onTap: () => _showDocument(context,
                t('pro'), t('proDescription') + '\n\n' + t('proComing')),
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
            const SizedBox(height: 28),
            const Center(child: Text('ARTDRIFT  ·  INFINITE ART GALLERY',
              style: TextStyle(color: Color(0xFF765A3F), fontSize: 10,
                letterSpacing: 1.4))),
            const SizedBox(height: 10),
          ])),
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
