import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Home/FirstHomePage.dart';
import 'package:dishdive/Pages/Favorites/FavoritesPage.dart';
import 'package:dishdive/Utils/color_use.dart';

// CHANGES:
// - Simplified to only two tabs: Home and Marketplace
// - Removed floating and TabController logic for clarity
// - Uses BottomNavigationBar for standard navigation
// - Keeps icons and color scheme matching your design

class BottomBar extends StatefulWidget {
  final int currentIndex;
  const BottomBar({super.key, this.currentIndex = 0});

  @override
  State<BottomBar> createState() => _BottomBarState();
}

class _BottomBarState extends State<BottomBar> {
  late int _selectedIndex;

  final List<Widget> _pages = [FirstHomePage(), FavoritesPage()];

  @override
  void initState() {
    super.initState();
    _selectedIndex = widget.currentIndex;
  }

  void _onItemTapped(int index) {
    if (_selectedIndex == index) return;
    setState(() {
      _selectedIndex = index;
    });
    // Optionally, you can use Navigator if you want to push pages instead of swapping in place
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: colorUse.appBarColor,
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        selectedItemColor: colorUse.activeButton,
        unselectedItemColor: Colors.white,
        showSelectedLabels: false,
        showUnselectedLabels: false,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home, size: 32),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.bookmark, size: 32),
            label: 'Favorites',
          ),
        ],
      ),
    );
  }
}
