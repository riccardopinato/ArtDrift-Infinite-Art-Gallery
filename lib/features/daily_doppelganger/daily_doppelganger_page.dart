import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../ui/art_remote_image.dart';
import '../../ui/localization.dart';
import '../../ui/parchment.dart';
import 'daily_doppelganger.dart';
import 'daily_doppelganger_copy.dart';

/// Art-only editorial microscreen. Never changes the InfiniteGallery camera,
/// favorites or the shared GalleryDrift engine.
class DailyDoppelgangerPage extends StatefulWidget {
  const DailyDoppelgangerPage({
    super.key, this.clock, this.catalogLoader, this.imageBuilder,
  });

  final DateTime Function()? clock;
  final Future<List<DailyDoppelgangerPair>> Function()? catalogLoader;
  final Widget Function(BuildContext, DailyDoppelgangerMedia)? imageBuilder;

  @override
  State<DailyDoppelgangerPage> createState() => _DailyDoppelgangerPageState();
}

class _DailyDoppelgangerPageState extends State<DailyDoppelgangerPage>
    with WidgetsBindingObserver {
  late Future<DailyDoppelgangerPair?> _today;
  late DateTime _openedAt;

  DateTime _now() => widget.clock?.call() ?? DateTime.now();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _refresh();
  }

  void _refresh() {
    _openedAt = _now();
    _today = _load(_openedAt);
  }

  Future<DailyDoppelgangerPair?> _load(DateTime day) async {
    final available = await (widget.catalogLoader?.call() ??
        DailyDoppelgangerCatalog.load());
    return DailyDoppelgangerRotation.open(pairs: available, now: day);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed &&
        DailyDoppelgangerRotation.dayKey(_now()) !=
        DailyDoppelgangerRotation.dayKey(_openedAt)) {
      setState(_refresh);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  String tr(String language, String key) =>
      DailyDoppelgangerCopy.t(language, key);

  Future<void> _openLink(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null || uri.scheme != 'https') return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: ArtDriftLocale.current,
      builder: (context, language, _) => Scaffold(
        backgroundColor: const Color(0xFF101117),
        appBar: AppBar(
          elevation: 0,
          backgroundColor: const Color(0xFF101117),
          foregroundColor: ArtPaper.ivory,
          leading: IconButton(
            key: const Key('daily-doppelganger-close'),
            icon: const Icon(Icons.arrow_back),
            tooltip: tr(language, 'close'),
            onPressed: () => Navigator.of(context).pop(),
          ),
          title: Text('ARTDRIFT  ·  ✦', style: const TextStyle(
            fontSize: 11, letterSpacing: 2, color: ArtPaper.faded)),
        ),
        body: FutureBuilder<DailyDoppelgangerPair?>(
          future: _today,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return Center(child: Column(mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(color: ArtPaper.gold),
                  const SizedBox(height: 20),
                  Text(tr(language, 'loading'),
                    style: const TextStyle(color: ArtPaper.ivory)),
                ]));
            }
            if (snapshot.hasError || snapshot.data == null) {
              return Center(child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.theater_comedy_outlined,
                    color: ArtPaper.faded, size: 44),
                  const SizedBox(height: 12),
                  Text(tr(language, 'empty'),
                    style: const TextStyle(color: ArtPaper.ivory)),
                  TextButton(
                    key: const Key('daily-doppelganger-retry'),
                    onPressed: () => setState(_refresh),
                    child: Text(tr(language, 'retry')),
                  ),
                ],
              ));
            }
            return _reveal(context, language, snapshot.data!);
          },
        ),
      ),
    );
  }

  Widget _reveal(BuildContext context, String locale,
      DailyDoppelgangerPair pair) => Center(
    child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 910),
      child: SingleChildScrollView(
        key: const Key('daily-doppelganger-scroll'),
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 48),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(tr(locale, 'today'),
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 10, letterSpacing: 3,
                color: Color(0xFFBC9765))),
            const SizedBox(height: 12),
            Text(tr(locale, 'title'),
              textAlign: TextAlign.center,
              style: const TextStyle(fontFamily: 'serif', fontSize: 30,
                color: ArtPaper.ivory, height: 1.15)),
            const SizedBox(height: 9),
            Text(tr(locale, 'teaser'), textAlign: TextAlign.center,
              style: const TextStyle(color: ArtPaper.faded, fontSize: 13)),
            const SizedBox(height: 10),
            Text(DailyDoppelgangerRotation.dayKey(_openedAt),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFFAC8A60), fontSize: 11)),
            const SizedBox(height: 27),
            Row(
              key: const Key('daily-doppelganger-pair'),
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: _portraitCard(context, locale, pair.portrait,
                  tr(locale, 'left'),
                  pair.artist + ' · ' + pair.year)),
                const SizedBox(width: 12),
                Expanded(child: _portraitCard(context, locale, pair.celebrity,
                  tr(locale, 'right'), pair.celebrity.license)),
              ],
            ),
            const SizedBox(height: 22),
            OrnateFrame(shadow: false,
              child: Row(children: [
                const Icon(Icons.auto_awesome_outlined,
                  color: ArtPaper.gold, size: 20),
                const SizedBox(width: 11),
                Expanded(child: Text(tr(locale, 'tomorrow'),
                  style: const TextStyle(color: ArtPaper.ink,
                    fontFamily: 'serif', fontSize: 15))),
              ]),
            ),
            const SizedBox(height: 18),
            Text(tr(locale, 'disclaimer'),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFFC5AD8B),
                fontSize: 12, height: 1.45)),
            const SizedBox(height: 5),
            Text(tr(locale, 'local'),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFFB6A58D),
                fontSize: 10, height: 1.4)),
            const SizedBox(height: 20),
            Theme(data: Theme.of(context).copyWith(
                dividerColor: Colors.transparent),
              child: ExpansionTile(
                key: const Key('daily-doppelganger-credits'),
                title: Text(tr(locale, 'credits'), style: const TextStyle(
                  color: ArtPaper.ivory, fontSize: 13)),
                iconColor: ArtPaper.faded,
                collapsedIconColor: ArtPaper.faded,
                children: [
                  _credit(locale, pair.portrait),
                  _credit(locale, pair.celebrity),
                  ListTile(
                    dense: true,
                    title: Text(tr(locale, 'editorial'),
                      style: const TextStyle(color: ArtPaper.ivory)),
                    onTap: () => _openLink(pair.editorialEvidence),
                    trailing: const Icon(Icons.open_in_new,
                      color: ArtPaper.faded, size: 18),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
  );

  Widget _portraitCard(BuildContext context, String locale,
      DailyDoppelgangerMedia media, String label, String caption) =>
      Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(label, textAlign: TextAlign.center,
          style: const TextStyle(color: Color(0xFFBDA276),
            fontSize: 10, letterSpacing: 1, fontWeight: FontWeight.bold)),
        const SizedBox(height: 9),
        OrnateFrame(
          padding: const EdgeInsets.all(6), shadow: true,
          child: AspectRatio(
            aspectRatio: 0.72,
            child: ColoredBox(
              color: const Color(0xFF251F1C),
              child: widget.imageBuilder?.call(context, media) ??
                Image.network(
                  media.previewUrl,
                  fit: BoxFit.contain, cacheWidth: kIsWeb ? null : 640,
                  semanticLabel: media.name,
                  webHtmlElementStrategy:
                      ArtRemoteImage.strategyFor(isWeb: kIsWeb),
                  errorBuilder: (_, __, ___) => Center(
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      const Icon(Icons.broken_image_outlined,
                        color: ArtPaper.faded, size: 28),
                      const SizedBox(height: 9),
                      Text(tr(locale, 'unavailable'),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: ArtPaper.ivory,
                          fontSize: 12)),
                    ]),
                  ),
                ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        Text(media.name, maxLines: 2, textAlign: TextAlign.center,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(color: ArtPaper.ivory,
            fontFamily: 'serif', fontSize: 17)),
        const SizedBox(height: 5),
        Text(caption, maxLines: 2, textAlign: TextAlign.center,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(color: ArtPaper.faded,
            fontSize: 11, height: 1.35)),
      ]);

  Widget _credit(String locale, DailyDoppelgangerMedia media) =>
      Padding(padding: const EdgeInsets.symmetric(vertical: 3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(media.name + ' · ' + media.credit,
            style: const TextStyle(color: ArtPaper.ivory, fontSize: 12)),
          Wrap(spacing: 8, children: [
            TextButton.icon(
              onPressed: () => _openLink(media.filePage),
              icon: const Icon(Icons.open_in_new, size: 14),
              label: Text(tr(locale, 'source'), style:
                  const TextStyle(fontSize: 11)),
            ),
            TextButton.icon(
              onPressed: () => _openLink(media.licenseUrl),
              icon: const Icon(Icons.copyright, size: 14),
              label: Text(media.license, style:
                  const TextStyle(fontSize: 11)),
            ),
          ]),
        ]));
}
