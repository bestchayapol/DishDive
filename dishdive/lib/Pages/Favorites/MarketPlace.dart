import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/widgets/MarketPlaceDonate.dart';
import 'package:dishdive/widgets/MarketPlaceReceive.dart';

class MarketPlacePage extends StatefulWidget {
  const MarketPlacePage({super.key});

  @override
  _FriendpageState createState() => _FriendpageState();
}

class _FriendpageState extends State<MarketPlacePage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      appBar: AppBar(
        title: const Text(
          "MarketPlace",
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Color.fromARGB(240, 255, 255, 255),
          ),
        ),
        backgroundColor: const Color(0xFF1B4D3F),
        elevation: 5,
        shadowColor: const Color.fromARGB(255, 98, 98, 98),
        centerTitle: true,
        automaticallyImplyLeading: false,
      ),
      body: Column(
        children: [
          Container(
            color: const Color(0xFF4CB391),
            child: TabBar(
              controller: _tabController,
              tabs: const [
                Tab(text: 'Receive'),
                Tab(text: 'Donate'),
              ],
              labelStyle: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
              indicator: BoxDecoration(
                color: const Color.fromARGB(97, 27, 77, 63),
                borderRadius: BorderRadius.circular(4),
              ),
              indicatorSize: TabBarIndicatorSize.tab,
              indicatorWeight: 3,
              indicatorPadding: EdgeInsets.zero,
              indicatorColor: Colors.transparent,
              labelColor: Colors.white,
              unselectedLabelColor: const Color.fromARGB(169, 255, 255, 255),
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: const [
                MarketPlaceReceive(),
                MarketPlaceDonate(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
