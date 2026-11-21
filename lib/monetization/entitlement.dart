/// Provider-agnostic entitlement boundary per App Factory Golden.
/// No fake Pro, purchases or ad requests until Play provider verification.
enum ArtDriftPlan { free, proLifetime }
enum ArtDriftEntitlementSource { localDefault, providerVerified, offlineCache, unknown }

class ArtDriftEntitlement {
  const ArtDriftEntitlement({required this.plan, required this.source,
    this.verifiedAt});
  final ArtDriftPlan plan;
  final ArtDriftEntitlementSource source;
  final DateTime? verifiedAt;

  bool get proVerified => plan == ArtDriftPlan.proLifetime &&
      (source == ArtDriftEntitlementSource.providerVerified ||
       source == ArtDriftEntitlementSource.offlineCache) &&
      verifiedAt != null;
  bool get suppressAds => proVerified;
}

abstract final class ProAccess {
  static const storeCatalogConfigured = false;
  static const ArtDriftEntitlement current = ArtDriftEntitlement(
    plan: ArtDriftPlan.free, source: ArtDriftEntitlementSource.localDefault);
  static bool get mayOfferPurchase => storeCatalogConfigured;
  static bool get mayRequestAds => !current.suppressAds;
}
