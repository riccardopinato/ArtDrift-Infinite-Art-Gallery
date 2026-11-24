import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/museum_cloud_catalog.dart';
import '../ui/art_remote_image.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

/// A D1 search result is always inspectable, including metadata-only records.
/// It is deliberately NOT promoted to the offline canvas or cloud favorites:
/// D1 image rights and a compatible artwork identity must be reviewed first.
class MuseumCloudArtworkDetailScreen extends StatelessWidget {
  const MuseumCloudArtworkDetailScreen({super.key, required this.work});

  final MuseumCloudWork work;
  static String t(String key) => ArtDriftLocale.text(key);

  Future<void> _launch(BuildContext context, String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null || uri.scheme != 'https' || uri.userInfo.isNotEmpty) return;
    try {
      final opened = await launchUrl(uri,
        mode: LaunchMode.platformDefault, webOnlyWindowName: '_blank');
      if (!opened && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('cloudMuseumOpenFailed'))));
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('cloudMuseumOpenFailed'))));
      }
    }
  }

  Widget _image(double height) {
    Widget missing() => Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(Icons.image_not_supported_outlined,
          color: Color(0xFFB5A080), size: 45),
        const SizedBox(height: 13),
        Text(t('cloudMuseumImageUnavailable'),
          textAlign: TextAlign.center,
          style: const TextStyle(color: Color(0xFFD5C5AC), fontSize: 13)),
      ],
    );
    return Semantics(
      label: work.title,
      image: work.imageUrl != null,
      child: Container(
        key: const Key('artdrift-d1-detail-image'),
        height: height,
        width: double.infinity,
        decoration: BoxDecoration(
          color: const Color(0xFF191B20),
          border: Border.all(color: const Color(0xFF756047), width: 1),
          borderRadius: BorderRadius.circular(16)),
        clipBehavior: Clip.antiAlias,
        child: work.imageUrl == null
          ? missing()
          : InteractiveViewer(
              minScale: 1,
              maxScale: 5,
              child: Center(child: Image.network(
                work.imageUrl!,
                fit: BoxFit.contain,
                width: double.infinity,
                height: height,
                filterQuality: FilterQuality.medium,
                webHtmlElementStrategy:
                  ArtRemoteImage.strategyFor(isWeb: kIsWeb),
                loadingBuilder: (context, child, progress) =>
                    progress == null ? child :
                    const Center(child: CircularProgressIndicator(
                      color: ArtPaper.gold)),
                errorBuilder: (_, __, ___) => missing(),
              )),
            ),
      ),
    );
  }

  Widget _metadata() {
    Widget line(String label, String value) => Padding(
      padding: const EdgeInsets.only(bottom: 11),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label.toUpperCase(), style: const TextStyle(
          color: ArtPaper.gold, letterSpacing: 1.15, fontSize: 10)),
        const SizedBox(height: 3),
        Text(value, style: const TextStyle(
          color: ArtPaper.ink, fontSize: 14, height: 1.45)),
      ]),
    );
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [ArtPaper.pale, ArtPaper.ivory, Color(0xFFE1CEAE)]),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: ArtPaper.gold)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('ARTDRIFT  ·  ARCHIVE', style: TextStyle(
          color: ArtPaper.gold, fontSize: 11, letterSpacing: 1.4)),
        const SizedBox(height: 12),
        Text(work.title, key: const Key('artdrift-d1-detail-title'),
          style: const TextStyle(fontFamily: 'serif',
            color: ArtPaper.ink, fontSize: 25, height: 1.22)),
        const SizedBox(height: 19),
        if (work.artist.isNotEmpty)
          line(t('cloudMuseumArtist'), work.artist),
        line(t('cloudMuseumMuseum'), work.museum),
        if (work.date.isNotEmpty)
          line(t('cloudMuseumDate'), work.date),
        if (work.medium.isNotEmpty)
          line(t('cloudMuseumMedium'), work.medium),
        line(t('cloudMuseumLicense'), work.license),
        if (work.credit.isNotEmpty)
          line(t('cloudMuseumCredit'), work.credit),
        const Divider(color: ArtPaper.gold, height: 28),
        if (work.sourceUrl != null) ...[
          _launchFromBuilder(work.sourceUrl!),
          const SizedBox(height: 8),
        ],
        Builder(builder: (context) => OutlinedButton.icon(
          key: const Key('artdrift-d1-detail-rights'),
          onPressed: () => _launch(context, work.rightsEvidenceUrl),
          icon: const Icon(Icons.gavel_outlined, size: 17),
          label: Text(t('cloudMuseumRights')),
          style: OutlinedButton.styleFrom(
            foregroundColor: ArtPaper.ink,
            side: const BorderSide(color: ArtPaper.gold)),
        )),
        if (work.sourceUrl == null)
          Padding(
            padding: const EdgeInsets.only(top: 11),
            child: Text(t('cloudMuseumNoOfficial'),
              style: const TextStyle(color: Color(0xFF795D3C),
                fontSize: 11, height: 1.4))),
      ]),
    );
  }

  // A separately built button obtains a valid BuildContext for SnackBars.
  Widget _launchFromBuilder(String url) => Builder(
    builder: (context) => OutlinedButton.icon(
      key: const Key('artdrift-d1-detail-official'),
      onPressed: () => _launch(context, url),
      icon: const Icon(Icons.open_in_new, size: 17),
      label: Text(t('cloudMuseumOfficial')),
      style: OutlinedButton.styleFrom(
        foregroundColor: ArtPaper.ink,
        side: const BorderSide(color: ArtPaper.gold)),
    ));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF111319),
      body: SafeArea(child: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 5, 16, 5),
          child: Row(children: [
            IconButton(
              key: const Key('artdrift-d1-detail-back'),
              icon: const Icon(Icons.arrow_back_rounded),
              color: ArtPaper.ivory,
              tooltip: t('back'),
              onPressed: () => Navigator.of(context).pop()),
            const SizedBox(width: 8),
            const Expanded(child: Text('ARTDRIFT · MUSEUMS',
              style: TextStyle(color: Color(0xFFD8BD92),
                fontSize: 11, letterSpacing: 1.1))),
          ]),
        ),
        Expanded(child: LayoutBuilder(builder: (context, constraints) {
          final wide=constraints.maxWidth>=760;
          final maxWidth=math.min(1160.0, constraints.maxWidth-32);
          final imageHeight=wide
            ? math.max(240.0, math.min(680.0, constraints.maxHeight-40))
            : math.max(210.0, math.min(460.0, constraints.maxWidth*0.95));
          return SingleChildScrollView(
            key: const Key('artdrift-d1-detail-scroll'),
            padding: const EdgeInsets.fromLTRB(16, 9, 16, 24),
            child: Center(child: SizedBox(width: maxWidth,
              child: wide
                ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Expanded(flex: 6, child: _image(imageHeight)),
                    const SizedBox(width: 19),
                    Expanded(flex: 4, child: _metadata()),
                  ])
                : Column(children: [
                    _image(imageHeight),
                    const SizedBox(height: 16),
                    _metadata(),
                  ]),
            )),
          );
        })),
      ])),
    );
  }
}
