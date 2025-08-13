import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Components/Cards/card_favorites.dart';

class ListFavoritesWidget extends StatefulWidget {
  const ListFavoritesWidget({super.key});

  @override
  State<ListFavoritesWidget> createState() => _ListFavoritesWidgetState();
}

class _ListFavoritesWidgetState extends State<ListFavoritesWidget> {
  // Example data
  final List<Map<String, dynamic>> favorites = [
    {"name": "Grilled fish set", "percent": 83, "tags": "Japanese, Salty"},
    {"name": "Beef stew", "percent": 75, "tags": "French, Salty"},
    {"name": "Grilled squid", "percent": 90, "tags": "Thai, Salty"},
    {"name": "Thai sweet pork", "percent": 80, "tags": "Thai, Sweet"},
  ];

  int? pendingDeleteIndex;

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
                    fontSize: 36,
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
                          onPressed: () {
                            setState(() {
                              favorites.removeAt(index);
                              pendingDeleteIndex = null;
                            });
                            Navigator.of(context).pop();
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
                            style: TextStyle(fontSize: 26, color: Colors.white),
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
                              fontSize: 26,
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
    return ListView.builder(
      padding: const EdgeInsets.all(10),
      itemCount: favorites.length,
      itemBuilder: (context, index) {
        final fav = favorites[index];
        return FavoriteCard(
          name: fav["name"],
          percent: fav["percent"],
          tags: fav["tags"],
          onDelete: () => _showDeleteDialog(index),
        );
      },
    );
  }
}
