import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:artdrift/services/catalog_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('real painting bootstrap is bundled, displayable and under 2 MB', () async {
    final service = CatalogService();
    addTearDown(service.close);
    final works = await service.bundled();
    expect(works.length, greaterThanOrEqualTo(28));
    expect(works.every((a) => a.displayable && a.hasBundledPreview), isTrue);
    expect(works.map((a) => a.id).toSet().length, works.length);
    var compressedBytes = 0;
    for (final painting in works) {
      final bytes = await rootBundle.load(painting.bootstrapAsset);
      expect(bytes.lengthInBytes, greaterThan(100));
      expect(bytes.lengthInBytes, lessThanOrEqualTo(45000));
      compressedBytes += bytes.lengthInBytes;
    }
    expect(compressedBytes, lessThan(2 * 1024 * 1024));
  });

  test('initial catalog loads real artwork with no network dependency', () async {
    final service = CatalogService();
    addTearDown(service.close);
    final art = await service.load();
    expect(art.length, greaterThanOrEqualTo(28));
    expect(art.every((a) => a.hasBundledPreview), isTrue);
  });
}
