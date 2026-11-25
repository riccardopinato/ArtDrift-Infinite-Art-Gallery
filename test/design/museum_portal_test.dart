import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/ui/localization.dart';
import 'package:artdrift/ui/museum_portal.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ArtDriftLocale.current.value = 'it';
  });

  testWidgets('approved Italian portal copy and no artificial delay',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(home: MuseumPortal.loading()));
    expect(find.byKey(const Key('artdrift-portal-line1')), findsOneWidget);
    expect(find.text('Il museo sta aprendo'), findsOneWidget);
    expect(find.text('la visita sta per cominciare'), findsOneWidget);
    expect(find.text('Carichiamo le opere del tuo museo…'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-portal-progress')), findsOneWidget);
    expect(find.byKey(const Key('artdrift-portal-retry')), findsNothing);
  });

  testWidgets('error shows real retry callback, no success simulation',
      (tester) async {
    var retries = 0;
    await tester.pumpWidget(MaterialApp(home: MuseumPortal.unavailable(
      onRetry: () => retries++,
    )));
    expect(find.text('La galleria non è disponibile'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-portal-progress')), findsNothing);
    await tester.tap(find.byKey(const Key('artdrift-portal-retry')));
    await tester.pump();
    expect(retries, 1);
    expect(find.text('La galleria non è disponibile'), findsOneWidget);
  });

  testWidgets('portal structural labels are localized in all six languages',
      (tester) async {
    for (final code in ArtDriftLocale.codes) {
      ArtDriftLocale.current.value = code;
      await tester.pumpWidget(const MaterialApp(
        home: MuseumPortal.loading(),
      ));
      expect(find.text(ArtDriftLocale.text('portalEntryLabel')),
          findsOneWidget);
      expect(find.text(ArtDriftLocale.text('portalFooter')),
          findsOneWidget);

      await tester.pumpWidget(MaterialApp(
        home: MuseumPortal.unavailable(onRetry: () {}),
      ));
      expect(find.text(ArtDriftLocale.text('portalInterruptionLabel')),
          findsOneWidget);
    }
  });

  testWidgets('six locales have nonempty and distinct portal headlines',
      (tester) async {
    final seen = <String>{};
    for (final code in ArtDriftLocale.codes) {
      ArtDriftLocale.current.value = code;
      await tester.pumpWidget(const MaterialApp(
        home: MuseumPortal.loading()));
      final headline = ArtDriftLocale.text('portalLine1');
      expect(headline, isNotEmpty);
      expect(ArtDriftLocale.text('portalLine2'), isNotEmpty);
      seen.add(headline);
    }
    expect(seen.length, 6);
  });
}
