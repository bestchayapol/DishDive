import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/Components/Cards/card_favorites.dart';
import 'package:dishdive/Pages/Restaurant/DishPage.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class ListFavoritesWidget extends StatefulWidget {
  const ListFavoritesWidget({super.key});

  @override
  State<ListFavoritesWidget> createState() => _ListFavoritesWidgetState();
}

class _ListFavoritesWidgetState extends State<ListFavoritesWidget> {
  List<Map<String, dynamic>> favorites = [];
  bool isLoading = true;
  int? pendingDeleteIndex;

  int _toPercentFromParts({num? positive, num? total, num? score}) {
    if (positive != null && total != null && total > 0) {
      return ((positive / total) * 100).round().clamp(0, 100);
    }
    return 0; // Default to 0 if no valid data
  }

  @override
  void initState() {
    super.initState();
    fetchFavorites();
  }

  // Public method to refresh favorites
  void refreshFavorites() {
    fetchFavorites();
  }

  Future<void> fetchFavorites() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;

    if (token == null || userId == null) {
      setState(() {
        isLoading = false;
      });
      return;
    }

    try {
      Dio dio = Dio();
      final response = await dio.get(
        ApiConfig.getFavoriteDishesEndpoint(userId),
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final List<dynamic> favoritesData = response.data;
        setState(() {
          favorites = favoritesData
              .map(
                (dish) => {
                  'dish_id': dish['dish_id'],
                  'res_id': dish['res_id'] ?? dish['restaurant_id'] ?? 0,
                  'name': dish['dish_name'] ?? 'Unknown Dish',
                  'percent': _toPercentFromParts(
                    positive: dish['positive_reviews'],
                    total: dish['total_reviews'],
                    score: dish['sentiment_score'],
                  ),
                  'tags': dish['cuisine'] ?? 'Unknown',
                  'imageUrl': dish['image_link'] ?? '',
                  'prominentFlavor': dish['prominent_flavor'],
                },
              )
              .toList();
          isLoading = false;
        });
      }
    } catch (e) {
      print('Error fetching favorites: $e');
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> removeFavorite(int dishId) async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;

    if (token == null || userId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Authentication error. Please login again.'),
        ),
      );
      return;
    }

    try {
      Dio dio = Dio();
      final response = await dio.delete(
        ApiConfig.removeFavoriteEndpoint,
        data: {'user_id': userId, 'dish_id': dishId},
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Removed from favorites')));
        fetchFavorites(); // Refresh the list
      }
    } catch (e) {
      print('Error removing favorite: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to remove from favorites')),
      );
    }
  }

  void _showDeleteDialog(int index) {
    setState(() {
      pendingDeleteIndex = index;
    });
    showDialog(
      context: context,
      builder: (context) => Center(
        child: Material(
          color: Colors.transparent,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 320,
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: colorUse.accent,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(10),
                    topRight: Radius.circular(10),
                  ),
                ),
                child: const Text(
                  "Are you sure?",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'InriaSans',
                    fontWeight: FontWeight.bold,
                    fontSize: 32,
                    color: Colors.black,
                  ),
                ),
              ),
              Container(
                width: 320,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: colorUse.secondaryColor,
                  borderRadius: BorderRadius.only(
                    bottomLeft: Radius.circular(10),
                    bottomRight: Radius.circular(10),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.12),
                      blurRadius: 8,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        ElevatedButton(
                          onPressed: () async {
                            Navigator.of(context).pop();
                            final dishId = favorites[index]['dish_id'];
                            await removeFavorite(dishId);
                            setState(() {
                              pendingDeleteIndex = null;
                            });
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: colorUse.activeButton,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            minimumSize: const Size(90, 44),
                            elevation: 0,
                          ),
                          child: const Text(
                            "Yes",
                            style: TextStyle(fontSize: 22, color: Colors.white),
                          ),
                        ),
                        OutlinedButton(
                          onPressed: () {
                            setState(() {
                              pendingDeleteIndex = null;
                            });
                            Navigator.of(context).pop();
                          },
                          style: OutlinedButton.styleFrom(
                            side: const BorderSide(
                              color: colorUse.activeButton,
                              width: 2,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            minimumSize: const Size(90, 44),
                          ),
                          child: const Text(
                            "No",
                            style: TextStyle(
                              fontSize: 22,
                              color: colorUse.activeButton,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (favorites.isEmpty) {
      return const Center(
        child: Text(
          'No favorite dishes yet',
          style: TextStyle(
            fontSize: 16,
            color: Colors.white,
            fontFamily: 'InriaSans',
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(10),
      itemCount: favorites.length,
      itemBuilder: (context, index) {
        final fav = favorites[index];
        return GestureDetector(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => DishPage(
                  dishId: fav['dish_id'] as int,
                  dishName: fav['name'] as String,
                  restaurantId: (fav['res_id'] as int?) ?? 0,
                ),
              ),
            );
          },
          child: FavoriteCard(
            name: fav["name"],
            percent: fav["percent"],
            tags: fav["tags"],
            imageUrl: fav["imageUrl"],
            onDelete: () => _showDeleteDialog(index),
          ),
        );
      },
    );
  }
}
