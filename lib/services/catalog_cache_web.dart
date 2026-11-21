import 'package:shared_preferences/shared_preferences.dart';

const _catalogKey = 'artdrift-catalog-v1.json';

Future<String?> read() async {
  final preferences = await SharedPreferences.getInstance();
  return preferences.getString(_catalogKey);
}

Future<void> write(String content) async {
  final preferences = await SharedPreferences.getInstance();
  await preferences.setString(_catalogKey, content);
}
