import 'dart:io';
import 'package:path_provider/path_provider.dart';

Future<File> _cacheFile() async {
  final directory = await getApplicationSupportDirectory();
  return File('${directory.path}/artdrift-catalog-v1.json');
}

Future<String?> read() async {
  final file = await _cacheFile();
  if (!await file.exists()) return null;
  return file.readAsString();
}

Future<void> write(String content) async {
  final file = await _cacheFile();
  final pending = File('${file.path}.pending');
  await pending.writeAsString(content, flush: true);
  await pending.rename(file.path);
}
