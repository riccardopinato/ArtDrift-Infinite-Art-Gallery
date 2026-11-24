import 'package:flutter/material.dart';

import '../services/artdrift_account.dart';
import '../services/favorite_cloud_sync.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

/// Intentionally a section of the existing curator settings, not a new
/// navigation tab or compulsory onboarding flow.
class ArtDriftAccountCard extends StatefulWidget {
  const ArtDriftAccountCard({super.key, required this.sync});
  final FavoriteSyncController? sync;

  @override
  State<ArtDriftAccountCard> createState() => _ArtDriftAccountCardState();
}

class _ArtDriftAccountCardState extends State<ArtDriftAccountCard> {
  bool busy = false;

  static const _labels = <String, List<String>>{
    'it': [
      'Account Google', 'Continua con Google',
      'Collega Google per ritrovare i preferiti su Web e Android.',
      'Account non ancora configurato',
      'Sincronizza ora', 'Esci',
      'Importa preferiti locali', 'Collezione sincronizzata',
      'Preferiti solo su questo dispositivo',
      'Modifiche in attesa', 'Importare i preferiti locali?',
      'Le opere già presenti nell’account saranno conservate.',
      'Importa', 'Annulla', 'Preferiti importati',
      'Non è stato possibile completare l’operazione.',
    ],
    'en': [
      'Google account', 'Continue with Google',
      'Link Google to recover favorites on Web and Android.',
      'Account not configured yet',
      'Sync now', 'Sign out',
      'Import device favorites', 'Collection synced',
      'Favorites saved on this device',
      'Pending changes', 'Import device favorites?',
      'Existing account favorites will be preserved.',
      'Import', 'Cancel', 'Favorites imported',
      'Could not complete this action.',
    ],
    'fr': [
      'Compte Google', 'Continuer avec Google',
      'Associez Google pour retrouver vos favoris sur Web et Android.',
      'Compte non configuré', 'Synchroniser', 'Déconnexion',
      'Importer les favoris locaux', 'Collection synchronisée',
      'Favoris stockés sur cet appareil', 'Modifications en attente',
      'Importer les favoris locaux ?', 'Les favoris existants seront conservés.',
      'Importer', 'Annuler', 'Favoris importés', 'Opération impossible.',
    ],
    'es': [
      'Cuenta de Google', 'Continuar con Google',
      'Vincula Google para recuperar favoritos en Web y Android.',
      'Cuenta aún sin configurar', 'Sincronizar', 'Cerrar sesión',
      'Importar favoritos locales', 'Colección sincronizada',
      'Favoritos guardados en este dispositivo', 'Cambios pendientes',
      '¿Importar favoritos locales?', 'Se conservarán los favoritos actuales.',
      'Importar', 'Cancelar', 'Favoritos importados',
      'No se pudo completar la operación.',
    ],
    'de': [
      'Google-Konto', 'Mit Google fortfahren',
      'Mit Google Favoriten auf Web und Android wiederherstellen.',
      'Konto noch nicht eingerichtet', 'Jetzt synchronisieren', 'Abmelden',
      'Lokale Favoriten importieren', 'Sammlung synchronisiert',
      'Favoriten nur auf diesem Gerät', 'Ausstehende Änderungen',
      'Lokale Favoriten importieren?', 'Vorhandene Favoriten bleiben erhalten.',
      'Importieren', 'Abbrechen', 'Favoriten importiert',
      'Vorgang konnte nicht abgeschlossen werden.',
    ],
    'pt': [
      'Conta Google', 'Continuar com Google',
      'Liga o Google para recuperar favoritos na Web e no Android.',
      'Conta ainda não configurada', 'Sincronizar agora', 'Sair',
      'Importar favoritos locais', 'Coleção sincronizada',
      'Favoritos guardados neste dispositivo', 'Alterações pendentes',
      'Importar favoritos locais?', 'Os favoritos existentes serão mantidos.',
      'Importar', 'Cancelar', 'Favoritos importados',
      'Não foi possível concluir.',
    ],
  };

  String t(int i) => (_labels[ArtDriftLocale.current.value]
      ?? _labels['en']!)[i];

  Future<void> perform(Future<void> Function() work) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      await work();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.maybeOf(context)?.showSnackBar(
        SnackBar(content: Text(t(15))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> importGuest() async {
    final sync = widget.sync;
    if (sync == null) return;
    final allowed = await showDialog<bool>(context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: ArtPaper.ivory,
        title: Text(t(10), style: const TextStyle(color: ArtPaper.ink)),
        content: Text(t(11), style: const TextStyle(color: ArtPaper.ink)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false),
            child: Text(t(13))),
          TextButton(onPressed: () => Navigator.pop(ctx, true),
            child: Text(t(12))),
        ]));
    if (!mounted || allowed != true) return;
    await perform(() async {
      final count = await sync.importGuestFavorites();
      if (!mounted) return;
      ScaffoldMessenger.maybeOf(context)?.showSnackBar(
        SnackBar(content: Text('${t(14)}: $count')));
    });
  }

  @override
  Widget build(BuildContext context) {
    final account = ArtDriftAccount.instance;
    final sync = widget.sync;
    return AnimatedBuilder(
      animation: Listenable.merge([account, if (sync != null) sync]),
      builder: (context, _) {
        final loggedIn = account.signedIn;
        final status = !ArtDriftAccount.configured
            ? t(3)
            : !loggedIn
                ? t(2)
                : (sync?.pendingCount ?? 0) > 0
                    ? '${t(9)}: ${sync!.pendingCount}'
                    : (sync?.hasSynced ?? false)
                        ? t(7) : t(8);
        return Container(
          key: const Key('artdrift-google-account-section'),
          decoration: BoxDecoration(
            color: const Color(0xFFF5EAD7),
            border: Border.all(color: const Color(0xFFBBA27E)),
            borderRadius: BorderRadius.circular(5)),
          padding: const EdgeInsets.all(12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                const Icon(Icons.account_circle_outlined,
                  color: Color(0xFF92704A), size: 28),
                const SizedBox(width: 10),
                Expanded(child: Text(loggedIn
                    ? (account.name?.trim().isNotEmpty == true
                        ? account.name! : (account.email ?? t(0)))
                    : t(0), maxLines: 2,
                  style: const TextStyle(color: ArtPaper.ink,
                    fontFamily: 'serif', fontSize: 17))),
              ]),
              const SizedBox(height: 8),
              if (loggedIn && account.email != null) Text(account.email!,
                style: const TextStyle(color: Color(0xFF72583B),
                  fontSize: 11)),
              Text(status,
                key: const Key('artdrift-account-sync-status'),
                style: const TextStyle(color: Color(0xFF745B3D),
                  fontSize: 12, height: 1.5)),
              if (sync?.lastError != null) Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(sync!.lastError!,
                  style: const TextStyle(color: Color(0xFF9A4D3D),
                    fontSize: 11))),
              if (account.lastError != null) Text(account.lastError!,
                style: const TextStyle(color: Color(0xFF9A4D3D),
                  fontSize: 11)),
              const SizedBox(height: 10),
              if (ArtDriftAccount.configured && !loggedIn)
                OutlinedButton.icon(
                  key: const Key('artdrift-google-signin'),
                  onPressed: busy || account.busy
                      ? null : () => perform(account.signIn),
                  icon: const Icon(Icons.login_rounded, size: 17),
                  label: Text(t(1))),
              if (loggedIn) ...[
                Wrap(spacing: 8, runSpacing: 6, children: [
                  OutlinedButton.icon(
                    key: const Key('artdrift-cloud-sync-now'),
                    onPressed: busy || sync == null || sync.switching ||
                        sync.syncing ? null : () => perform(sync.synchronize),
                    icon: const Icon(Icons.sync_rounded, size: 17),
                    label: Text(t(4))),
                  OutlinedButton(
                    key: const Key('artdrift-google-signout'),
                    onPressed: busy ? null : () => perform(account.signOut),
                    child: Text(t(5))),
                ]),
                if (sync?.guestImportAvailable ?? false)
                  TextButton.icon(
                    key: const Key('artdrift-import-guest-favorites'),
                    onPressed: busy || sync!.switching
                        ? null : importGuest,
                    icon: const Icon(Icons.library_add_outlined),
                    label: Text(t(6))),
              ],
            ],
          ),
        );
      },
    );
  }
}
