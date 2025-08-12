import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/widgets/list_favorites.dart';

class FavoritesPage extends StatelessWidget {
  const FavoritesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      body: Column(
        children: [
          // Top black section with profile icon and title
          Container(
            color: colorUse.appBarColor,
            padding: const EdgeInsets.only(
              top: 40,
              left: 16,
              right: 16,
              bottom: 18,
            ),
            child: Stack(
              children: [
                // Centered title
                const Align(
                  alignment: Alignment.center,
                  child: Text(
                    "Favorite\nDishes",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontFamily: 'InriaSans',
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
                // Profile icon on the right
                Align(
                  alignment: Alignment.centerRight,
                  child: Container(
                    width: 48,
                    height: 48,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.grey, // Placeholder for profile image
                    ),
                    // Uncomment below to use actual profile image:
                    // child: img != null
                    //     ? ClipOval(
                    //         child: Image.network(
                    //           img!,
                    //           width: 48,
                    //           height: 48,
                    //           fit: BoxFit.cover,
                    //         ),
                    //       )
                    //     : null,
                  ),
                ),
              ],
            ),
          ),
          // Favorite cards (grey rectangles as placeholders)
          Expanded(child: ListFavoritesWidget()),
        ],
      ),
    );
  }
}
