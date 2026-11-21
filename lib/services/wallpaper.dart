import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

import '../models/artwork.dart';

/// Explicit user action only: no automatic home/lock change in v0.1.
class AndroidWallpaper {
  static const channel = MethodChannel('artdrift/wallpaper');

  static Future<Uint8List> compose(Artwork artwork,
      {bool entireImage = true}) async {
    if (!artwork.displayable) throw StateError('Opera non autorizzata.');
    final response = await http.get(Uri.parse(artwork.imageUrl(width: 843)))
        .timeout(const Duration(seconds: 25));
    if (response.statusCode != 200 || response.bodyBytes.isEmpty ||
        response.bodyBytes.length > 24 * 1024 * 1024) {
      throw const HttpException('Immagine non disponibile per lo sfondo');
    }
    final codec = await ui.instantiateImageCodec(response.bodyBytes,
      targetWidth: 843);
    final frame = await codec.getNextFrame();
    codec.dispose();
    final image = frame.image;
    const width = 1080.0;
    const height = 1920.0;
    final factor = entireImage
        ? math.min(width / image.width, height / image.height)
        : math.max(width / image.width, height / image.height);
    final scaledW = image.width * factor;
    final scaledH = image.height * factor;
    final recorder = ui.PictureRecorder();
    final canvas = ui.Canvas(recorder);
    canvas.drawColor(const ui.Color(0xFF101117), ui.BlendMode.src);
    canvas.drawImageRect(image,
      ui.Rect.fromLTWH(0, 0, image.width.toDouble(), image.height.toDouble()),
      ui.Rect.fromLTWH((width - scaledW) / 2, (height - scaledH) / 2,
        scaledW, scaledH),
      ui.Paint()..filterQuality = ui.FilterQuality.high);
    final picture = recorder.endRecording();
    final output = await picture.toImage(width.toInt(), height.toInt());
    final bytes = await output.toByteData(format: ui.ImageByteFormat.png);
    output.dispose();
    image.dispose();
    picture.dispose();
    if (bytes == null) throw StateError('Composizione sfondo non riuscita');
    return bytes.buffer.asUint8List();
  }

  static Future<void> apply(Uint8List bytes, String target) async {
    if (bytes.length > 24 * 1024 * 1024) {
      throw StateError('Sfondo troppo grande per questo dispositivo');
    }
    final success = await channel.invokeMethod<bool>('setWallpaper', {
      'bytes': bytes, 'target': target,
    });
    if (success != true) throw StateError('Sfondo non confermato da Android');
  }
}
