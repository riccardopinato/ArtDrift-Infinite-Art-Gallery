import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../ui/localization.dart';

class DopplegangerScreen extends StatefulWidget {
  const DopplegangerScreen({super.key});

  @override
  State<DopplegangerScreen> createState() => _DopplegangerScreenState();
}

class _DopplegangerScreenState extends State<DopplegangerScreen> {
  late Future<List<Map<String, dynamic>>> _catalog = _load();
  int _index = 0;
  List<String>? _choices;
  String? _answer;
  bool _revealed = false;
  String _text(String key) => ArtDriftLocale.text(key);

  Future<List<Map<String, dynamic>>> _load() async {
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
      _index = (_index + 1) % total;
      _choices = null;
      _answer = null;
      _revealed = false;
    });
  }

  Widget _image(Map<String, dynamic> data, {required String label}) =>
      SizedBox(
        height: 230,
        child: Image.memory(
          base64Decode(data['image'] as String),
          fit: BoxFit.contain,
          semanticLabel: label,
        ),
      );

  Widget _credits(Map<String, dynamic> data) {
    final links = (data['links'] as List).cast<String>();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(data['credit'] as String),
        Wrap(children: [
          for (var index = 0; index < links.length; index++)
            TextButton(
              onPressed: () async {
                final opened = await launchUrl(Uri.parse(links[index]));
                if (!opened && mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(_text('doppleUnavailable'))),
                  );
                }
              },
              child: Text(_text(index == 0 ? 'doppleLicense' : 'doppleSource')),
            ),
        ]),
      ],
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Doppleganger')),
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
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
          children: [
            Text(_text('doppleQuestion'),
              style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 16),
            _image(art, label: _text('dopplePortrait')),
            const SizedBox(height: 16),
            if (!_revealed) ...[
              for (final option in options)
                OutlinedButton(
                  onPressed: () => setState(() {
                    _answer = option;
                    _revealed = true;
                  }),
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
              Text(correct, style: Theme.of(context).textTheme.headlineSmall),
              Text(title),
              const SizedBox(height: 12),
              _image(person, label: correct),
              const SizedBox(height: 12),
              Text(round['note'] as String),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: () => _next(rows.length),
                child: Text(_text('doppleNext')),
              ),
              ExpansionTile(
                title: Text(_text('doppleCredits')),
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
