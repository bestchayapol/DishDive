import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Restaurant/RestaurantPage.dart';
import 'package:dishdive/Components/Cards/card_home.dart';

class ListViewWidget extends StatelessWidget {
  final List<Map<String, dynamic>> restaurants;
  final bool isLoading;

  const ListViewWidget({
    super.key,
    required this.restaurants,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (restaurants.isEmpty) {
      return const Center(
        child: Text(
          'No restaurants found',
          style: TextStyle(
            fontSize: 18,
            color: Colors.white,
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: restaurants.length,
      itemBuilder: (context, index) {
        final r = restaurants[index];
        return RestaurantCard(
          name: r["name"]!,
          cuisine: r["cuisine"]!,
          distance: r["distance"]!,
          imageUrl: r["imageUrl"]!,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const RestaurantPage()),
            );
          },
        );
      },
    );
  }
}
