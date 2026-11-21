import 'package:shared_preferences/shared_preferences.dart';

class Favorites {
  static const _key = 'artdrift.favorites.v1';
  final Set<int> ids = {};

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    ids.addAll((prefs.getStringList(_key) ?? const [])
        .map(int.tryParse).whereType<int>());
  }

  bool contains(int id) => ids.contains(id);

  Future<void> toggle(int id) async {
    if (!ids.add(id)) ids.remove(id);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_key, ids.map((id) => '$id').toList());
  }
}
