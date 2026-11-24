import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:artdrift/screens/museum_cloud_catalog_page.dart';
import 'package:artdrift/services/museum_cloud_catalog.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  setUp(() {
    ArtDriftLocale.current.value = 'it';
  });

  MuseumCloudCatalog fakeCatalog({String? sourceUrl}) {
    return MuseumCloudCatalog(
      baseUrl: 'https://d1.test',
      client: MockClient((req) async {
        expect(req.url.path, '/api/v1/museum-search');
        expect(req.url.queryParameters['q'], 'painting');
        return http.Response(jsonEncode({
          'source': 'ArtDrift-Museums',
          'count': 1,
          'next_cursor': null,
          'works': [
            {
              'source_key': 'met:991',
              'museum_source': 'met',
              'title': 'Openable artwork',
              'artist': 'Artist Example',
              'museum_name': 'The Metropolitan Museum of Art',
              'date': '1900',
              'medium': 'Oil on canvas',
              'rights_license': 'CC0',
              'rights_evidence_url':
                  'https://www.metmuseum.org/about-the-met/policies-and-documents/open-access',
              'credit_line': 'Museum example credit',
              'source_url': sourceUrl,
              // Deliberately no image: detail must still open.
              'thumbnail_url': null,
            }
          ],
        }), 200);
      }),
    );
  }

  testWidgets('D1 record without official URL opens its own detail', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: MuseumCloudCatalogPageScreen(
        initialQuery: 'painting',
        catalog: fakeCatalog(),
      ),
    ));
    await tester.pumpAndSettle();
    const key = ValueKey('artdrift-d1-work-met:991');
    expect(find.byKey(key), findsOneWidget);
    final row = tester.widget<ListTile>(find.byKey(key));
    expect(row.onTap, isNotNull,
        reason: 'Metadata-only search results must never be disabled');
    await tester.tap(find.byKey(key));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('artdrift-d1-detail-title')), findsOneWidget);
    expect(find.text('Openable artwork'), findsOneWidget);
    expect(find.text('The Metropolitan Museum of Art'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-d1-detail-image')), findsOneWidget);
    expect(find.byKey(const Key('artdrift-d1-detail-official')), findsNothing);
    expect(find.byKey(const Key('artdrift-d1-detail-rights')), findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-d1-detail-back')));
    await tester.pumpAndSettle();
    expect(find.byKey(key), findsOneWidget);
  });

  testWidgets('D1 record with official URL still opens internal detail', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: MuseumCloudCatalogPageScreen(
        initialQuery: 'painting',
        catalog: fakeCatalog(sourceUrl:
          'https://www.metmuseum.org/art/collection/search/991'),
      ),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('artdrift-d1-work-met:991')));
    await tester.pumpAndSettle();
    expect(find.text('Openable artwork'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-d1-detail-official')), findsOneWidget);
    expect(find.byKey(const Key('artdrift-d1-detail-rights')), findsOneWidget);
  });
}
