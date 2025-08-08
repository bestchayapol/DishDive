// import 'package:dio/dio.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Components/profile_bar.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/widgets/HomepageDonate.dart';
import 'package:dishdive/widgets/HomepageReceive.dart';
import 'package:dishdive/components/integrate_model.dart' as components;
import 'package:provider/provider.dart';


class FirstHomePage extends StatefulWidget {
  const FirstHomePage({super.key});

  @override
  State<FirstHomePage> createState() => _FirstHomePageState();
}

class _FirstHomePageState extends State<FirstHomePage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String? username;
  String? email;
  String? img;
  String? firstname;
  String? lastname;
  String? fullname;
  int? userid;
  List<components.Itemlist> items = [];

  @override
  void initState() {
    super.initState();
    fetchUserData();
    // fetchItems();
    _tabController = TabController(length: 2, vsync: this);
  }

  Future<void> fetchUserData() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetProfileOfCurrentUserByUserId/$userId',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      final parsedJson = response.data; // Directly get the parsed data
      setState(() {
        // Update the username and email variables with the parsed user data
        username = parsedJson['username'];
        email = parsedJson['email'];
        img = parsedJson['user_pic'];
        firstname = parsedJson['firstname'];
        lastname = parsedJson['lastname'];
        fullname = '$firstname $lastname';
        userid = userId;
      });
    } else {
      throw Exception('Failed to load user data');
    }
  }

  //   Future<List<components.Itemlist>> fetchItems() async {
  //   final token = Provider.of<TokenProvider>(context, listen: false).token;
  //   Dio dio = Dio();
  //   final response = await dio.get(
  //     'http://10.0.2.2:5428/GetWishlistsOfCurrentUser',
  //     options: Options(
  //       headers: {
  //         'Authorization': 'Bearer $token',
  //         'Content-Type': 'application/json',
  //       },
  //     ),
  //   );

  //   if (response.statusCode == 200) {
  //     final parsedJson = response.data as List;
  //     List<components.Itemlist> items = parsedJson.map((json) => components.Itemlist.fromJson(json)).toList();
  //     return items;
  //   } else {
  //     throw Exception('Failed to load items');
  //   }
  // }


  // void refreshItems() {
  //   setState(() {
  //     fetchItems();
  //   });
  // }
// class FirstHomePage extends StatefulWidget {
//   const FirstHomePage({super.key});

//   @override
//   State<FirstHomePage> createState() => _FirstHomePageState();
// }

// class _FirstHomePageState extends State<FirstHomePage> {
  // final url = Endpoints.baseUrl;
  // List<components.Wishlist> wishlists = [];
  // String? username = 'Test User';
  // String? email = 'testuser@example.com';
  // String? img = 'https://via.placeholder.com/150'; // Example profile picture URL
  // String? firstname = 'Test';
  // String? lastname = 'User';
  // String? fullname = 'Test User';
  // int? userid = 1;
  // List<Item> items = [];
  
  
  // @override
  // void initState() {
  //   super.initState();
    // fetchWishlists();
    // fetchUserData();
  // }


  // void refreshItems() {
  //   setState(() {
  //     // Trigger rebuild by updating state
  //     fetchItems(); // Re-fetch items
  //   });
  // }
  // Future<List<components.Wishlist>> fetchItems() async {
  //   final token = Provider.of<TokenProvider>(context, listen: false).token;
  //   Dio dio = Dio();
  //   final response = await dio.get(
  //     'http://10.0.2.2:5428/GetWishlistsOfCurrentUser',
  //     options: Options(
  //       headers: {
  //         'Authorization': 'Bearer $token',
  //         'Content-Type': 'application/json',
  //       },
  //     ),
  //   );

  //   if (response.statusCode == 200) {
  //     final parsedJson = response.data as List;
  //     items = parsedJson.map((json) => Item.fromJson(json)).toList();
  //     return items;
  //   } else {
  //     throw Exception('Failed to load items');
  //   }
  // }

  // void refreshWishlists() {
  //   setState(() {
  //     // Trigger rebuild by updating state
  //     fetchWishlists(); // Re-fetch wishlists
  //   });
  // }

  // Future<void> fetchUserData() async {
  //   final token = Provider.of<TokenProvider>(context, listen: false).token;
  //   final userId = Provider.of<TokenProvider>(context, listen: false).userId;
  //   Dio dio = Dio();
  //   final response = await dio.get(
  //     'http://10.0.2.2:5428/GetProfileOfCurrentUser/$userId',
  //     options: Options(
  //       headers: {
  //         'Authorization': 'Bearer $token',
  //         'Content-Type': 'application/json', // Adjust content type as needed
  //       },
  //     ),
  //   );

  //   if (response.statusCode == 200) {
  //     final parsedJson = response.data; // Directly get the parsed data
  //     setState(() {
  //       // Update the username and email variables with the parsed user data
  //       username = parsedJson['username'];
  //       email = parsedJson['email'];
  //       img = parsedJson['user_pic'];
  //       firstname = parsedJson['firstname'];
  //       lastname = parsedJson['lastname'];
  //       fullname = '$firstname $lastname';
  //       userid = userId;
  //     });
  //   } else {
  //     throw Exception('Failed to load user data');
  //   }
  // }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize( // Use PreferredSize to customize AppBar height
        preferredSize: const Size.fromHeight(100), // Set your desired height
        child: AppBar(
          backgroundColor: colorUse.primaryColor,
          shadowColor: const Color.fromARGB(255, 171, 171, 171),
          elevation: 5,
          automaticallyImplyLeading: false,
          toolbarHeight: 40, // Height for content within AppBar
          flexibleSpace: Align(
            alignment: Alignment.bottomLeft, // Position ProfileBar at bottom-left
            child: Padding(
              padding: const EdgeInsets.only(left:5, right:5, top:30, bottom: 10),
              child: ProfileBar(
                images: img ?? '',
                name: username ?? '',
                email: email ?? '',
                fullname: fullname ?? '',
              ),
            ),
          ),
        ),
      ),
      backgroundColor: colorUse.backgroundColor,
      body: Column(
          // Main column
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Container(
            //   color: colorUse.primaryColor,
            //   height: 40.0,
            // ),
            // Profile Row
            // Container(
            //   color: colorUse.primaryColor,
            //   height: AppBar().preferredSize.height,
            //   width: 400,
            //   child: ProfileBar(
            //     images: img ?? '',
            //     name: username ?? '',
            //     email: email ?? '',
            //     fullname: fullname ?? '',
            //   ),
            // ),
            

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
          const SizedBox(height: 12.0), // Spacing between profile and card
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: const [
                HomePageReceive(),
                HomePageDonate(),
              ],
            ),
          ),],
        ),
      );
  }
}
