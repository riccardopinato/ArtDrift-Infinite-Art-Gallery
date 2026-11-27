import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../ui/localization.dart';
import '../ui/parchment.dart';

class DopplegangerScreen extends StatefulWidget {
  const DopplegangerScreen({super.key, this.catalogLoader});

  /// Allows deterministic catalogue loading in widget tests without changing
  /// the bundled, verified portrait catalogue used by the actual app.
  final Future<List<Map<String, dynamic>>> Function()? catalogLoader;

  @override
  State<DopplegangerScreen> createState() => _DopplegangerScreenState();
}

class _DopplegangerScreenState extends State<DopplegangerScreen> {
  late Future<List<Map<String, dynamic>>> _catalog = _load();
  int _index = 0;
  List<String>? _choices;
  String? _answer;
  bool _revealed = false;
  int _correct = 0;
  // Reuse the same decoded bytes for repeated reveals and back-to-back
  // widget rebuilds. All 87 embedded image pairs total about 1 MB as JSON;
  // entries are created lazily and never trigger a network read.
  final _decodedImages = <String, Uint8List>{};
  static const _scoreWords = <String, String>{
    'it': 'corrette', 'en': 'correct', 'fr': 'bonnes réponses',
    'es': 'aciertos', 'de': 'richtig', 'pt': 'certas',
  };
  String _text(String key) => ArtDriftLocale.text(key);

  Future<List<Map<String, dynamic>>> _load() async {
    if (widget.catalogLoader != null) {
      return widget.catalogLoader!();
    }
    final raw = await rootBundle.loadString('assets/doppleganger.json');
    final rows = (jsonDecode(raw) as List).cast<Map<String, dynamic>>();
    final verified = rows.where((row) => row['status'] == 'verified').toList();
    if (verified.map((row) => row['person']['name']).toSet().length < 3) {
      throw const FormatException('Incomplete Doppleganger catalog');
    }
    return verified..shuffle();
  }

  void _next(int total) {
    setState(() {
      if (_index + 1 >= total) _correct = 0;
      _index = (_index + 1) % total;
      _choices = null;
      _answer = null;
      _revealed = false;
    });
  }

  Widget _image(Map<String, dynamic> data, {required String label}) {
    final encoded = data['image'] as String;
    final bytes = _decodedImages.putIfAbsent(encoded,
      () => base64Decode(encoded));
    return DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFF1E1B20),
          border: Border.all(color: const Color(0xFFC9A574), width: 1.2),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Padding(
          padding: const EdgeInsets.all(9),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: Image.memory(
              bytes,
              height: MediaQuery.sizeOf(context).height < 700 ? 164 : 230,
              width: double.infinity,
              fit: BoxFit.contain, semanticLabel: label,
              errorBuilder: (_, __, ___) => const SizedBox(height: 230,
                child: Center(child: Icon(Icons.image_not_supported,
                  color: ArtPaper.faded))),
            ),
          ),
        ),
      );
  }

  Widget _credits(Map<String, dynamic> data) {
    final links = (data['links'] as Map).cast<String, String>();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(data['credit'] as String,
          style: const TextStyle(color: ArtPaper.ivory)),
        Wrap(children: [
          for (final link in links.entries)
            TextButton(
              onPressed: () async {
                var opened = false;
                try {
                  final uri = Uri.tryParse(link.value);
                  if (uri != null && uri.scheme == 'https' &&
                      uri.userInfo.isEmpty &&
                      (!uri.hasPort || uri.port == 443)) {
                    opened = await launchUrl(uri,
                      mode: LaunchMode.externalApplication);
                  }
                } on PlatformException {
                  // The browser or platform may reject external navigation.
                }
                if (!opened && mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(_text('doppleUnavailable'))),
                  );
                }
              },
              child: Text(_text(link.key)),
            ),
        ]),
      ],
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF101117),
    appBar: AppBar(
      backgroundColor: const Color(0xFF101117),
      foregroundColor: ArtPaper.ivory,
      centerTitle: true,
      title: const Text('DOPPLEGANGER', style: TextStyle(
        fontFamily: 'serif', letterSpacing: 1.8,
        fontSize: 17, color: ArtPaper.ivory)),
    ),
    body: FutureBuilder<List<Map<String, dynamic>>>(
      future: _catalog,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(child: FilledButton(
            onPressed: () => setState(() => _catalog = _load()),
            child: Text(_text('doppleRetry')),
          ));
        }
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final rows = snapshot.requireData;
        final round = rows[_index];
        final art = round['art'] as Map<String, dynamic>;
        final person = round['person'] as Map<String, dynamic>;
        final correct = person['name'] as String;
        final options = _choices ??= _makeChoices(rows, correct);
        final title = art['name'] as String;
        return ListView(
          key: ValueKey(round['id']),
          padding: const EdgeInsets.fromLTRB(20, 17, 20, 48),
          children: [
            const Text('ARTDRIFT  ·  CURIOSITÀ', style: TextStyle(
              color: ArtPaper.gold, fontSize: 10, letterSpacing: 2)),
            const SizedBox(height: 9),
            Text(
              '${_index + 1}/${rows.length}  ·  $_correct '
              '${_scoreWords[ArtDriftLocale.current.value] ?? _scoreWords['en']}',
              key: const Key('dopple-progress'),
              style: const TextStyle(color: ArtPaper.faded,
                fontSize: 12, letterSpacing: .2),
            ),
            const SizedBox(height: 8),
            Text(_text('doppleQuestion'), style: const TextStyle(
              color: ArtPaper.ivory, fontSize: 27,
              fontFamily: 'serif', height: 1.18)),
            const SizedBox(height: 16),
            _image(art, label: _text('dopplePortrait')),
            const SizedBox(height: 16),
            if (!_revealed) ...[
              for (final option in options)
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: ArtPaper.ivory,
                    side: const BorderSide(color: Color(0xFF94703F)),
                    padding: const EdgeInsets.symmetric(vertical: 14)),
                  onPressed: () {
                    // A second queued tap in the same frame cannot score twice.
                    if (_revealed) return;
                    setState(() {
                      _answer = option;
                      _revealed = true;
                      if (option == correct) _correct++;
                    });
                  },
                  child: Text(option),
                ),
              TextButton(
                onPressed: () => setState(() => _revealed = true),
                child: Text(_text('doppleReveal')),
              ),
            ] else ...[
              if (_answer != null)
                Semantics(
                  liveRegion: true,
                  child: Text(_text(_answer == correct
                    ? 'doppleCorrect' : 'doppleMiss')),
                ),
              Text(correct, style: const TextStyle(
                color: ArtPaper.ivory, fontFamily: 'serif', fontSize: 26)),
              Text(title, style: const TextStyle(color: ArtPaper.faded)),
              const SizedBox(height: 12),
              _image(person, label: correct),
              const SizedBox(height: 12),
              Text(round['note'] as String, style: const TextStyle(
                color: ArtPaper.ivory, height: 1.55, fontSize: 14)),
              const SizedBox(height: 12),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: ArtPaper.gold,
                  foregroundColor: ArtPaper.ivory,
                  padding: const EdgeInsets.symmetric(vertical: 14)),
                onPressed: () => _next(rows.length),
                child: Text(_text('doppleNext')),
              ),
              ExpansionTile(
                title: Text(_text('doppleCredits'),
                  style: const TextStyle(color: ArtPaper.faded)),
                children: [_credits(art), _credits(person)],
              ),
            ],
          ],
        );
      },
    ),
  );

  List<String> _makeChoices(List<Map<String, dynamic>> rows, String correct) {
    final alternatives = rows.map((row) => row['person']['name'] as String)
        .where((name) => name != correct).toSet().toList()..shuffle();
    return [correct, ...alternatives.take(2)]..shuffle();
  }
}
