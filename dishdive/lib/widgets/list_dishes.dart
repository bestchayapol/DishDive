import 'package:flutter/material.dart';
import 'package:dishdive/Components/Cards/card_menu.dart';
import 'package:dishdive/Pages/Restaurant/DishPage.dart';

class ListDishesGrid extends StatelessWidget {
  const ListDishesGrid({super.key});

  @override
  Widget build(BuildContext context) {
    // Example data for demonstration
    final dishes = [
      {
        "imagePath": "assets/Logo.png",
        "dishName": "Fried rice",
        "cuisine": "Thai",
        "taste": "Salty",
        "ratingPercent": 92,
      },
      {
        "imagePath": "assets/Logo.png",
        "dishName": "Beef stew",
        "cuisine": "French",
        "taste": "Salty",
        "ratingPercent": 85,
      },
      {
        "imagePath": "assets/Logo.png",
        "dishName": "Thai sweet pork",
        "cuisine": "Thai",
        "taste": "Sweet",
        "ratingPercent": 80,
      },
      {
        "imagePath": "assets/Logo.png",
        "dishName": "Spicy beef salad",
        "cuisine": "Thai",
        "taste": "Spicy",
        "ratingPercent": 90,
      },
    ];

    return GridView.builder(
      itemCount: dishes.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 18,
        crossAxisSpacing: 12,
        childAspectRatio: 0.8,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemBuilder: (context, index) => GestureDetector(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const DishPage()),
          );
        },
        child: MenuCard(
          imagePath: dishes[index]["imagePath"] as String,
          dishName: dishes[index]["dishName"] as String,
          cuisine: dishes[index]["cuisine"] as String,
          taste: dishes[index]["taste"] as String,
          ratingPercent: dishes[index]["ratingPercent"] as int,
        ),
      ),
    );
  }
}
