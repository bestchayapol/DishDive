import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/components/integrate_model.dart' as components;
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/widgets/card_widget.dart';
import 'package:provider/provider.dart';

class HomePageDonate extends StatefulWidget {
  const HomePageDonate({super.key});

  @override
  State<HomePageDonate> createState() => _HomePageDonateState();
}

class _HomePageDonateState extends State<HomePageDonate> {
  // late FollowerService _followerService;
  // late Future<List<Follower>> _followersFuture;
  List<components.Itemlist> items = [];

  @override
  void initState() {
    super.initState();
    fetchItemsDonate();
  }

  // Future<List<Follower>> _fetchFollowers() async {
  //   final token = Provider.of<TokenProvider>(context, listen: false).token;
  //   final userId = Provider.of<TokenProvider>(context, listen: false).userId;
  //   final followers =
  //       await _followerService.fetchFollowersOfCurrentUser(token!, userId!);
  //   return followers;
  // }

  Future<List<components.Itemlist>> fetchItemsDonate() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetDonateItemsOfCurrentUser',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      final parsedJson = response.data as List;
      List<components.Itemlist> items = parsedJson.map((json) => components.Itemlist.fromJson(json)).toList();
      return items;
    } else {
      throw Exception('Failed to load items');
    }
  }

  void refreshItemLists() {
    setState(() {
      // Trigger rebuild by updating state
      fetchItemsDonate(); // Re-fetch wishlists
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(8),
      child: FutureBuilder<List<components.Itemlist>>(
                future: fetchItemsDonate(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator());
                  } else if (snapshot.hasError) {
                    return Center(child: Text('Error: ${snapshot.error}'));
                  } else {
                    items = snapshot.data!;
                    if (items.isEmpty) {
                      return const Center(
                          child: Text(
                        'You don\'t have a wish yet.',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 16),
                      ));
                    } else {
                      return ListView.builder(
                        itemCount: items.length,
                        itemBuilder: (context, index) {
                          final itemlist = items[index];
                          if(itemlist.askedByUserId != null && itemlist.alreadyGave == true){
                            return SizedBox.shrink();
                          }
                          else{
                            return CardWidget(
                              product: itemlist.itemname,
                              askBy: itemlist.usernameAskedByUserId,
                              askedByUserId: itemlist.askedByUserId,
                              itemlistId: itemlist.itemlistId,
                              username:itemlist.username, // Access from the surrounding scope
                              userid: itemlist.userId, // Access from the surrounding scope
                              alreadyGave: itemlist.alreadyGave,
                              onUpdate: refreshItemLists,
                              description: itemlist.description,
                            );
                          }
                        },
                      );
                    }
                  }
                },
              ),
    );
  }
}
