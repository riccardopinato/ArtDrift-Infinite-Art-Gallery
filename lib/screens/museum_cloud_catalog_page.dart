import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/museum_cloud_catalog.dart';
import '../ui/localization.dart';

/// Optional D1 museum search. Metadata-only entries never become canvas tiles.
class MuseumCloudCatalogPageScreen extends StatefulWidget {
  const MuseumCloudCatalogPageScreen({
    super.key,required this.initialQuery,this.initialScope='all',
  });
  final String initialQuery,initialScope;
  @override State<MuseumCloudCatalogPageScreen> createState()=>_MuseumCloudCatalogPageScreenState();
}

class _MuseumCloudCatalogPageScreenState extends State<MuseumCloudCatalogPageScreen>{
  late final TextEditingController _input;
  final MuseumCloudCatalog _catalog=MuseumCloudCatalog();
  final List<MuseumCloudWork> _works=[];
  String? _cursor,_error;
  String _activeQuery='';
  bool _busy=false,_attempted=false;
  int _generation=0;
  static String t(String key)=>ArtDriftLocale.text(key);

  @override void initState(){
    super.initState();
    _input=TextEditingController(text:widget.initialQuery);
    if(widget.initialQuery.trim().length>=2){
      WidgetsBinding.instance.addPostFrameCallback((_) => _search());
    }
  }

  @override void dispose(){
    _generation++;
    _catalog.close();
    _input.dispose();
    super.dispose();
  }

  Future<void> _search({bool more=false}) async {
    if(_busy)return;
    final query=_input.text.trim();
    if(query.length<2)return;
    final generation=++_generation;
    setState((){
      _busy=true;_error=null;_attempted=true;
      if(!more){
        _works.clear();_cursor=null;_activeQuery=query;
      }
    });
    try{
      final page=await _catalog.search(
        more?_activeQuery:query,
        scope:widget.initialScope,cursor:more?_cursor:null);
      if(!mounted || generation!=_generation)return;
      setState((){
        _works.addAll(page.works);
        _cursor=page.nextCursor;
        _busy=false;
      });
    }catch(error){
      if(!mounted || generation!=_generation)return;
      setState((){
        _busy=false;_error=error.toString();
      });
    }
  }

  Future<void> _open(MuseumCloudWork work) async {
    final uri=Uri.tryParse(work.sourceUrl ?? '');
    if(uri==null || uri.scheme!='https' || uri.userInfo.isNotEmpty)return;
    final ok=await launchUrl(uri,mode:LaunchMode.externalApplication);
    if(!ok && mounted){
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content:Text(t('cloudMuseumOpenFailed'))));
    }
  }

  @override Widget build(BuildContext context){
    return Scaffold(
      appBar:AppBar(title:Text(t('cloudMuseumArchive'))),
      body:SafeArea(child:Column(children:[
        Padding(padding:const EdgeInsets.fromLTRB(16,12,16,7),
          child:Row(children:[
            Expanded(child:TextField(
              controller:_input,
              maxLength:90,
              textInputAction:TextInputAction.search,
              onSubmitted:(_)=>_search(),
              decoration:InputDecoration(
                labelText:t('searchHint'),counterText:'',
                prefixIcon:const Icon(Icons.search),
                border:const OutlineInputBorder(),
              ))),
            const SizedBox(width:8),
            IconButton.filled(
              onPressed:_busy?null:()=>_search(),
              tooltip:t('search'),icon:const Icon(Icons.search),
            ),
          ])),
        Padding(padding:const EdgeInsets.symmetric(horizontal:16),
          child:Text(t('cloudMuseumNotice'),
            style:const TextStyle(fontSize:11,color:Colors.white60))),
        if(_busy)const LinearProgressIndicator(minHeight:2),
        if(_error!=null)Padding(
          padding:const EdgeInsets.all(12),
          child:Text(t('cloudMuseumUnavailable')+': '+_error!,
            style:const TextStyle(color:Colors.orangeAccent,fontSize:12))),
        Expanded(child: !_attempted
          ?Center(child:Text(t('emptyQuery')))
          :_works.isEmpty && !_busy
            ?Center(child:Text(t('cloudMuseumNoResults')))
            :ListView.builder(
                itemCount:_works.length+(_cursor!=null?1:0),
                itemBuilder:(context,index){
                  if(index==_works.length){
                    return Center(child:Padding(
                      padding:const EdgeInsets.all(12),
                      child:OutlinedButton.icon(
                        onPressed:_busy?null:()=>_search(more:true),
                        icon:const Icon(Icons.expand_more),
                        label:Text(t('cloudMuseumMore')))));
                  }
                  final work=_works[index];
                  return ListTile(
                    leading:SizedBox(width:55,height:66,
                      child:work.imageUrl==null
                        ?const Icon(Icons.museum_outlined,
                          size:34,color:Colors.white38)
                        :Image.network(work.imageUrl!,
                          width:55,height:66,fit:BoxFit.contain,
                          cacheWidth:165,
                          errorBuilder:(_,__,___)=>
                            const Icon(Icons.museum_outlined,
                              color:Colors.white38))),
                    title:Text(work.title,maxLines:2,
                      overflow:TextOverflow.ellipsis),
                    subtitle:Text([
                      if(work.artist.isNotEmpty)work.artist,
                      if(work.date.isNotEmpty)work.date,
                      if(work.museum.isNotEmpty)work.museum,
                      if(work.medium.isNotEmpty)work.medium,
                      work.license,
                    ].join(' · '),maxLines:2,
                      overflow:TextOverflow.ellipsis),
                    trailing:work.sourceUrl==null
                      ? const Icon(Icons.info_outline,size:18)
                      : const Icon(Icons.open_in_new,size:18),
                    onTap:work.sourceUrl==null?null:()=>_open(work),
                  );
                })),
      ])),
    );
  }
}
