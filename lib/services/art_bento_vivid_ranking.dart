import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../models/artwork.dart';
import 'art_joyful_palette.dart';

/// Offline curation: 800 highest-ranked images from an independent visual
/// audit of the exact 4,499 packaged source-verified WebPs, not a remote API.
/// Vivid non-sepia chroma, blue/green/red diversity, luminance and scenery
/// increase a score; older manuscript-like works and yellow-only backgrounds
/// are penalized. An 80-work contact sheet was reviewed. Full QA remains HOLD.
///
/// The 800 *ordered* big-endian uint16 indices refer to sorted catalog keys,
/// NOT item positions in an individual user's pinned canvas playlist.
/// Corpus fingerprint and duplicates are checked before applying any ranks.
/// Rank bytes SHA256: 07777d4168d6fdd8aef82bc8f2c252d3c38c848298908eba6bd3a1e2569672e7
class ArtBentoVividRanking {
  ArtBentoVividRanking._();
  static const int expectedFingerprint = 2742452096;
  static const int count = 800;

  static const String _rankBytes = 'AFQHDhF+Bg0MKQAcBD8ECwMKCqYKPwjOCF8GZwDqClIJOgjqABIA0xEJAB0BEgFbAFUBFApzDj4AzgIbCkgAOgkgEQ4FcgkrCSwQyAeZCRwKBAjMCoANKQ5MD1wBrwYBCosKtQCMCnsDWwenCgYQVQV3ByQJwAqSCecJ/Q0HDe0BeAZzBycCPQQKDLwIcQBtAPcD3QizCQ8L3wxyAOUA/AOTCZQJtwm5DCUPvQoKCh4KegtnDXsAPAqXAL4CCAW5CU4LaAwIDA0QcwBJBUIGwgl7DpAALgAyAD4AdAmQCZMJmgpfCpkKvRDlABMAIwBXAL0BCATRBNIFtwZkCRIJlgjiCSIJNwlXCYwKYA5PD7gD8QSwCREJrQnzCgkPMhBiAAAFwQ64AO4JJgktCYsJrgpbDwcQLADsAaIDSwk0CU8JfgoWCqEMqw1JDo8B0wMUBKQFjAZ8CnkN6w7eEMkADgAwADkEtAaEBxAHFQeeCYAJqgnZERUAbAWLBZsHCAd4B68IZwiqCRUJ7woiC30NeQ+MANsBfAISBTcFiAWJBhoItgk5CXwJvQyEDXIOzQ9BASwBfwGqBQUFigqyDPIM/A8VACEERwbcBwsHZQjhCeEKGA1oDWoAFAAoBMMFVAkuCnYKww1iDoYQPxGGAz0E8wVVBWUFlQYwBz4HQQnHCgEKlAqzDKoOgg/3AhEDlgc3ClcNsw6qEIsRUQE2A14Fxwc6CSEMSw9qEPgBewHQA2sGWQZ3BygHQgdFCJEJFAmPCm4MGw3uEIAACQNYBUQGswiLCWcJaglrCbsMawy+DR0NvA6AAD0D+wiGCVgKxg1aDY4NlQBFAO0DvQWdBrQGtQctB0YHfglfCbYJ1An0CngKhwqYCqkL3QxdDfoOTQ6xDsoQOxF5AfYE+AWeBmEGYglECXMJvgpmCowMVAy1DeoQNRBmEZAAcgGAAacFnAc5B4gHxgf9CVsJYAlkCaQKUwwiDnYP1Q//EUUBpASMBw0JSwlQCV0JZQl2CdgKHQr/C/sMgAz7DiMO3RCIEUQAFQAvAygEyATdBRoFdQczB4QJTQltCXAMFwzIDQ8N5Q4EDuMP/BA9ANYA7wIdBHsFYAcrB2wJSglRCVkJWgljCXEJngphCq0K5wwADBYMSQ0SDXoN0g6tDrAPQg99EBAAGwBRBIUGWwlUCVwJYQlpCW4JhwmICZkJ+wpFCncKhgwaDLcNAw2EDaENtg3DDikOyQ8UD2gRCxENAIQCBQbnBxgHmglvCYIJgwm6CkMNEw2mDiIOxxAZEN4RWxFwAAEAugNdBH0HNAdECRsJXgliCWgJcgl1CXcJhQmRCawKnA1lDYAN3g8+D7kQLRDYAFwAdwDQBTEFOAdACRoJZgl5CYYJiQmcCkIKkQqTDbQOAw/uAjEGmgfCCAUJPAlFCYEKnQquCuYNOQ3kDwQPHw83D78PzxEmABABJgEoBWoFfwW4BqQImAjJCNkJFwl0CZUJswpWCoEKpwv0DHUM4Q2UDdoPrw/EEJUQswIeAywFhQbGCM8I1AkWCR8JmAnXCekKowvTC/8MSgymDNYNJg0nDX8N+Q5+EN8RJBE1AAsAMwBjAWYBeQVnBiYHGwmKCa8JuAqCCooLsgwMDRgNZg3PEGgRIgMmBIAEgwTgBxEHFAelCAYJGQkdCVYJegmfCicKMgpUCswKzgz/Do4PAA8DDycRBAAaAZcEvQWEBbIGDwmSCl0KfA0QDSUOdA7BD1gAKQBGAFkAawH7AhUEQQSHBm8GdgddCX0J2gqfC2UMjA0vDbIOXBEPEU4RkwAZASQBxQIWBDcEsgT+BcAI0wlMCY0JsApeCo4L3gvnDGINBA6vES0AWAB1AHoAvAHNAzQEnwYHBsMG5AeDB7QJVQm1CcEKFAoXClUL8Aw0DEINkQ2YDtMO2A8sD+sQHhAmEJAQshEoACQANAA7AFIDWgR3BugJMgmECfEKLAw1DFYMYAyeDRoQNxErAGYA4gDrAWECRwMYA4wELgYSCNgJUwnVCggKEgoxC0IL/AyPDLsNWA/bEAwRBxFVAHABKwHYA2YDiAR+BIkEqAWzBuYHZAhUCJIIvgk2CaAJsgm8ClkMuQ2MEAIQHBDoADYAXwE+AX4CLA==';

  /// Pure transform: existing score manifest must agree with full catalog,
  /// otherwise return the unmodified original map (fail closed).
  @visibleForTesting
  static Map<String,int> prioritize(List<Artwork> catalog,
      Map<String,int> pixelScores) {
    if (catalog.length != 4500 || pixelScores.length != catalog.length) {
      return pixelScores;
    }
    final keys = catalog.map((art) => art.catalogKey).toList()..sort();
    if (keys.toSet().length != keys.length ||
        ArtJoyfulPalette.fingerprint(keys) != expectedFingerprint) {
      return pixelScores;
    }
    final bytes = base64Decode(_rankBytes);
    if (bytes.length != count * 2) return pixelScores;
    final indices = <int>[];
    for (var i=0; i<bytes.length; i+=2) {
      final index = (bytes[i] << 8) | bytes[i+1];
      if (index >= keys.length) return pixelScores;
      indices.add(index);
    }
    if (indices.toSet().length != indices.length) return pixelScores;
    // Non-hero supporting imagery retains its relative source pixel score,
    // but cannot displace the vetted vivid band in the XL frames.
    final result = <String,int>{
      for (final key in keys) key: (pixelScores[key] ?? 0).clamp(0,70).toInt(),
    };
    for (var rank=0; rank<indices.length; rank++) {
      result[keys[indices[rank]]] = 255 - (rank * 144 ~/ (count-1));
    }
    return Map.unmodifiable(result);
  }
}
