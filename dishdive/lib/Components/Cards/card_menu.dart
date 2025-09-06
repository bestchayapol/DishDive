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
          // Image/Grey square inside card with padding
          Padding(
            padding: const EdgeInsets.only(top: 12, left: 12, right: 12),
            child: Stack(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    height: 110,
                    width: double.infinity,
                    color: Colors.grey[400],
                    child: widget.imagePath.startsWith('http')
                        ? Image.network(
                            widget.imagePath,
                            height: 100,
                            width: double.infinity,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) {
                              return Container(
                                height: 100,
                                width: double.infinity,
                                color: Colors.grey[400],
                                child: Icon(
                                  Icons.restaurant,
                                  color: Colors.grey[600],
                                  size: 40,
                                ),
                              );
                            },
                            loadingBuilder: (context, child, loadingProgress) {
                              if (loadingProgress == null) return child;
                              return Container(
                                height: 100,
                                width: double.infinity,
                                color: Colors.grey[400],
                                child: Center(
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(
                                      Colors.grey[600]!,
                                    ),
                                  ),
                                ),
                              );
                            },
                          )
                        : widget.imagePath.isNotEmpty
                        ? Image.asset(
                            widget.imagePath,
                            height: 100,
                            width: double.infinity,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) {
                              return Container(
                                height: 100,
                                width: double.infinity,
                                color: Colors.grey[400],
                                child: Icon(
                                  Icons.restaurant,
                                  color: Colors.grey[600],
                                  size: 40,
                                ),
                              );
                            },
                          )
                        : Icon(
                            Icons.restaurant,
                            color: Colors.grey[600],
                            size: 40,
                          ),
                  ),
                ),
                Positioned(
                  top: 8,
                  right: 8,
                  child: GestureDetector(
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
                        color: isFavorite
                            ? colorUse.sentimentColor
                            : Colors.white,
                        size: 20,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: SizedBox(
              height: 50, // Fixed height to accommodate up to 2 lines
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
          ),
          // Stretched sentiment bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Container(
              width: double.infinity,
              height: 28,
              decoration: BoxDecoration(
                color: colorUse.sentimentColor,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Stack(
                children: [
                  FractionallySizedBox(
                    widthFactor: widget.ratingPercent / 100,
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
                  Positioned(
                    right: 0,
                    top: 0,
                    bottom: 0,
                    child: Container(
                      width: 32,
                      decoration: BoxDecoration(
                        color: Colors.black,
                        borderRadius: const BorderRadius.only(
                          topRight: Radius.circular(6),
                          bottomRight: Radius.circular(6),
                        ),
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
