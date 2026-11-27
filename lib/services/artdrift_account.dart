import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Optional account: the museum is usable without any cloud configuration.
class ArtDriftAccount extends ChangeNotifier {
  ArtDriftAccount._();
  static final ArtDriftAccount instance = ArtDriftAccount._();

  static const url = String.fromEnvironment('SUPABASE_URL');
  static const publishableKey =
      String.fromEnvironment('SUPABASE_PUBLISHABLE_KEY');
  static const mobileCallback =
      'com.riccardopinato.artdrift://login-callback/';

  static bool get configured =>
      Uri.tryParse(url)?.hasScheme == true &&
      url.startsWith('https://') &&
      publishableKey.startsWith('sb_publishable_');

  SupabaseClient? _client;
  StreamSubscription<AuthState>? _events;
  bool busy = false;
  String? lastError;

  SupabaseClient? get client => _client;
  User? get user => _client?.auth.currentUser;
  String? get userId => user?.id;
  bool get signedIn => user != null;
  String? get email => user?.email;
  String? get name =>
      user?.userMetadata?['full_name']?.toString() ??
      user?.userMetadata?['name']?.toString();
  String? get avatarUrl =>
      user?.userMetadata?['avatar_url']?.toString();

  Future<void> initialize() async {
    if (!configured || _client != null) return;
    try {
      await Supabase.initialize(url: url, publishableKey: publishableKey);
      _client = Supabase.instance.client;
      _events = _client!.auth.onAuthStateChange.listen((event) {
        lastError = null;
        notifyListeners();
      });
      notifyListeners();
    } catch (_) {
      // Fail closed: do not block guest favorites or artwork browsing.
      lastError = 'Servizio account non disponibile.';
      notifyListeners();
    }
  }

  Future<void> signIn() async {
    if (!configured || _client == null || busy) return;
    busy = true;
    lastError = null;
    notifyListeners();
    try {
      final redirect = kIsWeb
          ? Uri.base.replace(query: null, fragment: null).toString()
          : mobileCallback;
      final started = await _client!.auth.signInWithOAuth(
        OAuthProvider.google,
        redirectTo: redirect,
        scopes: 'openid email profile',
        authScreenLaunchMode:
            kIsWeb ? LaunchMode.platformDefault : LaunchMode.externalApplication,
      );
      if (!started) throw StateError('google_oauth_not_started');
      // Session is provided later by Supabase Auth callback listener.
    } catch (_) {
      lastError = 'Accesso Google non riuscito. Riprova.';
      rethrow;
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  Future<void> signOut() async {
    if (_client == null || busy) return;
    busy = true;
    notifyListeners();
    try {
      await _client!.auth.signOut();
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _events?.cancel();
    super.dispose();
  }
}
