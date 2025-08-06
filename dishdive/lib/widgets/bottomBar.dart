import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_floating_bottom_bar/flutter_floating_bottom_bar.dart';
import 'package:dishdive/Pages/Preferences/ChatLog.dart';
import 'package:dishdive/Pages/Home/FirstHomePage.dart';
import 'package:dishdive/Pages/Restaurant/NewItemAdd.dart';
import 'package:dishdive/Pages/Favorites/MarketPlace.dart';
import 'package:dishdive/Utils/color_use.dart';


class bottomBar extends StatefulWidget {
  const bottomBar({super.key});
  @override
  State<bottomBar> createState() => _bottomBar();
}

class _bottomBar extends State<bottomBar> with SingleTickerProviderStateMixin {
  late TabController tabController;
  int currentPage = 0;
  List<IconData> icons = [
    Icons.home,
    Icons.explore,
    Icons.add,
    Icons.people,
  ];

  @override
  void initState() {
    super.initState();
    tabController = TabController(vsync: this, length: icons.length);
    tabController.addListener(() {
      setState(() {
        currentPage = tabController.index;
      });
    });
  }

  @override
  void dispose() {
    tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BottomBar(
        fit: StackFit.expand,
        borderRadius: BorderRadius.circular(500),
        duration: const Duration(seconds: 1),
        curve: Curves.decelerate,
        showIcon: true,
        width: MediaQuery.of(context).size.width * 0.8,
        barColor: Colors.white,
        start: 2,
        end: 0,
        offset: 10,
        barAlignment: Alignment.bottomCenter,
        iconHeight: 35,
        iconWidth: 35,
        reverse: false,
        hideOnScroll: true,
        scrollOpposite: false,
        onBottomBarHidden: () {},
        onBottomBarShown: () {},
        body: (context, controller) => TabBarView(
          controller: tabController,
          dragStartBehavior: DragStartBehavior.down,
          physics: const NeverScrollableScrollPhysics(),
          children: const [
            FirstHomePage(),
            MarketPlacePage(),
            NewItemAdd(),
            ChatLog(),
          ],
        ),
        child: TabBar(
          controller: tabController,
          tabs: List.generate(
            icons.length,
            (index) => Tab(
              icon: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color:
                      currentPage == index ? colorUse.activeButton : null,
                  shape: BoxShape.circle,
                ),
                child: Icon(icons[index],
                    color: currentPage == index
                        ? colorUse.activeButton
                        : colorUse.textColorWhite),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
