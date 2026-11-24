import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/features/daily_doppelganger/daily_doppelganger.dart';
import 'package:artdrift/features/daily_doppelganger/daily_doppelganger_copy.dart';
import 'package:artdrift/features/daily_doppelganger/daily_doppelganger_page.dart';
import 'package:artdrift/screens/search_sheet.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ArtDriftLocale.current.value = 'it';
  });

  test('source metadata and photo attribution are complete', () async {
    final pairs = await DailyDoppelgangerCatalog.load();
    expect(pairs.length, 5);
    expect(pairs.map((e) => e.id).toSet().length, 2);
    for (final pair in pairs) {
      expect(pair.portrait.previewUrl.startsWith('https://commons.wikimedia.org/'), true);
      expect(pair.celebrity.previewUrl.startsWith('https://commons.wikimedia.org/'), true);
      expect(pair.celebrity.credit, isNotEmpty);
      expect(pair.editorialEvidence.startsWith('https://'), true);
    }
  });

  test('source-backed expanded internal pilot contains exactly five stable QA pairs', () async {
    final pairs = await DailyDoppelgangerCatalog.load();
    expect(pairs.map((p) => p.id).toSet(), {
      'paul-mounet-keanu-reeves',
      'carl-feilberg-john-krasinski',
      'sir-david-wilkie-rupert-grint',
      'strobel-johann-vogt-robert-de-niro',
      'paul-revere-jack-black',
    });
    expect(pairs.every((p) => p.portrait.filePage.contains('commons.wikimedia.org/wiki/File:')), true);
    expect(pairs.every((p) => p.celebrity.filePage.contains('commons.wikimedia.org/wiki/File:')), true);
    expect(pairs.every((p) => p.celebrity.license.startsWith('CC BY ')), true);
    final previous = <String>[];
    for (var day = 1; day < 300; day++) {
      final date = DateTime.utc(2026, 1, 1).add(Duration(days: day));
      final chosen = DailyDoppelgangerRotation.select(
        pairs: pairs, date: date,
        previousDay: previous.isEmpty
          ? null
          : DailyDoppelgangerRotation.dayKey(date.subtract(const Duration(days: 1))),
        previousId: previous.isEmpty ? null : previous.last,
      );
      expect(chosen, isNotNull);
      if (previous.isNotEmpty) expect(chosen!.id, isNot(previous.last));
      previous.add(chosen!.id);
    }
  });

  test('same calendar day is pinned across reopen and after clock rollback', () async {
    final pairs = await DailyDoppelgangerCatalog.load();
    final a = await DailyDoppelgangerRotation.open(
        pairs: pairs, now: DateTime(2026, 11, 24, 10));
    final b = await DailyDoppelgangerRotation.open(
        pairs: [...pairs.reversed], now: DateTime(2026, 11, 24, 23, 59));
    expect(a!.id, b!.id);
    final c = await DailyDoppelgangerRotation.open(
        pairs: pairs, now: DateTime(2026, 11, 25, 0, 1));
    expect(c!.id, isNot(a.id));
    final back = await DailyDoppelgangerRotation.open(
        pairs: pairs, now: DateTime(2026, 11, 24, 14));
    expect(back!.id, c.id);
  });

  test('100 consecutive days never repeat yesterday, order-independent', () async {
    final pairs = await DailyDoppelgangerCatalog.load();
    String? lastDay;
    String? lastId;
    for (var offset = 0; offset < 100; offset++) {
      final day = DateTime(2026, 1, 1).add(Duration(days: offset));
      final current = DailyDoppelgangerRotation.select(
          pairs: pairs, date: day, previousDay: lastDay, previousId: lastId);
      final reordered = DailyDoppelgangerRotation.select(
          pairs: [...pairs.reversed], date: day,
          previousDay: lastDay, previousId: lastId);
      expect(current, isNotNull);
      expect(current!.id, reordered!.id);
      if (lastId != null) expect(current.id, isNot(lastId));
      lastId = current.id;
      lastDay = DailyDoppelgangerRotation.dayKey(day);
    }
  });

  test('fail closed on duplicate, unreviewed and miscredited assets', () async {
    final raw = await rootBundle.loadString(DailyDoppelgangerCatalog.assetPath);
    final duplicate = jsonDecode(raw) as Map<String, dynamic>;
    final pairs = duplicate['pairs'] as List;
    pairs[1]['id'] = pairs[0]['id'];
    expect(() => DailyDoppelgangerCatalog.parse(jsonEncode(duplicate)),
        throwsFormatException);
    final unpublished = jsonDecode(raw) as Map<String, dynamic>;
    (unpublished['pairs'] as List)[0]['status'] = 'DRAFT';
    expect(() => DailyDoppelgangerCatalog.parse(jsonEncode(unpublished)),
        throwsFormatException);
    final swapped = jsonDecode(raw) as Map<String, dynamic>;
    (swapped['pairs'] as List)[0]['celebrity']['fileName'] = 'Wrong Photo.jpg';
    expect(() => DailyDoppelgangerCatalog.parse(jsonEncode(swapped)),
        throwsFormatException);
  });

  test('complete core copy in all six supported languages', () {
    for (final lang in ArtDriftLocale.codes) {
      for (final key in [
        'title', 'teaser', 'cta', 'today', 'left', 'right',
        'tomorrow', 'disclaimer', 'credits', 'unavailable',
      ]) {
        final value = DailyDoppelgangerCopy.t(lang, key);
        expect(value, isNotEmpty);
        expect(value, isNot(key));
      }
    }
  });

  testWidgets('320dp viewport keeps portrait LEFT and celebrity RIGHT in a row',
      (tester) async {
    tester.view.physicalSize = const Size(320, 760);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    // WidgetTester uses FakeAsync: do NOT await rootBundle inside testWidgets.
    // The real catalog and rotation are already covered in non-widget tests.
    const fixture = DailyDoppelgangerPair(
      id: 'fixture-pair',
      artist: 'Fixture painter',
      year: '1875',
      editorialEvidence: 'https://example.org/fixture',
      portrait: DailyDoppelgangerMedia(
        name: 'Portrait fixture', fileName: 'portrait.jpg',
        filePage: 'https://commons.wikimedia.org/wiki/File:portrait.jpg',
        credit: 'Fixture painter', license: 'Public domain',
        licenseUrl: 'https://creativecommons.org/publicdomain/mark/1.0/'),
      celebrity: DailyDoppelgangerMedia(
        name: 'Celebrity fixture', fileName: 'celebrity.jpg',
        filePage: 'https://commons.wikimedia.org/wiki/File:celebrity.jpg',
        credit: 'Fixture photographer', license: 'CC BY 2.0',
        licenseUrl: 'https://creativecommons.org/licenses/by/2.0/'),
    );
    await tester.pumpWidget(MaterialApp(home: DailyDoppelgangerPage(
      clock: () => DateTime(2026, 11, 24, 11),
      previewPair: fixture,
      imageBuilder: (_, media) => ColoredBox(
        key: Key('fake-image-' + media.name),
        color: const Color(0xFF43382D)),
    )));
    await tester.pump();
    final row = tester.widget<Row>(
        find.byKey(const Key('daily-doppelganger-pair')));
    expect(row.children.length, 3);
    expect(find.text('Doppleganger del giorno'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.drag(find.byKey(const Key('daily-doppelganger-scroll')),
        const Offset(0, -500));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('daily-doppelganger-credits')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('curated search entry invokes the daily view once',
      (tester) async {
    var opened = 0;
    await tester.pumpWidget(MaterialApp(home: Builder(
      builder: (context) => Scaffold(body: TextButton(
        child: const Text('Open search'),
        onPressed: () => showArtSearchSheet(context, const [],
            onOpenDoppelganger: () => opened++),
      )),
    )));
    await tester.tap(find.text('Open search'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('artdrift-daily-doppelganger-entry')),
        findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-daily-doppelganger-entry')));
    await tester.pumpAndSettle();
    expect(opened, 1);
  });
}
