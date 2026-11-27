import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_test/flutter_test.dart';

/// Deterministic identity/source checks. This is NOT a visual resemblance
/// rating, proof of image licensing or independent editorial certification.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('every published Doppelganger pair has unique IDs and traceable images',
      () async {
    final raw = await rootBundle.loadString('assets/doppleganger.json');
    final rows = (jsonDecode(raw) as List<dynamic>)
        .cast<Map<String, dynamic>>();
    expect(rows.length, 87);
    final ids = <String>{};
    final people = <String>{};
    for (final row in rows) {
      final id = row['id'] as String;
      expect(ids.add(id), isTrue, reason: 'duplicate pair ID: $id');
      expect(row['status'], 'verified');
      expect((row['note'] as String).trim().length, greaterThan(20));
      final art = (row['art'] as Map).cast<String, dynamic>();
      final person = (row['person'] as Map).cast<String, dynamic>();
      people.add(person['name'] as String);
      for (final item in [art, person]) {
        expect((item['name'] as String).trim(), isNotEmpty);
        expect((item['credit'] as String).trim(), isNotEmpty);
        final bytes = base64Decode(item['image'] as String);
        expect(bytes.length, greaterThan(150),
            reason: 'invalid image payload at $id');
        // Real packaged portrait bytes must have a WebP RIFF header. This
        // checks packaging identity, not visual/subject/editorial accuracy.
        expect(utf8.decode(bytes.sublist(0, 4)), 'RIFF');
        expect(utf8.decode(bytes.sublist(8, 12)), 'WEBP');
        final links = (item['links'] as Map).cast<String, String>();
        for (final key in ['doppleSource', 'doppleLicense']) {
          final uri = Uri.tryParse(links[key] ?? '');
          expect(uri, isNotNull, reason: '$id has no $key');
          expect(uri!.scheme, 'https');
          expect(uri.host, isNotEmpty);
          expect(uri.userInfo, isEmpty);
        }
      }
      // The exact pairs previously rejected by the product owner must not
      // return simply because a separate pairing uses the same celebrity.
      final name = (person['name'] as String).toLowerCase();
      final painting = (art['name'] as String).toLowerCase();
      expect(name == 'rupert grint' &&
          painting.contains('paul smith palmer'), isFalse);
      expect(name == 'timothée chalamet' &&
          painting.contains('franz liszt'), isFalse);
      expect(name == 'daniel radcliffe' &&
          painting.contains('franz liszt'), isFalse);
      expect(name == 'paul giamatti' &&
          painting.contains('john adams'), isFalse);
    }
    expect(people.length, greaterThanOrEqualTo(3));
  });
}
