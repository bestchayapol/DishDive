import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Restaurant/RestaurantPage.dart';
import 'package:dishdive/Components/Cards/card_home.dart';

class ListViewWidget extends StatelessWidget {
  const ListViewWidget({super.key});

  @override
  Widget build(BuildContext context) {
    final restaurants = [
      {
        "name": "Alfredo's Seafood",
        "cuisine": "French",
        "distance": "1.1 km away",
        "imageUrl": "",
      },
      {
        "name": "Nayeon BBQ",
        "cuisine": "Korean",
        "distance": "1.2 km away",
        "imageUrl": "",
      },
      {
        "name": "Heng Heng Noodles",
        "cuisine": "Chinese",
        "distance": "1.5 km away",
        "imageUrl": "",
      },
      {
        "name": "Jake & Jaew Kitchen",
        "cuisine": "Mixed",
        "distance": "1.8 km away",
        "imageUrl": "",
      },
    ];

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
