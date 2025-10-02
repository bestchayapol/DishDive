import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class MenuCard extends StatefulWidget {
  final int dishId;
  final String imagePath;
  final String dishName;
  final String cuisine;
  final String taste;
  final int ratingPercent;
  final bool isFavorite;
  final Function(bool)? onFavoriteToggle;

  const MenuCard({
    super.key,
    required this.dishId,
    required this.imagePath,
    required this.dishName,
    required this.cuisine,
    required this.taste,
    required this.ratingPercent,
    this.isFavorite = false,
    this.onFavoriteToggle,
  });

  @override
  State<MenuCard> createState() => _MenuCardState();
}

class _MenuCardState extends State<MenuCard> {
  late bool isFavorite;

  @override
  void initState() {
    super.initState();
    isFavorite = widget.isFavorite;
  }

  @override
  void didUpdateWidget(MenuCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isFavorite != widget.isFavorite) {
      isFavorite = widget.isFavorite;
    }
  }

  @override
  Widget build(BuildContext context) {
    // Clamp rating to 0..100 and convert to widthFactor 0.0..1.0
    final double widthFactor = (widget.ratingPercent.clamp(0, 100)) / 100.0;

    return Container(
      decoration: BoxDecoration(
        color: colorUse.secondaryColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top row with title and favorite toggle (image removed)
          Padding(
            padding: const EdgeInsets.only(top: 12, left: 16, right: 12, bottom: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    widget.dishName,
                    style: const TextStyle(
                      fontFamily: 'InriaSans',
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                      color: Colors.black,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: () {
                    setState(() {
                      isFavorite = !isFavorite;
                    });
                    widget.onFavoriteToggle?.call(isFavorite);
                  },
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: const BoxDecoration(
                      color: Colors.black,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.favorite,
                      color: isFavorite ? colorUse.sentimentColor : Colors.white,
                      size: 20,
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Stretched sentiment bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Container(
              width: double.infinity,
              height: 28,
              decoration: BoxDecoration(
                // Base bar background should be dark/black
                color: Colors.black,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Stack(
                children: [
                  // Pink fill proportional to rating percent
                  FractionallySizedBox(
                    widthFactor: widthFactor,
                    alignment: Alignment.centerLeft,
                    child: Container(
                      decoration: BoxDecoration(
                        color: colorUse.sentimentColor,
                        borderRadius: BorderRadius.circular(6),
                      ),
                    ),
                  ),
                  Center(
                    child: Text(
                      "${widget.ratingPercent}%",
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              "${widget.cuisine}, ${widget.taste}",
              style: const TextStyle(fontSize: 16, color: Colors.black),
            ),
          ),
        ],
      ),
    );
  }
}
