// Browser-specific prefetch: the museum is contacted as an HTML <img>, not
// via a CORS-restricted byte fetch. The browser manages its own HTTP cache
// according to museum-provided response headers.
import 'dart:async';
import 'dart:html' as html;

import 'package:flutter/widgets.dart';

Future<bool> warmMuseumImage(BuildContext context, String url) async {
  if (!context.mounted) return false;
  final element = html.ImageElement();
  final completed = Completer<bool>();
  final onLoad = element.onLoad.listen((_) {
    if (!completed.isCompleted) completed.complete(true);
  });
  final onError = element.onError.listen((_) {
    if (!completed.isCompleted) completed.complete(false);
  });
  try {
    // Attach listeners BEFORE assigning src, including for HTTP cache hits.
    element.src = url;
    return await completed.future.timeout(
      const Duration(seconds: 7), onTimeout: () => false);
  } catch (_) {
    return false;
  } finally {
    await onLoad.cancel();
    await onError.cancel();
    // Do not persist or rehost the image. Browser HTTP caching is controlled
    // by each origin; a newly displayed <img> may reuse it when permitted.
  }
}
