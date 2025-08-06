import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Item/Item_details.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/components/integrate_model.dart' as components;
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class MarketPlaceDonate extends StatefulWidget {
  const MarketPlaceDonate({super.key});

  @override
  State<MarketPlaceDonate> createState() => _MarketPlaceDonateState();
}

class _MarketPlaceDonateState extends State<MarketPlaceDonate> {
  // late FollowerService _followerService;
  // late Future<List<Follower>> _followersFuture;
  List<components.Itemlist> items = [];

  @override
  void initState() {
    super.initState();
    // _followerService = FollowerService(Dio());
    // _followersFuture = _fetchFollowers();
  }

  // Future<List<Follower>> _fetchFollowers() async {
  //   final token = Provider.of<TokenProvider>(context, listen: false).token;
  //   final userId = Provider.of<TokenProvider>(context, listen: false).userId;
  //   final followers =
  //       await _followerService.fetchFollowersOfCurrentUser(token!, userId!);
  //   return followers;
  // }

  Future<List<components.Itemlist>> fetchMarketDonate() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetDonateMarketPlace',
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

  void refreshMarketItemLists() {
    setState(() {
      // Trigger rebuild by updating state
      fetchMarketDonate(); // Re-fetch wishlists
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 25),
      child: FutureBuilder<List<components.Itemlist>>(
        future: fetchMarketDonate(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.all(8.0),
              childAspectRatio: 0.7,
              children: snapshot.data!.map((item) {
                return Center(
                  child: InkWell(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => ItemDetails(
                            itemid: item.itemlistId,
                            username: item.username!,
                            onUpdateBuy: fetchMarketDonate,
                          ),
                        ),
                      );
                    },
                    child: Container(
                      width: 200,
                      height: 400,
                      padding: const EdgeInsets.all(8.0), // Add padding here
                      child: Stack(
                        children: [
                          // Outline for border ja
                                                    Positioned.fill( 
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(22.5), 
                              child: Container(
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                    colors: [
                                      colorUse.activeIconCircle,
                                      colorUse.activeIconCircle.withOpacity(0.7),
                                      colorUse.activeButton.withOpacity(0.9),
                                    ],
                                    stops: const [0.0, 0.5, 1.0],
                                  ),
                                ),
                              ),
                            ),
                          ),
                          // Image layer
                          Padding(
                            padding: const EdgeInsets.all(8.0),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(15.0),
                              child: Image.network(
                                item.itemPic,
                                width: 200,
                                height: 400,
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                          // Text layer
                          SizedBox(
                            width: 200,
                            height: 400,
                            child: Padding(
                              padding: const EdgeInsets.all(8.0),
                              child: Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.end,
                                  children: [
                                    Text(
                                      item.itemname,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 20,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }).toList(),
            );
          } else if (snapshot.hasError) {
            return Text('Error: ${snapshot.error}');
          } else {
            return const Center(child: CircularProgressIndicator());
          }
        },
      ),
    );
  }
}
