import 'package:flutter/material.dart';

/// Native-only: uses the same resized ImageProvider key as a 400px canvas tile.
/// The Flutter image cache can reuse the decoded result where applicable.
Future<bool> warmMuseumImage(BuildContext context, String url) async {
  if (!context.mounted) return false;
  var failed = false;
  final image = ResizeImage.resizeIfNeeded(400, null, NetworkImage(url));
  try {
    await precacheImage(image, context, onError: (error, stack) {
      failed = true;
    }).timeout(const Duration(seconds: 7));
    return !failed;
  } catch (_) {
    return false;
  }
}
