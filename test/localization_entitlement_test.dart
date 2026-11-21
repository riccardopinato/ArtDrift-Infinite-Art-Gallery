import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/monetization/entitlement.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  test('free/default is never incorrectly marked purchased or ad-free', () {
    expect(ProAccess.current.proVerified, isFalse);
    expect(ProAccess.current.suppressAds, isFalse);
    expect(ProAccess.mayOfferPurchase, isFalse);
    expect(const ArtDriftEntitlement(
      plan: ArtDriftPlan.proLifetime,
      source: ArtDriftEntitlementSource.unknown).proVerified, isFalse);
  });
  test('entitlements require provider evidence, not just a plan flag', () {
    final valid = ArtDriftEntitlement(plan: ArtDriftPlan.proLifetime,
      source: ArtDriftEntitlementSource.providerVerified,
      verifiedAt: DateTime.utc(2026, 11, 21));
    expect(valid.proVerified, isTrue);
    expect(valid.suppressAds, isTrue);
  });
  test('all six locales have search and settings core labels', () {
    expect(ArtDriftLocale.codes.length, 6);
    for (final code in ArtDriftLocale.codes) {
      ArtDriftLocale.current.value = code;
      for (final key in ['search','searchTitle','settings','language',
          'filterArtist','filterTitle','filterSubject','about','pro','close']) {
        expect(ArtDriftLocale.text(key), isNotEmpty);
      }
    }
    ArtDriftLocale.current.value = 'it';
  });
}
